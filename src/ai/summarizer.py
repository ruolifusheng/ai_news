"""Daily summary generation using AI."""

import json
from typing import List
from datetime import datetime

from .client import AIClient
from .prompts import DAILY_SUMMARY_SYSTEM, DAILY_SUMMARY_USER
from ..models import ContentItem


class DailySummarizer:
    """Generates daily Markdown summaries of important content."""

    def __init__(self, ai_client: AIClient):
        """Initialize daily summarizer.

        Args:
            ai_client: AI client for making completions
        """
        self.client = ai_client

    async def generate_summary(
        self,
        items: List[ContentItem],
        date: str,
        total_fetched: int
    ) -> str:
        """Generate daily summary in Markdown format.

        Args:
            items: High-scoring content items to include
            date: Date string (YYYY-MM-DD)
            total_fetched: Total number of items fetched before filtering

        Returns:
            str: Markdown formatted summary
        """
        if not items:
            return self._generate_empty_summary(date, total_fetched)

        # Prepare items as JSON for the AI, including discussion data
        items_data = []
        for item in items:
            entry = {
                "title": item.title,
                "url": str(item.url),
                "score": item.ai_score,
                "summary": item.ai_summary,
                "source": f"{item.source_type.value}/{item.author or 'unknown'}",
                "tags": item.ai_tags,
                "reason": item.ai_reason,
            }

            # Include discussion/engagement metadata for richer summaries
            meta = item.metadata
            if meta.get("score") or meta.get("descendants"):
                entry["hn_score"] = meta.get("score")
                entry["hn_comments"] = meta.get("descendants")
            if meta.get("discussion_url"):
                entry["discussion_url"] = meta["discussion_url"]
            if meta.get("favorite_count"):
                entry["twitter_likes"] = meta["favorite_count"]
                entry["twitter_retweets"] = meta.get("retweet_count", 0)
            if meta.get("reply_count"):
                entry["twitter_replies"] = meta["reply_count"]
            if meta.get("views"):
                entry["twitter_views"] = meta["views"]
            if meta.get("bookmarks"):
                entry["twitter_bookmarks"] = meta["bookmarks"]

            # Include top comments excerpt for AI to synthesize
            if item.content and "--- Top Comments ---" in item.content:
                comments_part = item.content.split("--- Top Comments ---", 1)[1]
                entry["top_comments"] = comments_part[:1200]

            items_data.append(entry)

        items_json = json.dumps(items_data, indent=2)

        # Generate summary using AI
        user_prompt = DAILY_SUMMARY_USER.format(
            date=date,
            count=len(items),
            items_json=items_json
        )

        # Use client's max_tokens if available, otherwise default to a safe value
        max_tokens = getattr(self.client, "max_tokens", 4096)

        raw_response = await self.client.complete(
            system=DAILY_SUMMARY_SYSTEM,
            user=user_prompt,
            temperature=0.5,
            max_tokens=max_tokens
        )

        # Add header with metadata
        header = f"""# Horizon Daily - {date}

> From {total_fetched} items, {len(items)} important content pieces were selected

---

"""
        try:
            # Clean response if it contains markdown code blocks
            text = raw_response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].strip()

            data = json.loads(text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response as fallback
            return header + raw_response.strip()

        # Build markdown programmatically
        sections = []

        # Highlights section
        if data.get("highlights"):
            sections.append("## Today's Highlights ⭐️\n")
            for item in data["highlights"]:
                sections.append(self._format_item(item))

        # Other sections
        for section in data.get("sections", []):
            title = section.get("title", "Other Updates")
            sections.append(f"## {title}\n")
            for item in section.get("items", []):
                sections.append(self._format_item(item))

        return header + "\n".join(sections)

    def _format_item(self, item: dict) -> str:
        """Format a single item into Markdown with explicit spacing."""
        title = item.get("title", "Untitled").replace("[", "(").replace("]", ")")
        url = item.get("url", "#")
        score = item.get("score", "?")
        summary = item.get("summary", "")

        # Format sources
        sources = item.get("sources", [])
        if isinstance(sources, list):
            sources_str = ", ".join(sources)
        else:
            sources_str = str(sources)

        # Format tags
        tags = item.get("tags", [])
        if isinstance(tags, list):
            tags_str = ", ".join([f"`#{t}`" for t in tags])
        else:
            tags_str = ""

        # Build item markdown block - using headlines and explicit spacing
        lines = [
            f"### [{title}]({url}) ⭐️ {score}/10",
            "",
            f"{summary}",
            "",
            f"*Sources: {sources_str}*"
        ]

        if item.get("community_perspective"):
            lines.append("")
            lines.append(f"**Community**: {item['community_perspective']}")

        if tags_str:
            lines.append("")
            lines.append(f"**Tags**: {tags_str}")

        # separator for clarity
        return "\n".join(lines) + "\n\n---\n\n"

    def _generate_empty_summary(self, date: str, total_fetched: int) -> str:
        """Generate summary when no high-scoring items were found.

        Args:
            date: Date string
            total_fetched: Total items fetched

        Returns:
            str: Empty summary message
        """
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
