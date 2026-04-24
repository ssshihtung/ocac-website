#!/usr/bin/env python3
"""Post-process already-generated archive markdown: NFKC normalize + dedup adjacent CJK chars.

Fixes PDF-font artefacts like ⾺馬, 蘭蘭, ⼩小, ⽯石 → 馬, 蘭, 小, 石.
Only touches files matching patterns we generated (report-*, project-*, YYYY-*).
"""
import re, unicodedata
from pathlib import Path

ZH = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo/content/zh/archive")
EN = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo/content/en/archive")

PATTERNS = ["report-20*.md", "project-*.md", "2020-*.md", "2021-*.md", "2022-*.md", "2023-*.md", "2024-*.md", "2025-*.md"]

def dedup_cjk(text):
    out = []
    prev = ""
    for ch in text:
        if re.match(r"[\u4e00-\u9fff]", ch) and ch == prev:
            continue
        out.append(ch)
        prev = ch
    return "".join(out)

def strip_radical_artefacts(text):
    """Drop CJK-Radical block chars (U+2E80..U+2FDF) when adjacent to a regular CJK char.

    PDFs using certain CJK fonts encode a glyph as "radical + base char" — we want just the base.
    """
    out = []
    for i, ch in enumerate(text):
        if "\u2e80" <= ch <= "\u2fdf":
            # Look at next char; if CJK ideograph, drop this radical
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if "\u4e00" <= nxt <= "\u9fff":
                continue
        out.append(ch)
    return "".join(out)

def fix(text):
    text = unicodedata.normalize("NFKC", text)
    text = strip_radical_artefacts(text)
    text = dedup_cjk(text)
    # Also common Taiwan punctuation artefacts
    text = text.replace("⻄", "西").replace("⺠", "民").replace("⻛", "風")
    text = text.replace("⻢", "馬").replace("⻓", "長").replace("⻔", "門")
    return text

count = 0
for base in (ZH, EN):
    for pat in PATTERNS:
        for f in base.glob(pat):
            orig = f.read_text()
            fixed = fix(orig)
            if fixed != orig:
                f.write_text(fixed)
                count += 1

print(f"Normalised {count} files")
