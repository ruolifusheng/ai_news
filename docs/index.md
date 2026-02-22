---
layout: default
title: Home
---

# Horizon

Welcome to [Horizon](https://github.com/thysrael/Horizon), an AI-driven information aggregation system.

## Documentation

- [Configuration Guide](configuration) — AI providers, information sources, filtering, and environment variable substitution
- [Source Scrapers](scrapers) — How Horizon collects content from GitHub, Hacker News, RSS, and Reddit
- [Scoring System](scoring) — AI-based content analysis and the 0-10 scoring scale

## Latest Summaries

<ul>
  {% for post in site.posts limit:20 %}
    <li>
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      <small style="color: #666;">- {{ post.date | date: "%Y-%m-%d" }}</small>
    </li>
  {% endfor %}
</ul>
