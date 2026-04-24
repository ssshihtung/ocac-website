#!/usr/bin/env python3
"""Parse extracted OCAC reports and generate Hugo articles.

Phases:
  1) Annual overview articles (6 years × 2 languages = 12 articles)
  2) Long-term project profile articles
  3) Individual event stubs from per-year timelines

Writes to:
  content/zh/archive/report-{year}.md              # Phase 1 zh
  content/en/archive/report-{year}.md              # Phase 1 en
  content/zh/archive/project-{slug}.md             # Phase 2 zh
  content/en/archive/project-{slug}.md             # Phase 2 en
  content/zh/archive/{year}-{slug}.md              # Phase 3 zh
  content/en/archive/{year}-{slug}.md              # Phase 3 en
"""
from pathlib import Path
import json, re, datetime, unicodedata

ROOT = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo")
RAW = ROOT / "tmp/reports/raw"
ZH = ROOT / "content/zh/archive"
EN = ROOT / "content/en/archive"
ZH.mkdir(parents=True, exist_ok=True)
EN.mkdir(parents=True, exist_ok=True)

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]

# --- Event detection ------------------------------------------------------

EVENT_MARKERS = ["主辦", "策劃", "時間", "地點", "時間與地點", "活動性質", "參與者", "與談", "合作夥伴", "進駐藝術家"]
DATE_RE = re.compile(r"(20\d{2})\s*[年\s/\-\.]\s*(\d{1,2})\s*[月/\-\.]?\s*(\d{0,2})")
RANGE_RE = re.compile(r"(20\d{2})[年\s/\-\.](\d{1,2})[月/\-\.]?\s*(\d{0,2})\s*[-–~～至到]\s*(?:(20\d{2})[年\s/\-\.])?(\d{1,2})[月/\-\.]?\s*(\d{0,2})")

def slugify(txt, maxlen=50):
    txt = unicodedata.normalize("NFKD", txt)
    # strip punctuation; keep ascii letters/digits; turn cjk into pinyin-less tokens via index
    out = re.sub(r"[^\w\u4e00-\u9fff]+", "-", txt, flags=re.UNICODE).strip("-").lower()
    return out[:maxlen].strip("-") or "event"

def parse_date(text):
    """Return ISO date string YYYY-MM-DD or YYYY-12-31 if only year."""
    m = RANGE_RE.search(text)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3) or "1"
    else:
        m = DATE_RE.search(text)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3) or "1"
        else:
            return None
    try:
        return f"{int(y):04d}-{int(mo):02d}-{int(d or 1):02d}"
    except ValueError:
        return None

def detect_events(pages):
    """Simple segmenter: cluster sequential pages into events.

    An event starts on a page whose first non-empty block (short, <40 chars, no 主辦) is the title,
    and the page contains at least 1 EVENT_MARKER.
    Events continue on the next page if it contains images and no new title but references the same event (inferred by lack of new 主辦).
    """
    events = []
    cur = None
    for p in pages:
        blocks = p.get("blocks") or [p["text"]]
        txt = p["text"]
        has_marker = any(mk in txt for mk in EVENT_MARKERS)
        if not blocks:
            continue
        first = blocks[0].strip()
        # Title is the first block if it's short and does not contain marker
        is_title = len(first) < 60 and not any(mk in first for mk in EVENT_MARKERS) and has_marker

        if is_title:
            if cur:
                events.append(cur)
            # pull full title: join leading short blocks until a marker appears
            title_parts = []
            body_start = 0
            for i, b in enumerate(blocks):
                if any(mk in b for mk in EVENT_MARKERS):
                    body_start = i
                    break
                if len(b) < 80:
                    title_parts.append(b.strip())
                else:
                    body_start = i
                    break
            title = " ".join(title_parts).strip() or first
            body = "\n\n".join(blocks[body_start:]).strip()
            cur = {
                "title": title,
                "body": body,
                "images": list(p["images"]),
                "first_page": p["page"],
                "last_page": p["page"],
            }
        else:
            # continuation of current event OR orphan — attach to current
            if cur is None:
                cur = {
                    "title": first[:60] if first else f"Page {p['page']}",
                    "body": txt,
                    "images": list(p["images"]),
                    "first_page": p["page"],
                    "last_page": p["page"],
                }
            else:
                cur["body"] += "\n\n" + txt
                cur["images"].extend(p["images"])
                cur["last_page"] = p["page"]
    if cur:
        events.append(cur)
    return events

