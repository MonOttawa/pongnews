#!/usr/bin/env python3
"""
Pong News Content Pipeline API
Adds articles, triggers rebuild, lists content.
Usage: python content-pipeline.py [command] [args]
Commands:
  add    - Add article from stdin (JSON or markdown with frontmatter)
  list   - List all articles
  rebuild- Trigger site rebuild
  stats  - Show content statistics
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(__file__).parent
CONTENT_DIR = SITE_DIR / "src" / "content" / "articles"
DIST_DIR = SITE_DIR / "dist"


def list_articles():
    articles = []
    for f in sorted(CONTENT_DIR.glob("*.md"), reverse=True):
        # Parse frontmatter
        text = f.read_text()
        fm = {}
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                for line in text[3:end].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        fm[key.strip()] = val.strip().strip('"').strip("'")
        articles.append({
            "slug": f.stem,
            "title": fm.get("title", f.stem),
            "date": fm.get("date", "unknown"),
            "category": fm.get("category", "General"),
            "summary": fm.get("summary", "")[:120],
        })
    return articles


def add_article(title, slug, date, category, tags, summary, sources, content):
    """Write a new article markdown file and trigger rebuild."""
    tags_yaml = str(tags).replace("'", '"')
    sources_yaml = "\n".join(f'  - "{s}"' for s in sources)
    
    md = f"""---
title: "{title}"
slug: "{slug}"
date: "{date}"
category: "{category}"
tags: {json.dumps(tags)}
summary: "{summary}"
sources:
{sources_yaml}
---

{content}
"""
    filepath = CONTENT_DIR / f"{slug}.md"
    filepath.write_text(md)
    return {"slug": slug, "file": str(filepath), "created": True}


def rebuild():
    """Trigger Astro static site rebuild."""
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(SITE_DIR),
        capture_output=True, text=True, timeout=120
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout[-500:] if result.stdout else "",
        "error": result.stderr[-500:] if result.stderr else "",
    }


def stats():
    articles = list_articles()
    categories = {}
    for a in articles:
        cat = a["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    total_size = sum(f.stat().st_size for f in CONTENT_DIR.glob("*.md"))
    
    return {
        "total_articles": len(articles),
        "categories": categories,
        "total_content_bytes": total_size,
        "dist_size": sum(f.stat().st_size for f in DIST_DIR.rglob("*")) if DIST_DIR.exists() else 0,
        "latest": articles[0] if articles else None,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: content-pipeline.py [list|stats|rebuild]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        print(json.dumps(list_articles(), indent=2))
    elif cmd == "stats":
        print(json.dumps(stats(), indent=2))
    elif cmd == "rebuild":
        result = rebuild()
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
