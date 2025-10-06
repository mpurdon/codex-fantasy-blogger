"""Simple static blog publisher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from codex_fantasy_blogger.config import config
from codex_fantasy_blogger.models import BlogPost
from codex_fantasy_blogger.utils.logging import get_logger


logger = get_logger("blog.publisher")


class BlogPublisher:
    def __init__(self, output_dir: str | Path | None = None) -> None:
        self.output_dir = Path(output_dir or config.writer.output_dir)
        template_dir = Path(__file__).resolve().parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=False,
            lstrip_blocks=True,
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.output_dir / "_posts.json"
        self.index_path = self.output_dir.parent / "index.html"

    def _load_metadata(self) -> List[dict]:
        if not self.metadata_path.exists():
            return []
        try:
            data = json.loads(self.metadata_path.read_text())
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            logger.warning("Failed to parse existing posts metadata; starting fresh")
        return []

    def _save_metadata(self, entries: List[dict]) -> None:
        self.metadata_path.write_text(json.dumps(entries, indent=2))

    def _render_post(self, post: BlogPost) -> str:
        template = self.env.get_template("post.md.j2")
        return template.render(post=post)

    def _render_index(self, posts_meta: List[dict]) -> str:
        template = self.env.get_template("index.html.j2")
        return template.render(
            title=config.writer.blog_title,
            posts=posts_meta,
        )

    def publish(self, post: BlogPost) -> Path:
        post_path = self.output_dir / f"{post.slug}.md"
        logger.info("Publishing blog post to %s", post_path)
        post_path.write_text(self._render_post(post))

        metadata = self._load_metadata()
        new_entry = {
            "title": post.title,
            "slug": post.slug,
            "created_at": post.created_at.isoformat(),
            "path": str(post_path.relative_to(self.output_dir.parent)),
        }
        filtered = [entry for entry in metadata if entry.get("slug") != post.slug]
        filtered.append(new_entry)
        filtered.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        self._save_metadata(filtered)

        index_html = self._render_index(filtered)
        logger.info("Updating index at %s", self.index_path)
        self.index_path.write_text(index_html)
        return post_path
