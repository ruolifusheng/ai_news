<div align="center">

# 🌅 Horizon

**AI-Driven Information Aggregation System**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square)](https://github.com/astral-sh/uv)
[![Daily Summary](https://github.com/Thysrael/Horizon/actions/workflows/deploy-docs.yml/badge.svg?style=flat-square)](https://thysrael.github.io/Horizon/)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Thysrael/Horizon?style=flat-square)](https://github.com/Thysrael/Horizon/commits/main)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

<p align="center">
  <img src="docs/assets/horizon-header.svg" alt="Horizon Header" />
</p>

*Horizon monitors academic peers and social trends across multiple platforms, using AI to filter effectively important content.*

</div>

## Features

- **Multi-Source Aggregation**: Monitors GitHub (releases, user events), Hacker News, RSS feeds, and Reddit
- **AI-Powered Filtering**: Supports Anthropic (Claude), OpenAI (GPT-4), Google (Gemini), and OpenAI-compatible APIs (DeepSeek, Groq) to score content importance
- **Daily Summaries**: Automatically generates comprehensive Markdown reports with key developments
- **Deduplication**: Merges cross-source duplicates to keep summaries concise
- **Content Enrichment**: Automatically searches the web for background context on high-scoring items
- **Simple & Configurable**: File-based config, CLI tool, easy to schedule with cron/launchd

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

Create `data/config.json` to configure sources and AI. Start from the example:

```bash
cp data/config.example.json data/config.json
# Edit data/config.json to customize your sources
```

See [`data/config.example.json`](data/config.example.json) for a complete example covering all source types and environment variable substitution.

For the full configuration reference, see the [Configuration Guide](docs/configuration.md).

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
2. Use AI to analyze and score new content
3. Generate a summary markdown file in `data/summaries/` (e.g., `data/summaries/horizon-2026-02-22.md`)
