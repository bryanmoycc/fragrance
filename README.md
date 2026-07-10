# Fragrance Profiles

A searchable local web app for browsing fragrance profiles: notes (top/middle/base),
main accords, brand, rating, price (low/avg/high), and (once populated) best seasons
to wear.

## Data

`data/parfumo_data_clean.csv` is an open (CC0) dataset of ~59K fragrances (Parfumo, via
the [R4DS TidyTuesday project](https://github.com/rfordatascience/tidytuesday/blob/main/data/2024/2024-12-10/readme.md)).
It covers name, brand, release year, concentration, rating, main accords, and notes.

`data/goldenscent_perfumes.csv` supplies price data (~1,556 of 59K fragrances, ~2.6%
coverage), sourced from [rawanalqarni/Perfumes_Recommender](https://github.com/rawanalqarni/Perfumes_Recommender)
on GitHub (a scrape of goldenscent.com, prices in SAR, converted to USD at the pegged
3.75:1 rate). **That repo has no open-source license**, so this is used for a private/
local project only — don't redistribute `data/goldenscent_perfumes.csv` or ship this as
a public product without sorting out licensing first. Matching to the Parfumo dataset is
fuzzy (brand + name similarity, see `scripts/merge_prices.py`) since the two sources
don't share IDs or naming conventions, so coverage is partial and a few matches may be
wrong.

**Season isn't in any open dataset found so far** — both Fragrantica and Parfumo
disallow AI-bot crawling in `robots.txt`, so that column exists in the schema but is
left `NULL` until filled from another source.

## Setup

```bash
python3 scripts/build_db.py     # builds data/fragrances.db from the notes CSV (gitignored)
python3 scripts/merge_prices.py # merges in price data from the GoldenScent CSV
python3 server.py               # serves the app at http://127.0.0.1:8000
```

No external dependencies — everything uses the Python standard library
(`sqlite3`, `http.server`, `difflib`) plus vanilla JS on the frontend.

## Adding season data

The `season` column lives on the `fragrances` table. Update it via SQL/script against
`data/fragrances.db`, or write a merge script like `scripts/merge_prices.py` once a
source is found, then rerun it.