# --- Title translation hints (manual; can be expanded) --------------------

ZH_EN_HINTS = {
    "執行成果": "Annual Report",
    "年度執行成果": "Annual Report",
    "空間營運簡報": "Space Operations Briefing",
    "蜿蜒集": "The Meandering Collection",
    "台越交流計畫": "Taiwan–Vietnam Exchange Project",
    "一隻蒼蠅飛入海洋無垠的吐納": "A Fly Entering the Ocean’s Boundless Breath",
    "一群老鼠闖入叢林無懼的開路": "A Pack of Mice Fearlessly Breaking Trail in the Jungle",
    "寫給未來的群島": "Letters to the Future Archipelago",
    "群島航空": "Archipiélago Airlines",
    "空間沙盒": "Space Sandbox",
    "作品展一件": "One-Work Exhibition",
    "一群人的自學": "A Group Self-Study",
    "藝策互助會": "Artist–Curator Mutual Aid Meeting",
    "發聲與未言": "Un/Uttered",
    "亞洲藝術團體對話": "Asian Art Collectives in Dialogue",
    "微型影展": "Micro Film Festival",
    "群島資料庫": "Archipiélago Archive",
    "數位荒原": "No Man’s Land",
    "打開－當代藝術工作站": "Open Contemporary Art Center",
    "打開-當代藝術工作站": "Open Contemporary Art Center",
    "打開當代藝術工作站": "Open Contemporary Art Center",
    "打開－當代": "OCAC",
    "駐地": "residency",
    "駐村": "residency",
    "個展": "Solo Exhibition",
    "個人藝術計畫": "Solo Art Project",
    "交流計畫": "Exchange Project",
    "拜訪": "Visit",
    "參訪": "Visit",
    "演出": "Performance",
    "放映": "Screening",
    "工作坊": "Workshop",
    "論壇": "Forum",
    "討論會": "Discussion",
    "讀書會": "Reading Group",
    "藝術進駐": "Art Residency",
    "戀戀檳榔": "Areca Romance",
    "ba-bau AIR": "ba-bau AIR",
    "KANTA": "KANTA",
    "Un/Uttered": "Un/Uttered",
    "PETAMU": "PETAMU",
    "ACELab": "ACELab",
    "ACE另類交換所": "ACE Alternative Currency Exchange Lab",
    "加帝旺宜": "Jatiwangi",
    "超自然聲音節": "Supernatural Sound Festival",
    "Jatiwangi Art Factory": "Jatiwangi Art Factory",
    "archipiélago": "archipiélago",
    "群島": "Archipiélago",
    "長拓": "Longtruk",
    "Longtruk": "Longtruk",
    "in the gap, in between": "in the gap, in between",
    "亞洲藝術人才交流計畫": "Asian Artists Exchange Program",
}

