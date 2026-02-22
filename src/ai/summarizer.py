"""Daily summary generation — pure programmatic rendering."""

from typing import List, Dict
from collections import defaultdict

from ..models import ContentItem


class DailySummarizer:
    """Generates daily Markdown summaries from pre-analyzed content items.

    No AI call needed — all data (score, summary, background, tags)
    is already produced by the analyzer and enricher stages.
    """

    def __init__(self):
        """Initialize daily summarizer."""
        pass

    async def generate_summary(
        self,
        items: List[ContentItem],
        date: str,
        total_fetched: int,
    ) -> str:
        """Generate daily summary in Markdown format.

        Items are split into highlights (score >= 9) and sections grouped by tag.

        Args:
            items: High-scoring content items (already enriched)
            date: Date string (YYYY-MM-DD)
            total_fetched: Total number of items fetched before filtering

        Returns:
            str: Markdown formatted summary
        """
        if not items:
            return self._generate_empty_summary(date, total_fetched)

        header = f"""# Horizon Daily - {date}

> From {total_fetched} items, {len(items)} important content pieces were selected

---

"""
        sections = []

        # Split into highlights and regular
        highlights = [i for i in items if (i.ai_score or 0) >= 9.0]
        regular = [i for i in items if (i.ai_score or 0) < 9.0]

        if highlights:
            sections.append("## Today's Highlights\n")
            for item in highlights:
                sections.append(self._format_item(item))

        # Group regular items by primary tag
        grouped = self._group_by_tag(regular)
        for section_title, group_items in grouped.items():
            sections.append(f"## {section_title}\n")
            for item in group_items:
                sections.append(self._format_item(item))

        return header + "\n".join(sections)

    def _format_item(self, item: ContentItem) -> str:
        """Format a single ContentItem into Markdown."""
        title = item.title.replace("[", "(").replace("]", ")")
        url = str(item.url)
        score = item.ai_score or "?"
        meta = item.metadata

        summary = meta.get("detailed_summary") or item.ai_summary or ""
        source = item.source_type.value
        if meta.get("subreddit"):
            source += f"/r/{meta['subreddit']}"
        source += f"/{item.author or 'unknown'}"

        # Build item block
        lines = [
            f"### [{title}]({url}) ⭐️ {score}/10",
            "",
            summary,
            "",
            f"*Source: {source}*",
        ]

        if meta.get("background"):
            lines.append("")
            lines.append(f"**Background**: {meta['background']}")

        if meta.get("community_discussion"):
            lines.append("")
            lines.append(f"**Discussion**: {meta['community_discussion']}")

        # Tags
        if item.ai_tags:
            tags_str = ", ".join([f"`#{t}`" for t in item.ai_tags])
            lines.append("")
            lines.append(f"**Tags**: {tags_str}")

        return "\n".join(lines) + "\n\n---\n\n"

    def _group_by_tag(self, items: List[ContentItem]) -> Dict[str, List[ContentItem]]:
        """Group items by their primary tag into named sections."""
        TAG_SECTIONS = {
            "ai": "AI / Machine Learning",
            "ml": "AI / Machine Learning",
            "machine-learning": "AI / Machine Learning",
            "deep-learning": "AI / Machine Learning",
            "llm": "AI / Machine Learning",
            "nlp": "AI / Machine Learning",
            "systems": "Systems & Infrastructure",
            "infrastructure": "Systems & Infrastructure",
            "performance": "Systems & Infrastructure",
            "linux": "Systems & Infrastructure",
            "kernel": "Systems & Infrastructure",
            "security": "Security",
            "programming": "Programming & Tools",
            "rust": "Programming & Tools",
            "python": "Programming & Tools",
            "golang": "Programming & Tools",
            "tools": "Programming & Tools",
            "open-source": "Open Source",
        }

        grouped: Dict[str, List[ContentItem]] = defaultdict(list)
        for item in items:
            section = "Other Updates"
            for tag in (item.ai_tags or []):
                tag_lower = tag.lower()
                if tag_lower in TAG_SECTIONS:
                    section = TAG_SECTIONS[tag_lower]
                    break
            grouped[section].append(item)

        return dict(grouped)

    def _generate_empty_summary(self, date: str, total_fetched: int) -> str:
        """Generate summary when no high-scoring items were found."""
        return f"""# Horizon Daily - {date}

> Analyzed {total_fetched} items, but none met the importance threshold.

No significant developments today. This might indicate:
- A quiet day in your tracked sources
- The AI score threshold is too high
- Your information sources need expansion

Consider:
1. Lowering the `ai_score_threshold` in config.json
2. Adding more diverse information sources
3. Checking if the AI model is working correctly
"""
