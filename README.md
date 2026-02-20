<div align="center">

# 🌅 Horizon

**AI-Driven Information Aggregation System**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square)](https://github.com/astral-sh/uv)
[![Daily Summary](https://github.com/thysrael/horizon/actions/workflows/daily-summary.yml/badge.svg?style=flat-square)](https://github.com/thysrael/horizon/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

<p align="center">
  <img src="docs/assets/horizon-header.svg" alt="Horizon Header" />
</p>

*Horizon monitors academic peers and social trends across multiple platforms, using AI to filter effectively important content.*

</div>

## Features

- 🔍 **Multi-Source Aggregation**: Monitors GitHub (releases, user events), Hacker News, RSS feeds, and Twitter
- 🤖 **AI-Powered Filtering**: supports Anthropic (Claude), OpenAI (GPT-4), Google (Gemini), and OpenAI-compatible APIs (DeepSeek, Groq) to score content importance
- 📊 **Daily Summaries**: Automatically generates comprehensive Markdown reports with key developments
- 💡 **Smart Recommendations**: Suggests new high-quality sources based on content analysis
- 🎯 **Deduplication**: Tracks seen content to avoid repeated processing and merges cross-source duplicates
- ⚙️ **Simple & Configurable**: File-based config, CLI tool, easy to schedule with cron/launchd

## Quick Start

### 1. Installation

```bash
# Clone or create project directory
cd horizon

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### 2. Configuration

Create `.env` file with API keys:

```bash
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-...
# GOOGLE_API_KEY=AI...
```

Create `data/config.json` to configure sources and AI. Here is a complete example:

```json
{
  "version": "1.0",
  "ai": {
    "provider": "openai",
    "model": "deepseek-reasoner",
    "base_url": "https://api.deepseek.com",
    "api_key_env": "OPENAI_API_KEY",
    "temperature": 0.3,
    "max_tokens": 16384
  },
  "sources": {
    "github": [
      {
        "type": "user_events",
        "username": "karpathy",
        "enabled": true,
        "priority": "high"
      },
      {
        "type": "repo_releases",
        "owner": "astral-sh",
        "repo": "uv",
        "enabled": true,
        "priority": "medium"
      }
    ],
    "hackernews": {
      "enabled": true,
      "fetch_top_stories": 20,
      "min_score": 100
    },
    "rss": [
      {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom/everything/",
        "enabled": true,
        "category": "ai-tools"
      }
    ],
    "twitter": [
      {
        "username": "ylecun",
        "enabled": true
      }
    ]
  },
  "filtering": {
    "ai_score_threshold": 6.0,
    "time_window_hours": 72
  }
}
```

### 3. Usage

Run the aggregator:

```bash
# Manual run via uv
uv run horizon

# Or if installed globally
horizon
```

The system will:
1. Fetch content from configured sources
2. Filter out previously seen items
3. Use AI to analyze and score new content
4. Generate a summary markdown file in `data/summaries/` (e.g., `data/summaries/horizon-2024-02-20.md`)

## Project Structure

- `src/scrapers/`: Modules for fetching data from GitHub, HN, RSS, Twitter
- `src/ai/`: AI client wrappers (OpenAI, Anthropic, Gemini) and prompt logic
- `src/storage/`: Manages tracking of seen items and saving summaries
- `data/`: Stores configuration, state (`seen.json`), and generated summaries

## Development

```bash
# Format code
uv run ruff check .
```

First run will:
1. Fetch content from configured sources
2. Analyze with AI (scores 0-10)
3. Generate `data/summaries/horizon-YYYY-MM-DD.md`
4. Save state to `data/seen.json`

## Configuration Guide

### AI Providers

**Anthropic Claude** (recommended):
```json
{
  "ai": {
    "provider": "anthropic",
    "model": "claude-sonnet-4.5-20250929",
    "api_key_env": "ANTHROPIC_API_KEY"
  }
}
```

**OpenAI**:
```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key_env": "OPENAI_API_KEY"
  }
}
```

**Custom Base URL** (for proxies):
```json
{
  "ai": {
    "provider": "anthropic",
    "base_url": "https://your-proxy.com/v1",
    ...
  }
}
```

### Information Sources

**GitHub**:
```json
{
  "sources": {
    "github": [
      {
        "type": "user_events",
        "username": "gvanrossum",
        "enabled": true
      },
      {
        "type": "repo_releases",
        "owner": "python",
        "repo": "cpython",
        "enabled": true
      }
    ]
  }
}
```

**Hacker News**:
```json
{
  "hackernews": {
    "enabled": true,
    "fetch_top_stories": 30,
    "min_score": 100
  }
}
```

**RSS Feeds**:
```json
{
  "rss": [
    {
      "name": "Blog Name",
      "url": "https://example.com/feed.xml",
      "enabled": true,
      "category": "ai-ml"
    }
  ]
}
```

### Filtering

```json
{
  "filtering": {
    "ai_score_threshold": 7.0,
    "time_window_hours": 24
  }
}
```

- `ai_score_threshold`: Only include content scoring ≥ this value
- `time_window_hours`: Fetch content from last N hours (first run only)


## Project Structure

```
horizon/
├── pyproject.toml          # Project dependencies
├── README.md               # This file
├── .env                    # API keys (create from .env.example)
├── src/
│   ├── main.py             # CLI entry point
│   ├── models.py           # Data models
│   ├── orchestrator.py     # Main workflow coordinator
│   ├── scrapers/           # Platform scrapers
│   │   ├── github.py
│   │   ├── hackernews.py
│   │   └── rss.py
│   ├── ai/                 # AI analysis modules
│   │   ├── client.py       # Multi-provider AI client
│   │   ├── analyzer.py     # Content scoring
│   │   ├── summarizer.py   # Daily summaries
│   │   └── recommender.py  # Source recommendations
│   └── storage/
│       └── manager.py      # File storage
├── data/
│   ├── config.json         # Configuration
│   ├── seen.json           # Deduplication state
│   └── summaries/          # Generated Markdown files
└── logs/                   # Application logs
```

## AI Scoring System

Content is scored 0-10:

- **9-10**: Groundbreaking - Major breakthroughs, paradigm shifts
- **7-8**: High Value - Important developments, deep technical content
- **5-6**: Interesting - Worth knowing but not urgent
- **3-4**: Low Priority - Generic or routine content
- **0-2**: Noise - Spam, off-topic, or trivial

Only content scoring ≥ `ai_score_threshold` appears in daily summaries.

## Output Format

Daily summaries are saved as `data/summaries/horizon-YYYY-MM-DD.md`:

```markdown
# Horizon Daily - 2026-02-20

> From 156 items, 18 important content pieces were selected

---

## Today's Highlights ⭐️

### [Major Linux Kernel Performance Improvement](https://github.com/...) ⭐️ 9.5/10

Significant optimization reducing context switch overhead by 40%.

- **Source**: github/torvalds
- **Why Important**: Impacts all Linux systems
- **Tags**: #kernel #performance #systems

## AI/ML

[... more categorized content ...]

---

## 💡 Recommended Sources

Consider following these based on today's high-quality content...
```

## Troubleshooting

**No high-scoring content**:
- Lower `ai_score_threshold` in config
- Add more diverse sources
- Check AI API is working

**Rate limiting errors**:
- Add `GITHUB_TOKEN` to `.env`
- Reduce `fetch_top_stories` for Hacker News
- Increase `time_window_hours` to spread requests

**Missing dependencies**:
```bash
uv sync  # Reinstall all dependencies
```



## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Roadmap

- [X] Twitter/X integration (via official API)
- [ ] More sources (Reddit, ArXiv, ...)
- [ ] Track news history/context
- [ ] Cross-source comprehensive analysis
- [ ] GitHub Actions workflow
- [ ] Complete documentation
