# Codex Fantasy Blogger

This project automates a multi-agent workflow that produces a fantasy football FAAB acquisitions blog post and publishes it to a lightweight static blog.

## Overview

The pipeline consists of four agents:

1. **Top Adds Agent** – Pulls the latest waiver-wire trend data from the Sleeper public API and chooses the top `N` adds (defaults to 10).
2. **Player Research Agent** – Gathers recent news and contextual data for each player using ESPN (where available) and Google News RSS as a fallback.
3. **Transaction Expert Agent** – Synthesizes the research and issues a buy/pass recommendation with confidence and rationale (LLM-powered when `OPENAI_API_KEY` is present, otherwise heuristic).
4. **Writer Agent** – Assembles the full blog narrative and hands it to the publisher, which renders Markdown and updates a static HTML index.

Running the CLI outputs a Markdown post under `content/posts/` and keeps `content/index.html` in sync.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional: set an OpenAI API key to enable LLM-enhanced summaries and prose.

```bash
export OPENAI_API_KEY="sk-..."
# Optional tuning knobs
export FAAB_BLOGGER_MODEL="gpt-4o-mini"
export FAAB_BLOGGER_TEMPERATURE="0.4"
```

## Usage

```bash
faab-blogger --top-n 10
```

After a successful run you will find:

- `content/posts/faab-top-adds-YYYY-MM-DD.md` – Markdown blog post with front matter.
- `content/posts/_posts.json` – Metadata used to maintain the blog index.
- `content/index.html` – Landing page linking to every generated post.

## Notes

- The workflow relies on publicly available APIs (Sleeper, ESPN, Google News). Network access is required when the agents run.
- If no LLM is configured, the system still produces reasoned output via deterministic heuristics.
- Templates for the blog are located in `src/codex_fantasy_blogger/blog/templates/` and can be customized.
