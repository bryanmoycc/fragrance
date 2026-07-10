# Fragrance Profiles

A searchable local web app for browsing fragrance profiles: notes (top/middle/base),
main accords, brand, rating, and (once populated) best seasons to wear and price range.

## Data

`data/parfumo_data_clean.csv` is an open dataset of ~59K fragrances (Parfumo, via the
[R4DS TidyTuesday project](https://github.com/rfordatascience/tidytuesday/blob/main/data/2024/2024-12-10/readme.md)).
It covers name, brand, release year, concentration, rating, main accords, and notes.

**Season and price are not in any open dataset found so far** — both Fragrantica and
Parfumo disallow AI-bot crawling in `robots.txt`, so those columns exist in the schema
but are left `NULL` until filled from another source (manual entry, a licensed dataset,
or retailer data you provide).

## Setup

```bash
python3 scripts/build_db.py   # builds data/fragrances.db from the CSV (gitignored)
python3 server.py             # serves the app at http://127.0.0.1:8000
```

No external dependencies — everything uses the Python standard library
(`sqlite3`, `http.server`) plus vanilla JS on the frontend.

## Adding season / price data

Both columns live on the `fragrances` table (`season`, `price_low`, `price_avg`,
`price_high`). Update them via SQL/script against `data/fragrances.db`, or extend
`scripts/build_db.py` to merge in a new source, then rerun it.
