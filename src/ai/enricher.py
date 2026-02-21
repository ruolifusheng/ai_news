"""Content enrichment using AI (second-pass analysis).

For items that pass the score threshold, this module generates:
- Background knowledge to help readers understand the news
- Synthesized context from related stories found via search
"""

import json
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, MofNCompleteColumn

from .client import AIClient
from .prompts import CONTENT_ENRICHMENT_SYSTEM, CONTENT_ENRICHMENT_USER
from ..models import ContentItem


class ContentEnricher:
    """Enriches high-scoring content items with background knowledge and related context."""

    def __init__(self, ai_client: AIClient):
        self.client = ai_client

    async def enrich_batch(
        self,
        items: List[ContentItem],
        related_map: Dict[str, List[dict]],
    ) -> None:
        """Enrich items in-place with background knowledge and related context.

        Args:
            items: Content items to enrich (modified in-place)
            related_map: Mapping of item IDs to related stories from search
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Enriching", total=len(items))

            for item in items:
                related = related_map.get(item.id, [])
                try:
                    await self._enrich_item(item, related)
                except Exception as e:
                    print(f"Error enriching item {item.id}: {e}")
                progress.advance(task)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=10)
    )
    async def _enrich_item(
        self, item: ContentItem, related_stories: List[dict]
    ) -> None:
        """Enrich a single item with background and related context.

        Args:
            item: Content item to enrich (modified in-place via metadata)
            related_stories: Related stories from search
        """
        # Build related stories text
        related_text = ""
        if related_stories:
            lines = []
            for r in related_stories[:6]:
                source = r.get("source", "unknown")
                score = r.get("score", 0)
                lines.append(f"- [{r['title']}]({r['url']}) (source: {source}, score: {score})")
            related_text = "\n".join(lines)

        user_prompt = CONTENT_ENRICHMENT_USER.format(
            title=item.title,
            url=str(item.url),
            summary=item.ai_summary or item.title,
            score=item.ai_score or 0,
            reason=item.ai_reason or "",
            tags=", ".join(item.ai_tags) if item.ai_tags else "",
            related_stories=related_text or "No related stories found.",
        )

        response = await self.client.complete(
            system=CONTENT_ENRICHMENT_SYSTEM,
            user=user_prompt,
            temperature=0.4,
        )

        # Parse JSON response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                raise ValueError(f"Invalid JSON response: {response}")

        # Store enrichment results in metadata
        if result.get("background"):
            item.metadata["background"] = result["background"]
        if result.get("related_context"):
            item.metadata["related_context"] = result["related_context"]
        if related_stories:
            item.metadata["related_stories"] = [
                {"title": r["title"], "url": r["url"], "source": r.get("source", "")}
                for r in related_stories[:5]
            ]