def translate_title(zh):
    """Rough translate title. Keeps English words. Replaces known phrases."""
    out = zh
    for k, v in sorted(ZH_EN_HINTS.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(k, v)
    # if no Chinese chars remain, done. Else prepend english gloss
    if not re.search(r"[\u4e00-\u9fff]", out):
        return out.strip()
    # Mixed — add prefix
    return f"{out.strip()}"

def pick_hero(images):
    if not images:
        return "/images/ui/placeholder-white.png"
    images = sorted(images, key=lambda i: -(i.get("w", 0)*i.get("h", 0)))
    return images[0]["file"]

def write_md(path, frontmatter, body):
    fm_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            fm_lines.append(f'{k}: [{", ".join(chr(34)+x+chr(34) for x in v)}]')
        elif isinstance(v, bool):
            fm_lines.append(f"{k}: {str(v).lower()}")
        else:
            s = str(v).replace('"', '\\"')
            fm_lines.append(f'{k}: "{s}"')
    fm_lines.append("---\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fm_lines) + body + "\n")

# --- Year theme/summary ----------------------------------------------------

YEAR_THEMES_ZH = {
    "2020": "以亞洲／東南亞為軸的跨文化合作與群島思維持續深化；《島嶼集市》、KANTA Portraits、打鐵計劃等延伸行動。",
    "2021": "面對疫情，計畫轉向線上與地分散執行。《一隻蒼蠅飛入海洋無垠的吐納》線上聲音行動、《寫給未來的群島》線上工作坊、空間實驗沙盒等。",
    "2022": "檢視機構作為「非中心化網絡」的可能；嘗試 WEB3.0、NFT、DAO 對藝術組織運作的影響；延續國際與跨域對話。",
    "2023": "《蜿蜒集－台越交流計畫：河內》、《戀戀檳榔：打開－當代藝術工作站 X ba-bau AIR》、Longtruk 專題、Jane Jin Kaisen 研究駐地、區塊鏈數位創作生態培養。",
    "2024": "台北雙年展《一隻蒼蠅飛入海洋無垠的吐納。一群老鼠闖入叢林無懼的開路》、《Un/Uttered 發聲與未言：亞洲藝術團體對話暨微型影展》於大阪；持續推進蜿蜒集。",
    "2025": "《蜿蜒集－台越交流計畫：台北》進駐、多項國際參訪與進駐；「Close to Home」台灣原住民導演作品在日惹／哥本哈根／巴黎巡映；編織實踐與群島思維再開展。",
}

YEAR_THEMES_EN = {
    "2020": "Deepening cross-cultural collaboration across Asia/Southeast Asia under the 'archipiélago' frame; follow-ups including the 2019 Asian Art Biennial’s 'Island Market', KANTA Portraits, and the Blacksmith Plan.",
    "2021": "Pandemic pivot to online and distributed programmes: 'A Fly Entering the Ocean’s Boundless Breath' online sound actions, 'Letters to the Future Archipelago' online workshop, Space Sandbox 'One-Work Exhibition', and 'A Group Self-Study' recurring gatherings.",
    "2022": "Rethinking the organisation as a decentralised network; early engagement with WEB3.0, NFT, DAO as tools for art collectives; continuing international and cross-disciplinary dialogue.",
    "2023": "The Meandering Collection – Taiwan–Vietnam Exchange (Hanoi), 'Areca Romance: OCAC × ba-bau AIR', Longtruk thematic programme, Jane Jin Kaisen research residency, and cultivation of a blockchain digital art ecology.",
    "2024": "Taipei Biennial programme 'A Fly Entering the Ocean’s Boundless Breath. A Pack of Mice Fearlessly Breaking Trail in the Jungle'; 'Un/Uttered – Asian Art Collectives in Dialogue & Micro Film Festival' in Osaka; ongoing Meandering Collection.",
    "2025": "The Meandering Collection residencies in Taipei; multiple international visits and residencies; 'Close to Home' Taiwanese indigenous directors’ touring programme to Yogyakarta, Copenhagen and Paris; continued weaving practice and archipiélago thinking.",
}

# --- Phase 1: Annual overview articles -----------------------------------

def phase1():
    generated = []
    for y in YEARS:
        raw = json.loads((RAW / f"{y}.json").read_text())
        pages = raw["pages"]
        # Gather all images for hero selection
        all_imgs = [img for p in pages for img in p["images"]]
        hero = pick_hero(all_imgs)
        # Build event bullet list from first-block titles
        events = detect_events(pages)
        # Take a shortlist of plausible event titles (dedup + filter junk)
        seen = set()
        bullets = []
        for e in events:
            t = e["title"].strip()
            if len(t) < 2 or len(t) > 80:
                continue
            # filter obvious non-titles
            if re.match(r"^\d+$", t):
                continue
            if t in seen:
                continue
            if re.match(r"^\(?[A-Z]-\d", t) or t.startswith("年度"):
                continue
            seen.add(t)
            bullets.append(t)
        bullets = bullets[:30]

        # zh article
        theme_zh = YEAR_THEMES_ZH[y]
        body_zh = f"{theme_zh}\n\n"
        if bullets:
            body_zh += "## 年度活動 / 計畫\n\n" + "\n".join(f"- {b}" for b in bullets) + "\n\n"
        body_zh += "## 圖像紀錄\n\n"
        # Insert up to 8 images inline
        for img in all_imgs[:8]:
            body_zh += f"![]({img['file']})\n\n"
        body_zh += "\n---\n\n*本文由 2020–2025 年度結案報告整理而成，內容與圖文對應仍在陸續校正中。*\n"

        fm_zh = {
            "title": f"{y} 年度回顧",
            "date": f"{y}-12-31T00:00:00+08:00",
            "draft": False,
            "section": "archive",
            "image": hero,
            "tags": [y, "年度回顧"],
        }
        zh_path = ZH / f"report-{y}.md"
        write_md(zh_path, fm_zh, body_zh)
        generated.append(str(zh_path))

        # en article
        theme_en = YEAR_THEMES_EN[y]
        body_en = f"{theme_en}\n\n"
        if bullets:
            body_en += "## Year in programmes\n\n"
            for b in bullets:
                body_en += f"- {translate_title(b)}\n"
            body_en += "\n"
        body_en += "## Image record\n\n"
        for img in all_imgs[:8]:
            body_en += f"![]({img['file']})\n\n"
        body_en += "\n---\n\n*This article is compiled from OCAC’s 2020–2025 annual closing reports; English translations and image–event pairings are being refined.*\n"

        fm_en = {
            "title": f"{y} Year in Review",
            "date": f"{y}-12-31T00:00:00+08:00",
            "draft": False,
            "section": "archive",
            "image": hero,
            "tags": [y, "year-review"],
        }
        en_path = EN / f"report-{y}.md"
        write_md(en_path, fm_en, body_en)
        generated.append(str(en_path))

    return generated

# --- Phase 2: Long-term projects -----------------------------------------

LONG_TERM_PROJECTS = [
    {
        "slug": "meandering-collection-taiwan-vietnam",
        "title_zh": "蜿蜒集 — 台越交流計畫",
        "title_en": "The Meandering Collection — Taiwan–Vietnam Exchange",
        "years": ["2023", "2024", "2025"],
        "keywords": ["蜿蜒集", "台越交流", "ba-bau AIR", "Á Space", "Nha San"],
        "summary_zh": "《蜿蜒集－台越交流計畫》為打開－當代藝術工作站自 2023 年起與越南藝術空間 Á Space、ba-bau AIR、Nha San Collective 等合作夥伴共同發起的多年度雙向交換進駐計畫。以河內、台北為節點，邀請雙邊藝術家彼此駐地、交換研究與生產創作，透過展覽、放映、田野拜訪與對談，逐步建立台越當代藝術之間更細緻、長期的網絡。",
        "summary_en": "‘The Meandering Collection — Taiwan–Vietnam Exchange’ is a multi-year bilateral residency programme that OCAC initiated in 2023 with Vietnamese partners Á Space, ba-bau AIR and Nha San Collective. Using Hanoi and Taipei as dual nodes, it invites artists from both sides to reside, research and produce with one another, weaving a more intimate long-term network between Taiwan and Vietnam through exhibitions, screenings, field visits and conversations.",
    },
    {
        "slug": "fly-ocean-breath",
        "title_zh": "一隻蒼蠅飛入海洋無垠的吐納",
        "title_en": "A Fly Entering the Ocean’s Boundless Breath",
        "years": ["2020", "2021", "2024"],
        "keywords": ["一隻蒼蠅", "聲音行動", "失聲祭"],
        "summary_zh": "《一隻蒼蠅飛入海洋無垠的吐納》是打開－當代藝術工作站自 2020 年啟動、以音樂與實驗聲音為介面的跨國交流計畫。疫情期間轉為線上與四地分別執行的方式，集結台灣、印尼、菲律賓、泰國策展人與聲音影像創作者，探討聲音是否能作為重啟身體感官的圖景。2024 年此脈絡延伸進入「台北雙年展」的程序，與失聲祭共同策劃《一隻蒼蠅飛入海洋無垠的吐納。一群老鼠闖入叢林無懼的開路》放映與演出節目。",
        "summary_en": "Launched in 2020 as a cross-border sound and experimental music programme, ‘A Fly Entering the Ocean’s Boundless Breath’ gathered curators and sound/moving-image artists from Taiwan, Indonesia, the Philippines and Thailand. The pandemic reshaped it into online and locally-distributed actions, probing whether sound can re-open bodily perception. In 2024 it extended into the Taipei Biennial as ‘A Fly Entering the Ocean’s Boundless Breath. A Pack of Mice Fearlessly Breaking Trail in the Jungle’, co-curated with Lacking Sound Festival.",
    },
    {
        "slug": "archipielago",
        "title_zh": "群島｜archipiélago",
        "title_en": "archipiélago",
        "years": ["2020", "2021", "2022", "2023"],
        "keywords": ["群島", "archipiélago", "數位荒原", "寫給未來的群島"],
        "summary_zh": "「群島」（archipiélago）是自 2018 年起在打開－當代藝術工作站不定期聚會的一個非固定成員社群，透過讀書會、主題分享、「大眾飯店」、「全錯會」等多樣形式，連結藝術與非藝術領域的廣泛群體。其與《數位荒原》及群島資料庫的合作，孕育出《寫給未來的群島》線上工作坊、《群島航空》策展等延伸計畫，持續以「島嶼之間的雙向橋樑」作為工作隱喻。",
        "summary_en": "‘archipiélago’ is a membership-fluid community that has been meeting irregularly at OCAC since 2018. Through reading groups, themed sharings, 'Grand People’s Cafeteria' and 'All-Wrong Meetings', it connects a broad public beyond the art field. Its collaboration with No Man’s Land and the Archipiélago Archive has given rise to ongoing extensions such as the 'Letters to the Future Archipelago' online workshop and the 'Archipiélago Airlines' curatorial programme, consistently using the image of 'two-way bridges between islands' as a working metaphor.",
    },
    {
        "slug": "kanta-portraits",
        "title_zh": "KANTA Portraits｜馬來西亞－台灣交流計劃",
        "title_en": "KANTA Portraits — Malaysia–Taiwan Exchange",
        "years": ["2019", "2020"],
        "keywords": ["KANTA"],
        "summary_zh": "《KANTA Portraits 馬來西亞－台灣交流計劃：跨越邊界，一段尋找自己的旅程》延伸自 2018 年《邊境旅行 PETAMU Project》計畫。藝術家林猶進（Jeffrey Lim）與馬來西亞半島原住民關懷中心（COAC）共同策劃，邀請台灣阿美族紀錄片導演 Posak Jodian 進入馬來西亞多個原住民聚落，以肖像攝影與紀錄片、聲音採集等不同媒介，訪談部落耆老與青年的口述故事、神話與歌謠，嘗試建構台馬之間原住民文化下互為主體的對話空間。",
        "summary_en": "‘KANTA Portraits — Malaysia–Taiwan Exchange: Crossing Borders, A Journey to Find the Self’ extends the 2018 ‘PETAMU Project’. Co-curated by artist Jeffrey Lim with the Center for Orang Asli Concerns (COAC), it invited Taiwanese Amis documentary director Posak Jodian into multiple indigenous villages in Peninsular Malaysia. Through portrait photography, documentary, sound collection and conversations with elders and youth, it attempted to construct a space of mutual subjectivity between Taiwanese and Malaysian indigenous cultures.",
    },
    {
        "slug": "acelab",
        "title_zh": "ACE 另類交換所 ACELab",
        "title_en": "ACELab (Alternative Currency Exchange Laboratory)",
        "years": ["2019", "2020"],
        "keywords": ["ACELab", "ACE另類交換所"],
        "summary_zh": "《ACE 另類交換所》（ACELab）為打開－當代與菲律賓獨立研究者 Marika Constantino 共同規劃的分享與研究實驗工作坊。以另類貨幣（Alternative Currency）為概念，重新思考跨文化交流、持續性計畫與集體合作行動中所產生的無形價值。邀請菲律賓藝術家 JK Anicoche、印尼行為表演者 Ferrial Affif、台灣劇場創作者林欣怡，透過研究、行動與工作坊推動一種「創意區塊鏈」，讓不同藝術世界中的個體得以被聯繫與轉譯。",
        "summary_en": "‘ACELab’ is a sharing and research laboratory co-designed by OCAC and Filipina independent researcher Marika Constantino. Centred on the concept of ‘alternative currency’, it rethinks the intangible value produced in cross-cultural exchange, long-running projects and collective action. Together with Filipino artist JK Anicoche, Indonesian performance artist Ferrial Affif and Taiwanese theatre maker Lin Hsinyi, the programme pushed a ‘creative blockchain’ that links and translates individuals across different art worlds.",
    },
    {
        "slug": "jatiwangi-art-factory",
        "title_zh": "加帝旺宜超自然聲音節｜Jatiwangi Art Factory",
        "title_en": "Jatiwangi Supernatural Sound Festival",
        "years": ["2019", "2020"],
        "keywords": ["加帝旺宜", "Jatiwangi"],
        "summary_zh": "加帝旺宜藝術工廠（Jatiwangi Art Factory）位於印尼西爪哇，致力於以藝文活動在地深根並與社區合作，發起三年一次的「陶瓷音樂節」、「村落錄像節」以及「雙年藝術進駐節」。打開－當代的合作以 2019 年度送一至兩組台灣聲音創作者前往當地進駐，並與曾在打開－當代進駐的 Ismal Muntaha 討論未來台灣實驗聲音藝術家與加帝旺宜藝術工廠的長期合作。",
        "summary_en": "Jatiwangi Art Factory, located in West Java, Indonesia, has long rooted its practice in community life, initiating the triennial ‘Ceramic Music Festival’, ‘Village Video Festival’ and the biennial ‘Jatiwangi Residency Festival’. OCAC’s collaboration began with dispatching one or two Taiwanese sound artists to the site in 2019 and working with former OCAC resident Ismal Muntaha to plan longer-term cooperation between Taiwanese experimental sound artists and Jatiwangi Art Factory.",
    },
    {
        "slug": "un-uttered",
        "title_zh": "Un/Uttered 發聲與未言：亞洲藝術團體對話暨微型影展",
        "title_en": "Un/Uttered — Asian Art Collectives in Dialogue & Micro Film Festival",
        "years": ["2024"],
        "keywords": ["Un/Uttered", "發聲與未言"],
        "summary_zh": "《Un/Uttered 發聲與未言：亞洲藝術團體對話暨微型影展》由打開－當代藝術工作站與日本 Tra-Travel、大阪 Osaka Art Hub 共同主辦，2024 年 2 月於日本大阪 FIGYA 舉行。影展策劃由 P.M.S. 負責，邀請 Kawah Umei 連晨軿、Rngrang Hungul 余欣蘭、Posak Jodian 曾于軒等參與，放映包含《我在林森北路的那段日子》、《我是女人，我是獵人》、《母語》、《Ugaljai 蛾》、《Misafafahiyan 蛻變》等台灣原住民族導演作品。",
        "summary_en": "‘Un/Uttered — Asian Art Collectives in Dialogue & Micro Film Festival’ was co-hosted by OCAC, Tra-Travel (Japan) and Osaka Art Hub at FIGYA, Osaka, in February 2024. Programmed by P.M.S. with participants including Kawah Umei, Rngrang Hungul and Posak Jodian, the screenings featured works by Taiwanese indigenous directors: ‘My Days on Linsen North Road’, ‘I Am a Woman, I Am a Hunter’, ‘Mother Tongue’, ‘Ugaljai – Moth’ and ‘Misafafahiyan – Metamorphosis’.",
    },
    {
        "slug": "space-sandbox",
        "title_zh": "空間沙盒：作品展一件",
        "title_en": "Space Sandbox: One-Work Exhibition",
        "years": ["2021", "2022", "2023"],
        "keywords": ["空間沙盒", "作品展一件"],
        "summary_zh": "「空間沙盒：作品展一件」為打開－當代藝術工作站甘州街空間一樓的常態性展演計畫，以每一個月至一個半月為檔期，邀請跨領域藝術家在此實驗一件作品。此計畫曾與「一群人的自學」社群、跨域藝術家莊哲瑋等共同策劃，讓空間成為臨時的 live house、酒吧、服裝秀場，挑戰聽覺與視覺的嶄新敘事。",
        "summary_en": "‘Space Sandbox: One-Work Exhibition’ is a rolling programme on the ground floor of OCAC’s Ganzhou Street venue, with one-month to one-and-a-half-month slots inviting cross-disciplinary artists to experiment with a single work. Co-programmed at various points with the ‘A Group Self-Study’ community and cross-disciplinary artist Chuang Che-Wei, the space has turned into a pop-up live house, bar or fashion show — testing new auditory and visual narratives.",
    },
    {
        "slug": "a-group-self-study",
        "title_zh": "一群人的自學",
        "title_en": "A Group Self-Study",
        "years": ["2019", "2020", "2021", "2022", "2023"],
        "keywords": ["一群人的自學", "藝策互助會"],
        "summary_zh": "「一群人的自學」為一群對策展感興趣的朋友於 2016 年起自發組成的社群，每月最後一個週日晚間於打開－當代甘州街空間舉行讀書會或專題討論。2019 年夏天完成策展讀本《策展文化與文化策展》翻譯後，推出「藝術家策展人互助討論會（藝策互助會）」，將創作者主體納入策展自學之中。",
        "summary_en": "‘A Group Self-Study’ is a self-organised community of curators and curiosity-led friends who have been gathering at OCAC every last-Sunday evening since 2016. After finishing the Chinese translation of *Cultures of the Curatorial* in summer 2019, they launched the ‘Artist–Curator Mutual Aid Meeting’, folding artistic practitioners into their self-study process.",
    },
    {
        "slug": "areca-romance-ba-bau",
        "title_zh": "戀戀檳榔：打開－當代藝術工作站 X ba-bau AIR",
        "title_en": "Areca Romance: OCAC × ba-bau AIR",
        "years": ["2023"],
        "keywords": ["戀戀檳榔", "ba-bau"],
        "summary_zh": "《戀戀檳榔：打開－當代藝術工作站 X ba-bau AIR》為 2023 年打開－當代與越南 ba-bau AIR 的合作計畫，是《蜿蜒集》台越交流的重要起點之一。",
        "summary_en": "‘Areca Romance: OCAC × ba-bau AIR’ is a 2023 collaboration between OCAC and Vietnam-based ba-bau AIR, an early milestone of the broader ‘Meandering Collection’ Taiwan–Vietnam exchange.",
    },
    {
        "slug": "longtruk",
        "title_zh": "Longtruk: in the gap, in between",
        "title_en": "Longtruk: in the gap, in between",
        "years": ["2023"],
        "keywords": ["Longtruk"],
        "summary_zh": "《Longtruk: in the gap, in between》為 2023 年度執行的跨國策展研究計畫，延伸打開－當代對亞洲／東南亞區域的長期工作脈絡。",
        "summary_en": "‘Longtruk: in the gap, in between’ is a 2023 cross-border curatorial research project, extending OCAC’s long-term engagement with Asia / Southeast Asia.",
    },
    {
        "slug": "close-to-home-indigenous-directors",
        "title_zh": "Close to Home — 臺灣原住民導演作品選映",
        "title_en": "Close to Home — Taiwan Indigenous Directors Screening Series",
        "years": ["2025"],
        "keywords": ["Close to Home"],
        "summary_zh": "《Close to Home》為 2025 年度巡映計畫，將臺灣原住民導演作品帶往日惹、哥本哈根、巴黎等地，延續 Un/Uttered 以來對亞洲原住民族影像與聲音的持續關注。",
        "summary_en": "‘Close to Home’ is a 2025 touring screening programme that takes works by Taiwanese indigenous directors to Yogyakarta, Copenhagen and Paris, continuing the thread of indigenous moving-image and sound work opened by Un/Uttered.",
    },
]

def phase2():
    generated = []
    # Gather all images by year
    year_imgs = {}
    for y in YEARS:
        raw = json.loads((RAW / f"{y}.json").read_text())
        imgs = [img for p in raw["pages"] for img in p["images"]]
        # Also gather relevant pages/keywords for image selection
        year_imgs[y] = (imgs, raw)

    for proj in LONG_TERM_PROJECTS:
        # Find related images: pages in relevant years containing any keyword
        hero_candidates = []
        extra_imgs = []
        all_body_excerpts_zh = []
        for y in proj["years"]:
            if y not in year_imgs:
                continue
            imgs, raw = year_imgs[y]
            # scan pages
            for p in raw["pages"]:
                t = p["text"]
                if any(k in t for k in proj["keywords"]):
                    extra_imgs.extend(p["images"])
                    # excerpt: first 250 chars of page
                    all_body_excerpts_zh.append(f"**{y}**\n\n{t[:400].strip()}…")
        hero = pick_hero(extra_imgs or [img for y in proj["years"] if y in year_imgs for img in year_imgs[y][0]])

        # --- zh
        body_zh = proj["summary_zh"] + "\n\n"
        if all_body_excerpts_zh:
            body_zh += "## 各年度執行摘錄\n\n"
            for ex in all_body_excerpts_zh[:4]:
                body_zh += ex + "\n\n"
        if extra_imgs:
            body_zh += "## 圖像紀錄\n\n"
            seen_h = set()
            for img in extra_imgs[:10]:
                if img.get("hash") in seen_h:
                    continue
                seen_h.add(img.get("hash"))
                body_zh += f"![]({img['file']})\n\n"
        body_zh += "\n---\n\n*本長期計畫頁由 2019–2025 年度結案報告整理而成，內文、圖片仍在校正；若有錯漏歡迎回報。*\n"

        fm_zh = {
            "title": proj["title_zh"],
            "date": f"{max(proj['years'])}-12-31T00:00:00+08:00",
            "draft": False,
            "section": "archive",
            "image": hero,
            "tags": ["長期計畫"] + proj["years"],
        }
        zh_path = ZH / f"project-{proj['slug']}.md"
        write_md(zh_path, fm_zh, body_zh)
        generated.append(str(zh_path))

        # --- en
        body_en = proj["summary_en"] + "\n\n"
        if extra_imgs:
            body_en += "## Image record\n\n"
            seen_h = set()
            for img in extra_imgs[:10]:
                if img.get("hash") in seen_h:
                    continue
                seen_h.add(img.get("hash"))
                body_en += f"![]({img['file']})\n\n"
        body_en += "\n---\n\n*This long-term project page is compiled from OCAC’s 2019–2025 closing reports; English text and image–event matching are still being refined.*\n"
        fm_en = {
            "title": proj["title_en"],
            "date": f"{max(proj['years'])}-12-31T00:00:00+08:00",
            "draft": False,
            "section": "archive",
            "image": hero,
            "tags": ["long-term-project"] + proj["years"],
        }
        en_path = EN / f"project-{proj['slug']}.md"
        write_md(en_path, fm_en, body_en)
        generated.append(str(en_path))

    return generated

# --- Phase 3: Individual event stubs -------------------------------------

def phase3():
    generated = []
    for y in YEARS:
        raw = json.loads((RAW / f"{y}.json").read_text())
        events = detect_events(raw["pages"])
        seen_slugs = set()
        for ev in events:
            title = ev["title"].strip()
            body = ev["body"].strip()
            if len(title) < 3 or len(title) > 80:
                continue
            if re.match(r"^\d+$", title):
                continue
            # Filter generic / junk titles
            if title in ("", "年度計畫", "執行成果", "年度計畫（若申請二年度，請填寫二年度計畫）"):
                continue
            # Detect event date from body; fallback to year
            date = parse_date(body) or f"{y}-12-31"
            # Normalize to ISO datetime
            try:
                d = datetime.date.fromisoformat(date)
                date_iso = f"{d.isoformat()}T00:00:00+08:00"
            except Exception:
                date_iso = f"{y}-12-31T00:00:00+08:00"

            slug = slugify(title)
            key = f"{y}-{slug}"
            if key in seen_slugs:
                # Disambiguate
                key = f"{y}-{slug}-{ev['first_page']}"
            seen_slugs.add(key)

            hero = pick_hero(ev["images"])

            # zh body
            body_zh = body + "\n\n"
            if ev["images"]:
                body_zh += "## 圖像紀錄\n\n"
                seen_h = set()
                for img in ev["images"][:6]:
                    if img.get("hash") in seen_h:
                        continue
                    seen_h.add(img.get("hash"))
                    body_zh += f"![]({img['file']})\n\n"
            body_zh += f"\n---\n\n*本文由 {y} 年度結案報告自動整理生成；圖片與活動對應、文字準確度仍在校正中。*\n"

            fm_zh = {
                "title": title,
                "date": date_iso,
                "draft": False,
                "section": "archive",
                "image": hero,
                "tags": [y],
            }
            zh_path = ZH / f"{key}.md"
            write_md(zh_path, fm_zh, body_zh)
            generated.append(str(zh_path))

            # en body (stub — title translated, body original Chinese kept as reference)
            en_title = translate_title(title)
            body_en = (
                f"**Event (auto-generated stub; English description pending):**\n\n"
                f"- Year: {y}\n"
                f"- Source: OCAC {y} annual closing report (page {ev['first_page']}{'–'+str(ev['last_page']) if ev['last_page']!=ev['first_page'] else ''})\n\n"
                f"### Original Chinese text\n\n{body}\n\n"
            )
            if ev["images"]:
                body_en += "### Image record\n\n"
                seen_h = set()
                for img in ev["images"][:6]:
                    if img.get("hash") in seen_h:
                        continue
                    seen_h.add(img.get("hash"))
                    body_en += f"![]({img['file']})\n\n"
            body_en += f"\n---\n\n*Auto-generated from OCAC’s {y} annual closing report; English translation and image matching pending.*\n"

            fm_en = {
                "title": en_title,
                "date": date_iso,
                "draft": False,
                "section": "archive",
                "image": hero,
                "tags": [y],
            }
            en_path = EN / f"{key}.md"
            write_md(en_path, fm_en, body_en)
            generated.append(str(en_path))

    return generated

# --- Main -----------------------------------------------------------------

if __name__ == "__main__":
    print("=== Phase 1 ===")
    p1 = phase1()
    print(f"  wrote {len(p1)} files")
    print("=== Phase 2 ===")
    p2 = phase2()
    print(f"  wrote {len(p2)} files")
    print("=== Phase 3 ===")
    p3 = phase3()
    print(f"  wrote {len(p3)} files")
    print(f"\nTotal: {len(p1)+len(p2)+len(p3)} files")
