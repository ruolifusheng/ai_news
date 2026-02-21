---
layout: default
title: Recommendation System
---

# Recommendation System

After scoring, Horizon analyzes high-quality items to recommend new sources worth following. Recommendations are appended to the daily summary.

## How It Works

1. **Filter high-quality items** — Only items with `ai_score >= 8.0` are considered.
2. **Minimum threshold** — At least 3 high-quality items are required; otherwise no recommendations are generated.
3. **Frequency analysis** — Counts authors and source types using frequency counters. Produces top 10 authors and source distribution stats.
4. **AI recommendation** — The top 20 high-quality items (with title, score, source type, author, URL, tags) are sent to the AI model (temperature 0.4) along with the frequency analysis.
5. **Confidence filtering** — Only recommendations with `confidence >= 0.6` are kept.

## Output Format

Each recommendation contains:

| Field | Description |
|-------|-------------|
| `source_type` | One of: `github`, `hackernews`, `rss`, `twitter`, `reddit` |
| `identifier` | Username, repository, feed URL, or subreddit name |
| `reason` | Why this source is recommended |
| `confidence` | Float 0–1, must be >= 0.6 to be included |
| `sample_content` | List of example titles from this source |

## AI Criteria

The AI recommends sources based on:

- Consistent high-quality output across multiple items
- Original insights and analysis (not just aggregation)
- Active publishing cadence
- Relevance to software engineering, systems research, and AI/ML

It suggests GitHub users/repos, blogs/RSS feeds, Twitter accounts, and Reddit subreddits — only where multiple high-quality samples exist in the current batch.

## Summary Formatting

Recommendations appear as a `## Recommended Sources` section at the end of the daily summary. Each recommendation shows:

- Source type and identifier as a heading
- Reason text
- Confidence as a percentage
- Up to 3 sample content titles as bullet points
