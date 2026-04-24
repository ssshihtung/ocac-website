#!/usr/bin/env python3
"""Collapse multi-line strings inside generated frontmatter.

Some Phase 3 stubs have title values spanning multiple lines because the
title detector accepted blocks with embedded line breaks. That breaks YAML.
This script parses the frontmatter, collapses whitespace inside each single-line
double-quoted value, and rewrites.
"""
from pathlib import Path
import re

ZH = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo/content/zh/archive")
EN = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo/content/en/archive")

PATTERNS = ["report-*.md", "project-*.md", "2020-*.md", "2021-*.md", "2022-*.md", "2023-*.md", "2024-*.md", "2025-*.md"]

def fix_file(path: Path):
    t = path.read_text()
    if not t.startswith("---\n"):
        return False
    # Locate closing fence: first "---\n" after offset 4
    m = re.search(r"\n---\n", t[4:])
    if not m:
        return False
    fm_end = 4 + m.start() + 1
    fm = t[4:fm_end]
    rest = t[fm_end + 4:]  # after "\n---\n"

    # Re-parse frontmatter into (key, value) lines. Collapse multi-line quoted values.
    # Simple approach: walk lines; if a line opens a quoted value without closing it, consume subsequent lines until the quote closes.
    out_lines = []
    lines = fm.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # Count unescaped double quotes
        unesc = len(re.findall(r'(?<!\\)"', line))
        if unesc == 1:
            # Unclosed quoted value — keep appending until we see a closing quote
            buf = [line]
            i += 1
            while i < len(lines):
                buf.append(lines[i])
                if len(re.findall(r'(?<!\\)"', lines[i])) >= 1:
                    i += 1
                    break
                i += 1
            combined = " ".join(b.strip() for b in buf)
            combined = re.sub(r"\s+", " ", combined)
            out_lines.append(combined)
        else:
            out_lines.append(line)
            i += 1

    new_fm = "\n".join(out_lines)
    new_text = "---\n" + new_fm + "\n---\n" + rest
    if new_text != t:
        path.write_text(new_text)
        return True
    return False

count = 0
for base in (ZH, EN):
    for pat in PATTERNS:
        for f in base.glob(pat):
            if fix_file(f):
                count += 1
print(f"Fixed {count} files with multi-line frontmatter values")
