#!/usr/bin/env python3
"""Extract text + images from OCAC 2020-2025 annual reports.

Input: /Users/mashbean/Downloads/2019-2025 打開結案報告/*.pdf
Plus converted 2021 HTML.

Output:
  tmp/reports/raw/{year}.json  — per-year structured data (pages, blocks, images)
  static/images/reports/{year}/p{page}-i{idx}.{ext}  — extracted images
  tmp/reports/audit.md         — human-readable summary
"""
from pathlib import Path
import json
import re
import hashlib
import fitz  # PyMuPDF
from PIL import Image
import io

ROOT = Path("/Users/mashbean/Documents/AI-Agent/external/ocac-website/ocac-hugo")
SRC = Path("/Users/mashbean/Downloads/2019-2025 打開結案報告")
RAW = ROOT / "tmp/reports/raw"
IMG_ROOT = ROOT / "static/images/reports"
RAW.mkdir(parents=True, exist_ok=True)

FILES = {
    "2020": SRC / "2020 空間營運簡報-compressed.pdf",
    "2021_html": ROOT / "tmp/reports/2021.html",
    "2022": SRC / "2022 打開當代藝術工作站 視覺藝術組織營運專案.pdf",
    "2023": SRC / "2023 執行成果_打開＿當代藝術工作站.pdf",
    "2024": SRC / "2024 執行成果.pdf",
    "2025": SRC / "2025 執行成果_打開-當代藝術工作站.pdf",
}

MIN_IMG_BYTES = 15_000  # skip tiny ui icons; logos, etc. A 200x200 jpg is usually >15KB
MIN_DIM = 200

def extract_pdf(year: str, path: Path):
    print(f"\n=== {year}: {path.name} ===")
    doc = fitz.open(path)
    img_dir = IMG_ROOT / year
    img_dir.mkdir(parents=True, exist_ok=True)

    pages = []
    seen_hashes = set()

    for pno, page in enumerate(doc, 1):
        txt = page.get_text("text").strip()
        text_blocks = [b[4].strip() for b in page.get_text("blocks") if b[4].strip()]

        imgs = []
        for idx, info in enumerate(page.get_images(full=True)):
            xref = info[0]
            try:
                base = doc.extract_image(xref)
                raw = base["image"]
                ext = base["ext"]
            except Exception as e:
                continue
            h = hashlib.md5(raw).hexdigest()[:12]
            if h in seen_hashes:
                continue
            if len(raw) < MIN_IMG_BYTES:
                continue
            # dimension filter
            try:
                im = Image.open(io.BytesIO(raw))
                w, hdim = im.size
                if w < MIN_DIM or hdim < MIN_DIM:
                    continue
                # skip near-monochrome (covers, color blocks)
                if im.mode in ("RGB", "RGBA"):
                    small = im.convert("RGB").resize((32, 32))
                    px = list(small.getdata())
                    rs = [p[0] for p in px]; gs = [p[1] for p in px]; bs = [p[2] for p in px]
                    def var(xs):
                        m = sum(xs)/len(xs); return sum((x-m)**2 for x in xs)/len(xs)
                    if var(rs) < 50 and var(gs) < 50 and var(bs) < 50:
                        continue
            except Exception:
                continue
            seen_hashes.add(h)
            fname = f"p{pno:03d}-i{idx:02d}-{h}.{ext}"
            fpath = img_dir / fname
            fpath.write_bytes(raw)
            imgs.append({"file": f"/images/reports/{year}/{fname}", "w": w, "h": hdim, "hash": h})

        pages.append({"page": pno, "text": txt, "blocks": text_blocks, "images": imgs})

    out = RAW / f"{year}.json"
    out.write_text(json.dumps({"year": year, "source": path.name, "pages": pages}, ensure_ascii=False, indent=2))
    total_imgs = sum(len(p["images"]) for p in pages)
    print(f"  pages={len(pages)} imgs={total_imgs} → {out.name}")
    return {"year": year, "pages": len(pages), "images": total_imgs, "source": path.name}

def extract_html(year: str, path: Path):
    """Simpler: extract plain text from converted HTML. No embedded images expected."""
    print(f"\n=== {year}: {path.name} (HTML) ===")
    import subprocess
    # use textutil to plain text
    txt_path = path.with_suffix(".txt")
    if not txt_path.exists():
        subprocess.run(["textutil", "-convert", "txt", "-output", str(txt_path), str(path)], check=True)
    txt = txt_path.read_text()
    # Split on double newlines -> blocks
    blocks = [b.strip() for b in txt.split("\n\n") if b.strip()]
    pages = [{"page": 1, "text": txt, "blocks": blocks, "images": []}]
    out = RAW / f"{year}.json"
    out.write_text(json.dumps({"year": year, "source": path.name, "pages": pages}, ensure_ascii=False, indent=2))
    print(f"  blocks={len(blocks)} imgs=0 → {out.name}")
    return {"year": year, "pages": 1, "images": 0, "source": path.name}

def main():
    summary = []
    for key, p in FILES.items():
        if not p.exists():
            print(f"MISSING {key}: {p}")
            continue
        year = key.split("_")[0]
        if key.endswith("_html"):
            summary.append(extract_html(year, p))
        else:
            summary.append(extract_pdf(year, p))

    # Write audit
    audit = ["# OCAC report extraction audit\n"]
    audit.append("| Year | Source | Pages | Images |")
    audit.append("|---|---|---|---|")
    for s in summary:
        audit.append(f"| {s['year']} | {s['source']} | {s['pages']} | {s['images']} |")
    audit.append("\n")
    (ROOT / "tmp/reports/audit.md").write_text("\n".join(audit))
    print("\n" + "\n".join(audit))

if __name__ == "__main__":
    main()
