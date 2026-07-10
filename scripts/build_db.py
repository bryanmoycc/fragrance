#!/usr/bin/env python3
"""Builds data/fragrances.db (SQLite) from data/parfumo_data_clean.csv.

Season and price fields have no open data source yet, so they're created
as empty columns to be filled in later (manually or from a future source).
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "parfumo_data_clean.csv"
DB_PATH = ROOT / "data" / "fragrances.db"

SCHEMA = """
CREATE TABLE fragrances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parfumo_number TEXT,
    name TEXT NOT NULL,
    brand TEXT,
    release_year INTEGER,
    concentration TEXT,
    rating_value REAL,
    rating_count INTEGER,
    main_accords TEXT,
    top_notes TEXT,
    middle_notes TEXT,
    base_notes TEXT,
    perfumers TEXT,
    url TEXT,
    season TEXT,
    price_low REAL,
    price_avg REAL,
    price_high REAL
);
CREATE INDEX idx_fragrances_name ON fragrances(name COLLATE NOCASE);
CREATE INDEX idx_fragrances_brand ON fragrances(brand COLLATE NOCASE);
"""


def na(value):
    return None if value in ("", "NA") else value


def na_num(value, cast):
    value = na(value)
    if value is None:
        return None
    try:
        return cast(value)
    except ValueError:
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                na(row["Number"]),
                row["Name"],
                na(row["Brand"]),
                na_num(row["Release_Year"], int),
                na(row["Concentration"]),
                na_num(row["Rating_Value"], float),
                na_num(row["Rating_Count"], int),
                na(row["Main_Accords"]),
                na(row["Top_Notes"]),
                na(row["Middle_Notes"]),
                na(row["Base_Notes"]),
                na(row["Perfumers"]),
                na(row["URL"]),
            )
            for row in reader
        ]

    conn.executemany(
        """INSERT INTO fragrances
           (parfumo_number, name, brand, release_year, concentration, rating_value,
            rating_count, main_accords, top_notes, middle_notes, base_notes,
            perfumers, url)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM fragrances").fetchone()[0]
    print(f"Loaded {count} fragrances into {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
