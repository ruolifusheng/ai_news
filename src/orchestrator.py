"""Main orchestrator coordinating the entire workflow."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from urllib.parse import urlparse
import httpx
from rich.console import Console

from .models import Config, ContentItem
from .storage.manager import StorageManager
from .scrapers.github import GitHubScraper
from .scrapers.hackernews import HackerNewsScraper
from .scrapers.rss import RSSScraper
from .scrapers.twitter import TwitterScraper
from .scrapers.reddit import RedditScraper
from .ai.client import create_ai_client
from .ai.analyzer import ContentAnalyzer
from .ai.summarizer import DailySummarizer
from .ai.recommender import SourceRecommender


class HorizonOrchestrator:
    """Orchestrates the complete workflow for content aggregation and analysis."""

    def __init__(self, config: Config, storage: StorageManager):
        """Initialize orchestrator.

        Args:
            config: Application configuration
            storage: Storage manager
        """
        self.config = config
        self.storage = storage
        self.console = Console()

    async def run(self, force_hours: int = None) -> None:
        """Execute the complete workflow.

        Args:
            force_hours: Optional override for time window in hours
        """
        self.console.print("[bold cyan]🌅 Horizon - Starting aggregation...[/bold cyan]\n")

        try:
            # 1. Determine time window
            seen_data = self.storage.load_seen_items()
            since = self._determine_time_window(seen_data, force_hours)
            self.console.print(f"📅 Fetching content since: {since.strftime('%Y-%m-%d %H:%M:%S')}\n")

            # 2. Fetch content from all sources
            all_items = await self._fetch_all_sources(since)
            self.console.print(f"📥 Fetched {len(all_items)} items from all sources\n")

            if not all_items:
                self.console.print("[yellow]No new content found. Exiting.[/yellow]")
                return

            # 3. Filter out seen items
            new_items = self._filter_seen_items(all_items, seen_data)
            self.console.print(f"🆕 {len(new_items)} new items (filtered {len(all_items) - len(new_items)} duplicates)\n")

            if not new_items:
                self.console.print("[yellow]No new items to process. Exiting.[/yellow]")
                return

            # 3.5. Merge cross-source duplicates (same URL from different sources)
            merged_items = self._merge_cross_source_duplicates(new_items)
            if len(merged_items) < len(new_items):
                self.console.print(
                    f"🔗 Merged {len(new_items) - len(merged_items)} cross-source duplicates "
                    f"→ {len(merged_items)} unique items\n"
                )

            # 4. Analyze with AI
            analyzed_items = await self._analyze_content(merged_items)
            self.console.print(f"🤖 Analyzed {len(analyzed_items)} items with AI\n")

            # 5. Filter by score threshold
            threshold = self.config.filtering.ai_score_threshold
            important_items = [
                item for item in analyzed_items
                if item.ai_score and item.ai_score >= threshold
            ]
            important_items.sort(key=lambda x: x.ai_score or 0, reverse=True)

            self.console.print(
                f"⭐️ {len(important_items)} items scored ≥ {threshold}\n"
            )

            # 6. Generate daily summary
            today = datetime.utcnow().strftime("%Y-%m-%d")
            summary = await self._generate_summary(important_items, today, len(all_items))

            # 7. Recommend new sources
            recommendations = await self._recommend_sources(analyzed_items)

            # 8. Save summary with recommendations
            if recommendations:
                summary += self._format_recommendations(recommendations)

            summary_path = self.storage.save_daily_summary(today, summary)
            self.console.print(f"💾 Saved summary to: {summary_path}\n")

            # 8.5. Copy summary to docs/ for GitHub Pages
            try:
                import shutil
                from pathlib import Path

                # Setup Jekyll post format: YYYY-MM-DD-title.md
                post_filename = f"{today}-summary.md"
                posts_dir = Path("docs/_posts")
                posts_dir.mkdir(parents=True, exist_ok=True)

                dest_path = posts_dir / f"{today}-summary.md"

                # Add Jekyll front matter
                front_matter = (
                    "---\n"
                    "layout: default\n"
                    f"title: \"Horizon Summary: {today}\"\n"
                    f"date: {today}\n"
                    "---\n\n"
                )

                # Check if summary starts with an H1 header and strip it if it duplicates the title
                summary_content = summary
                if summary_content.strip().startswith("# Horizon Daily -"):
                    # Find the first newline and take everything after it
                    parts = summary_content.split("\n", 1)
                    if len(parts) > 1:
                        summary_content = parts[1].strip()

                with open(dest_path, "w") as f:
                    f.write(front_matter + summary_content)

                self.console.print(f"📄 Copied summary to GitHub Pages: {dest_path}\n")
            except Exception as e:
                self.console.print(f"[yellow]⚠️  Failed to copy summary to docs/: {e}[/yellow]\n")

            # 9. Update seen items
            for item in analyzed_items:
                self.storage.mark_item_seen(item, seen_data)

            seen_data.last_run = datetime.utcnow()
            self.storage.save_seen_items(seen_data)

            # 10. Cleanup old records
            removed = self.storage.cleanup_old_seen_items(seen_data, days=30)
            if removed > 0:
                self.console.print(f"🧹 Cleaned up {removed} old records\n")
                self.storage.save_seen_items(seen_data)

            self.console.print("[bold green]✅ Horizon completed successfully![/bold green]")

        except Exception as e:
            self.console.print(f"[bold red]❌ Error: {e}[/bold red]")
            raise

    def _determine_time_window(self, seen_data, force_hours: int = None) -> datetime:
        """Determine the time window for fetching content.

        Args:
            seen_data: Seen items data
            force_hours: Optional override for time window in hours

        Returns:
            datetime: Start time for fetching
        """
        if force_hours:
            since = datetime.now(timezone.utc) - timedelta(hours=force_hours)
        elif seen_data.last_run:
            since = seen_data.last_run
        else:
            # Default to configured time window
            hours = self.config.filtering.time_window_hours
            since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Ensure timezone-aware
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        return since

    async def _fetch_all_sources(self, since: datetime) -> List[ContentItem]:
        """Fetch content from all configured sources.

        Args:
            since: Fetch items published after this time

        Returns:
            List[ContentItem]: All fetched items
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []

            # GitHub sources
            if self.config.sources.github:
                github_scraper = GitHubScraper(self.config.sources.github, client)
                tasks.append(self._fetch_with_progress("GitHub", github_scraper, since))

            # Hacker News
            if self.config.sources.hackernews.enabled:
                hn_scraper = HackerNewsScraper(self.config.sources.hackernews, client)
                tasks.append(self._fetch_with_progress("Hacker News", hn_scraper, since))

            # RSS feeds
            if self.config.sources.rss:
                rss_scraper = RSSScraper(self.config.sources.rss, client)
                tasks.append(self._fetch_with_progress("RSS Feeds", rss_scraper, since))

            # Twitter (via Nitter)
            if self.config.sources.twitter:
                twitter_scraper = TwitterScraper(self.config.sources.twitter, client)
                tasks.append(self._fetch_with_progress("Twitter", twitter_scraper, since))

            # Reddit
            if self.config.sources.reddit.enabled:
                reddit_scraper = RedditScraper(self.config.sources.reddit, client)
                tasks.append(self._fetch_with_progress("Reddit", reddit_scraper, since))

            # Fetch all concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results
            all_items = []
            for result in results:
                if isinstance(result, Exception):
                    self.console.print(f"[red]Error fetching source: {result}[/red]")
                elif isinstance(result, list):
                    all_items.extend(result)

            return all_items

    async def _fetch_with_progress(self, name: str, scraper, since: datetime) -> List[ContentItem]:
        """Fetch from a scraper with progress indication.

        Args:
            name: Source name for display
            scraper: Scraper instance
            since: Fetch items after this time

        Returns:
            List[ContentItem]: Fetched items
        """
        self.console.print(f"🔍 Fetching from {name}...")
        items = await scraper.fetch(since)
        self.console.print(f"   Found {len(items)} items from {name}")
        return items

    def _filter_seen_items(self, items: List[ContentItem], seen_data) -> List[ContentItem]:
        """Filter out items that have been seen before.

        Args:
            items: All fetched items
            seen_data: Seen items data

        Returns:
            List[ContentItem]: New items only
        """
        return [
            item for item in items
            if not self.storage.is_item_seen(item.id, seen_data)
        ]

    def _merge_cross_source_duplicates(self, items: List[ContentItem]) -> List[ContentItem]:
        """Merge items that point to the same URL from different sources.

        Keeps the item with the richest content and combines metadata.

        Args:
            items: Items to deduplicate

        Returns:
            List[ContentItem]: Deduplicated items
        """
        def normalize_url(url: str) -> str:
            parsed = urlparse(str(url))
            # Strip www prefix, trailing slashes, and fragments
            host = parsed.hostname or ""
            if host.startswith("www."):
                host = host[4:]
            path = parsed.path.rstrip("/")
            return f"{host}{path}"

        # Group by normalized URL
        url_groups: Dict[str, List[ContentItem]] = {}
        for item in items:
            key = normalize_url(str(item.url))
            url_groups.setdefault(key, []).append(item)

        merged = []
        for key, group in url_groups.items():
            if len(group) == 1:
                merged.append(group[0])
                continue

            # Pick the item with the richest content as primary
            primary = max(group, key=lambda x: len(x.content or ""))

            # Merge metadata and source info from other items
            all_sources = set()
            for item in group:
                all_sources.add(item.source_type.value)
                # Merge metadata (engagement, discussion, etc.)
                for mk, mv in item.metadata.items():
                    if mk not in primary.metadata or not primary.metadata[mk]:
                        primary.metadata[mk] = mv

                # Append content (e.g., comments from another source)
                if item is not primary and item.content:
                    if primary.content and item.content not in primary.content:
                        primary.content = (primary.content or "") + f"\n\n--- From {item.source_type.value} ---\n" + item.content

            primary.metadata["merged_sources"] = list(all_sources)
            merged.append(primary)

        return merged

    async def _analyze_content(self, items: List[ContentItem]) -> List[ContentItem]:
        """Analyze content items with AI.

        Args:
            items: Items to analyze

        Returns:
            List[ContentItem]: Analyzed items
        """
        self.console.print("🤖 Analyzing content with AI...")

        ai_client = create_ai_client(self.config.ai)
        analyzer = ContentAnalyzer(ai_client)

        return await analyzer.analyze_batch(items)

    async def _generate_summary(
        self,
        items: List[ContentItem],
        date: str,
        total_fetched: int
    ) -> str:
        """Generate daily summary.

        Args:
            items: Important items to include
            date: Date string
            total_fetched: Total items fetched

        Returns:
            str: Markdown summary
        """
        self.console.print("📝 Generating daily summary...")

        ai_client = create_ai_client(self.config.ai)
        summarizer = DailySummarizer(ai_client)

        return await summarizer.generate_summary(items, date, total_fetched)

    async def _recommend_sources(self, items: List[ContentItem]) -> List:
        """Generate source recommendations.

        Args:
            items: Analyzed items

        Returns:
            List[SourceRecommendation]: Recommendations
        """
        self.console.print("💡 Generating source recommendations...")

        ai_client = create_ai_client(self.config.ai)
        recommender = SourceRecommender(ai_client)

        return await recommender.recommend_sources(items, min_score=8.0)

    def _format_recommendations(self, recommendations: List) -> str:
        """Format source recommendations as Markdown.

        Args:
            recommendations: Source recommendations

        Returns:
            str: Formatted Markdown section
        """
        if not recommendations:
            return ""

        md = "\n\n---\n\n## 💡 Recommended Sources\n\n"
        md += "Based on today's high-quality content, consider following:\n\n"

        for rec in recommendations:
            md += f"### {rec.source_type.value}: {rec.identifier}\n\n"
            md += f"{rec.reason}\n\n"
            md += f"**Confidence**: {rec.confidence:.0%}\n\n"

            if rec.sample_content:
                md += "**Sample content**:\n"
                for content in rec.sample_content[:3]:
                    md += f"- {content}\n"
                md += "\n"

        return md
