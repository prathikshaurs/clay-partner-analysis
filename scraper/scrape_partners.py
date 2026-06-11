"""
Clay Partner Directory Scraper
================================
Collects the public solutions-partner directory from clay.com/experts.

Design principles (be a polite citizen):
  - Honest User-Agent that identifies you and gives a contact.
  - 2-3s delay between requests so we never stress their servers.
  - Local caching: once a page is fetched, it's saved to data/raw/.
    Re-runs read from cache instead of re-hitting the site.
  - Only touches PUBLIC pages (no login). robots.txt permits /experts.

Output:
  data/processed/partners_list.csv   <- one row per partner (list view)
  data/processed/partners_detail.csv <- enriched per-partner detail

Usage:
  python scrape_partners.py --pages 6
  python scrape_partners.py --detail        # also fetch each partner page
  python scrape_partners.py --no-cache      # force refresh

NOTE: Review clay.com/terms-of-service before running. This is built for a
personal portfolio analysis; do not republish the raw scraped data.
"""

import argparse
import csv
import hashlib
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---- config ------------------------------------------------------------
BASE = "https://www.clay.com/experts"
PARTNER_BASE = "https://www.clay.com/experts/partner"
HEADERS = {
    "User-Agent": "Prathiksha-Portfolio-Project (prathikshamurs@gmail.com)"
}
DELAY_SECONDS = 2.5
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# tier ranking, used later in dbt / analysis
TIER_RANK = {
    "Artisan": 1,
    "Advanced Artisan": 2,
    "Studio": 3,
    "Elite Studio": 4,
}


# ---- fetching with cache ----------------------------------------------
def _cache_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()[:16]
    return RAW_DIR / f"{key}.html"


def fetch(url: str, use_cache: bool = True) -> str:
    cp = _cache_path(url)
    if use_cache and cp.exists():
        return cp.read_text(encoding="utf-8")
    print(f"  GET {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    cp.write_text(resp.text, encoding="utf-8")
    time.sleep(DELAY_SECONDS)  
    return resp.text


# ---- parsing -----------------------------------------------------------
def parse_list_page(html: str) -> list[dict]:
    """
    Extract partner cards from a directory list page.
    Each card links to /experts/partner/<slug> and carries a tier label
    and a short tagline. The DOM may change; adjust selectors as needed.
    """
    soup = BeautifulSoup(html, "html.parser")
    partners = []
    seen = set()

    for a in soup.select('a[href*="/experts/partner/"]'):
        href = a.get("href", "")
        m = re.search(r"/experts/partner/([a-z0-9\-]+)", href)
        if not m:
            continue
        slug = m.group(1)
        if slug in seen:
            continue
        seen.add(slug)

        text = a.get_text(" ", strip=True)

        # Tier label usually appears as a leading badge in the card text
        tier = "Unknown"
        for t in ("Elite Studio", "Studio", "Advanced Artisan", "Artisan"):
            if t in text:
                tier = t
                break

        partners.append({
            "slug": slug,
            "profile_url": f"{PARTNER_BASE}/{slug}",
            "tier": tier,
            "tier_rank": TIER_RANK.get(tier, 0),
            "card_text": text[:300],
        })
    return partners


def parse_detail_page(html: str, slug: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    body = soup.get_text("\n", strip=True)

    def grab_after(label: str) -> str:
        lines = body.split("\n")
        for i, line in enumerate(lines):
            if line.strip().lower() == label.lower():
                # collect next non-empty lines until next known label
                results = []
                for j in range(i + 1, min(i + 8, len(lines))):
                    val = lines[j].strip()
                    if val and val.lower() not in [
                        "expertise", "icps", "industry", "language",
                        "pricing", "minimum engagement", "location",
                        "support", "resources"
                    ]:
                        results.append(val)
                    elif val.lower() in [
                        "expertise", "icps", "industry", "language",
                        "pricing", "minimum engagement", "location"
                    ]:
                        break
                return ", ".join(results) if results else ""
        return ""

    return {
        "slug": slug,
        "location": grab_after("Location"),
        "expertise": grab_after("Expertise"),
        "icps": grab_after("ICPs"),
        "industry": grab_after("Industry"),
        "language": grab_after("Language"),
        "pricing": grab_after("Pricing"),
        "min_engagement": grab_after("Minimum Engagement"),
        "description_len": len(body),
        "mentions_ex_clay": int(bool(re.search(
            r"\b(ex-?clay|employee #?\d+|former Clay)\b",
            body, re.IGNORECASE))),
        "mentions_hubspot": int("hubspot" in body.lower()),
        "mentions_salesforce": int("salesforce" in body.lower()),
    }


# ---- orchestration -----------------------------------------------------
def scrape(pages: int, detail: bool, use_cache: bool):
    all_partners = []
    for page in range(1, pages + 1):
        url = BASE if page == 1 else f"{BASE}?page={page}"
        print(f"List page {page}")
        html = fetch(url, use_cache=use_cache)
        rows = parse_list_page(html)
        print(f"  found {len(rows)} partners")
        all_partners.extend(rows)

    # de-dupe by slug across pages
    by_slug = {p["slug"]: p for p in all_partners}
    all_partners = list(by_slug.values())
    print(f"\nTotal unique partners: {len(all_partners)}")

    list_csv = OUT_DIR / "partners_list.csv"
    with open(list_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_partners[0].keys()))
        w.writeheader()
        w.writerows(all_partners)
    print(f"Wrote {list_csv}")

    if detail:
        details = []
        for i, p in enumerate(all_partners, 1):
            print(f"Detail {i}/{len(all_partners)}: {p['slug']}")
            try:
                html = fetch(p["profile_url"], use_cache=use_cache)
                details.append(parse_detail_page(html, p["slug"]))
            except Exception as e:
                print(f"  ! failed: {e}")
        detail_csv = OUT_DIR / "partners_detail.csv"
        with open(detail_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(details[0].keys()))
            w.writeheader()
            w.writerows(details)
        print(f"Wrote {detail_csv}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=6)
    ap.add_argument("--detail", action="store_true",
                    help="also fetch each partner's detail page")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()
    scrape(pages=args.pages, detail=args.detail, use_cache=not args.no_cache)
