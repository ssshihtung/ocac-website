#!/usr/bin/env python3
"""Regenerate 2020 annual overview with timeline events parsed from slide pages.

2020 PDF is a slide deck where pages 1–2 are timeline pages with (date block, title block) pairs.
"""
import json, re
from pathlib import Path

ROOT = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo")
RAW = ROOT / "tmp/reports/raw"
ZH = ROOT / "content/zh/archive"
EN = ROOT / "content/en/archive"

DATE_LINE = re.compile(r"^\s*20\d{2}\s*\d{1,2}\s*/\s*\d{1,2}")

def load():
    return json.loads((RAW / "2020.json").read_text())

def clean(s):
    # Collapse soft linebreaks + double chars from CJK duplication artifacts in PDF extraction
    s = s.replace("\u2028", " ")
    # Many cjk chars get doubled during extraction (e.g. "蘭蘭", "個⼈人"): remove the duplicate of the pair
    # Pattern: same CJK char twice → keep one (only when forming a duplication artifact)
    # This is heuristic and may over-correct; acceptable since user said we'll fix manually
    def dedup_cjk(text):
        out = []
        prev = ""
        for ch in text:
            if re.match(r"[\u4e00-\u9fff]", ch) and ch == prev:
                continue  # drop duplicate CJK char
            out.append(ch)
            prev = ch
        return "".join(out)
    s = dedup_cjk(s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def timeline_events():
    d = load()
    pairs = []
    for pno in (1, 2):
        page = d["pages"][pno - 1]
        blocks = page["blocks"]
        # pair every (date, title) consecutive
        i = 0
        while i < len(blocks) - 1:
            b = blocks[i].strip()
            if DATE_LINE.match(b):
                date = clean(b)
                title = clean(blocks[i + 1])
                pairs.append((date, title))
                i += 2
            else:
                i += 1
    return pairs

def run():
    pairs = timeline_events()
    print(f"Found {len(pairs)} timeline events")
    for p in pairs:
        print(f"  {p[0]:20s}  {p[1]}")

    # Regenerate zh + en 2020 overview
    d = load()
    all_imgs = [img for p in d["pages"] for img in p["images"]]
    hero = all_imgs[0]["file"] if all_imgs else "/images/ui/placeholder-white.png"

    bullets_zh = "\n".join(f"- **{dt}** — {tt}" for dt, tt in pairs)

    body_zh = f"""以亞洲／東南亞為軸的跨文化合作與群島思維持續深化；《島嶼集市》、KANTA Portraits、打鐵計劃等延伸行動。

本篇為打開－當代藝術工作站 2020 年度空間營運簡報整理而成，主要收錄 2019 年度於甘州街空間執行的展演、交流、駐村、研究、討論與分享活動。

## 2019 年度活動時間軸

{bullets_zh}

## 年度計畫脈絡

- **打開－群島**：延續與《數位荒原》駐站暨群島資料庫的合作，與社群「群島」（archipiélago）達成「共享空間」默契。
- **開放的空間**：探訪作為另類資本累積可能的群聚實踐。
- **東南亞的延續旅程**：透過展演、交流、進駐的「行動」而非僅是展示。
- **延伸計畫**：KANTA Portraits 馬來西亞－台灣交流、ACELab（ACE 另類交換所）、加帝旺宜超自然聲音節、2019 KLEX 吉隆坡實驗電影／錄像／音樂節等。

## 圖像紀錄

"""
    for img in all_imgs[:12]:
        body_zh += f"![]({img['file']})\n\n"
    body_zh += "\n---\n\n*本文由 2020 年度空間營運簡報整理而成，部分中文字元因 PDF 字型關係可能需要校正；內容與圖文對應仍在持續修正中。*\n"

    fm_zh = f"""---
title: "2020 年度回顧"
date: "2020-12-31T00:00:00+08:00"
draft: false
section: "archive"
image: "{hero}"
tags: ["2020", "年度回顧"]
---
"""
    (ZH / "report-2020.md").write_text(fm_zh + body_zh)

    # EN version (basic)
    bullets_en = "\n".join(f"- **{dt}** — {tt}" for dt, tt in pairs)
    body_en = f"""OCAC’s 2020 closing deck documents the 2019 programme year at the Ganzhou Street space: exhibitions, exchanges, residencies, research, discussions and sharings.

Deepening cross-cultural collaboration across Asia / Southeast Asia under the ‘archipiélago’ frame; follow-ups including the 2019 Asian Art Biennial’s ‘Island Market’, KANTA Portraits, and the Blacksmith Plan.

## 2019 programme timeline

{bullets_en}

## Themes of the year

- **Open — archipiélago**: Continued collaboration with *No Man’s Land* and the Archipiélago Archive, co-inhabiting the Ganzhou Street space with the ‘archipiélago’ community.
- **The open space**: Exploring the convening of non-specialists as a form of alternative capital.
- **Southeast Asia – a continuing journey**: Emphasising ‘action’ (residencies, exchanges, collaborations) over mere ‘display’.
- **Extension projects**: KANTA Portraits (Malaysia–Taiwan), ACELab (Alternative Currency Exchange Laboratory), Jatiwangi Supernatural Sound Festival, KLEX Kuala Lumpur Experimental Film, Video and Music Festival 2019.

## Image record

"""
    for img in all_imgs[:12]:
        body_en += f"![]({img['file']})\n\n"
    body_en += "\n---\n\n*Compiled from the 2020 Space Operations Briefing; some Chinese characters may be affected by PDF font artefacts and are being corrected; image–event pairing is being refined.*\n"

    fm_en = f"""---
title: "2020 Year in Review"
date: "2020-12-31T00:00:00+08:00"
draft: false
section: "archive"
image: "{hero}"
tags: ["2020", "year-review"]
---
"""
    (EN / "report-2020.md").write_text(fm_en + body_en)
    print("Updated report-2020.md (zh + en)")

if __name__ == "__main__":
    run()
