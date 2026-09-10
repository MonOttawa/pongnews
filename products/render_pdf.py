#!/usr/bin/env python3
"""Render brain-pong-protocol.md to PDF via Chromium print-to-PDF."""
import subprocess, sys, pathlib, re

SRC = pathlib.Path.home() / "Projects/pongnews/products/brain-pong-protocol.md"
OUT_HTML = SRC.with_suffix(".html")
OUT_PDF = SRC.with_suffix(".pdf")

CSS = """
@page { size: Letter; margin: 22mm 18mm; }
* { box-sizing: border-box; }
body { font-family: 'DejaVu Sans', 'Noto Sans', sans-serif; color: #1a1a1a;
       font-size: 11pt; line-height: 1.55; }
h1 { font-size: 20pt; margin: 0 0 4pt; line-height: 1.2; }
h1 + p { font-size: 13pt; color: #444; margin-top: 0; }
h2 { font-size: 14pt; margin-top: 18pt; border-bottom: 1.5pt solid #1a1a1a; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin-top: 12pt; }
blockquote { margin: 10pt 0; padding: 8pt 12pt; background: #f4f2ee;
             border-left: 3pt solid #8a8a8a; font-size: 10pt; }
table { border-collapse: collapse; width: 100%; font-size: 10pt; margin: 8pt 0; }
th, td { border: 0.75pt solid #999; padding: 4pt 6pt; text-align: left; }
th { background: #f4f2ee; }
hr { border: none; border-top: 0.75pt solid #bbb; margin: 14pt 0; }
li { margin: 3pt 0; }
"""

def md_to_html(text: str) -> str:
    import markdown
    return markdown.markdown(text, extensions=["tables", "sane_lists"])

html = f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>\n" + md_to_html(SRC.read_text())
OUT_HTML.write_text(html)

subprocess.run(
    ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
     f"--print-to-pdf={OUT_PDF}", OUT_HTML.as_uri()],
    check=True, capture_output=True, timeout=120,
)
print("PDF:", OUT_PDF, OUT_PDF.stat().st_size, "bytes")
