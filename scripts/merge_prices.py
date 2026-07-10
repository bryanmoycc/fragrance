#!/usr/bin/env python3
"""Merges retail price data into data/fragrances.db.

Source: rawanalqarni/Perfumes_Recommender on GitHub (GoldenScent.com
scrape, prices in SAR). That repo carries no open-source license, so
this is used for a private/local project only, not redistribution.
See README.md for the caveat.

Matching is fuzzy (brand, then product name via difflib) since the
GoldenScent catalog and the Parfumo dataset use different naming
conventions and don't share IDs. Coverage will be partial and some
matches may be wrong -- this is best-effort supplementary data, not
authoritative.
"""
import csv
import difflib
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDENSCENT_CSV = ROOT / "data" / "goldenscent_perfumes.csv"
DB_PATH = ROOT / "data" / "fragrances.db"

SAR_TO_USD = 1 / 3.75  # SAR is pegged to USD at 3.75:1
BRAND_MATCH_CUTOFF = 0.85
NAME_MATCH_CUTOFF = 0.55


def normalize(text):
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def load_goldenscent_prices():
    groups = defaultdict(list)
    with GOLDENSCENT_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*SAR\s*$", row["Price"] or "")
            if not m or not row["Brand"] or not row["Name"]:
                continue
            usd = float(m.group(1)) * SAR_TO_USD
            groups[(row["Name"].strip(), row["Brand"].strip())].append(usd)

    results = []
    for (name, brand), prices in groups.items():
        results.append(
            {
                "name": name,
                "brand": brand,
                "low": round(min(prices), 2),
                "avg": round(sum(prices) / len(prices), 2),
                "high": round(max(prices), 2),
            }
        )
    return results


def main():
    conn = sqlite3.connect(DB_PATH)
    parfumo_rows = conn.execute(
        "SELECT id, name, brand FROM fragrances WHERE brand IS NOT NULL"
    ).fetchall()

    brand_to_candidates = defaultdict(list)
    for pid, name, brand in parfumo_rows:
        brand_to_candidates[normalize(brand)].append((pid, normalize(name)))

    parfumo_brand_keys = list(brand_to_candidates.keys())
    brand_match_cache = {}

    def resolve_brand(norm_brand):
        if norm_brand in brand_match_cache:
            return brand_match_cache[norm_brand]
        if norm_brand in brand_to_candidates:
            result = norm_brand
        else:
            close = difflib.get_close_matches(
                norm_brand, parfumo_brand_keys, n=1, cutoff=BRAND_MATCH_CUTOFF
            )
            result = close[0] if close else None
        brand_match_cache[norm_brand] = result
        return result

    goldenscent_products = load_goldenscent_prices()
    matched = 0
    used_ids = set()
    updates = []

    for product in goldenscent_products:
        norm_brand = normalize(product["brand"])
        resolved_brand = resolve_brand(norm_brand)
        if resolved_brand is None:
            continue

        candidates = brand_to_candidates[resolved_brand]
        norm_name = normalize(product["name"])
        candidate_names = [c[1] for c in candidates]
        close = difflib.get_close_matches(
            norm_name, candidate_names, n=1, cutoff=NAME_MATCH_CUTOFF
        )
        if not close:
            continue

        match_index = candidate_names.index(close[0])
        pid = candidates[match_index][0]
        if pid in used_ids:
            continue

        used_ids.add(pid)
        matched += 1
        updates.append((product["low"], product["avg"], product["high"], pid))

    conn.executemany(
        "UPDATE fragrances SET price_low = ?, price_avg = ?, price_high = ? WHERE id = ?",
        updates,
    )
    conn.commit()

    total_parfumo = len(parfumo_rows)
    print(f"GoldenScent products with usable price: {len(goldenscent_products)}")
    print(f"Matched to fragrances.db rows: {matched}")
    print(f"Coverage: {matched}/{total_parfumo} ({matched / total_parfumo:.1%})")
    conn.close()


if __name__ == "__main__":
    main()
