#!/usr/bin/env python3
"""Dependency-free dev server for the fragrance profile app.

Serves the static frontend plus a small JSON API backed by
data/fragrances.db (see scripts/build_db.py).
"""
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "fragrances.db"
STATIC_DIR = ROOT / "static"
PORT = 8000


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def split_list(value):
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def row_to_summary(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "brand": row["brand"],
        "release_year": row["release_year"],
        "main_accords": split_list(row["main_accords"]),
        "rating_value": row["rating_value"],
        "rating_count": row["rating_count"],
    }


def row_to_detail(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "brand": row["brand"],
        "release_year": row["release_year"],
        "concentration": row["concentration"],
        "rating_value": row["rating_value"],
        "rating_count": row["rating_count"],
        "main_accords": split_list(row["main_accords"]),
        "top_notes": split_list(row["top_notes"]),
        "middle_notes": split_list(row["middle_notes"]),
        "base_notes": split_list(row["base_notes"]),
        "perfumers": split_list(row["perfumers"]),
        "url": row["url"],
        "season": row["season"],
        "price_low": row["price_low"],
        "price_avg": row["price_avg"],
        "price_high": row["price_high"],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep stdout quiet; errors still raise

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, rel_path):
        path = (STATIC_DIR / rel_path).resolve()
        if STATIC_DIR not in path.parents and path != STATIC_DIR:
            self.send_error(404)
            return
        if not path.is_file():
            self.send_error(404)
            return
        content_type = "text/html"
        if path.suffix == ".css":
            content_type = "text/css"
        elif path.suffix == ".js":
            content_type = "application/javascript"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_static("index.html")
            return

        if parsed.path.startswith("/static/"):
            self.send_static(parsed.path[len("/static/"):])
            return

        if parsed.path == "/api/search":
            self.handle_search(params)
            return

        if parsed.path.startswith("/api/fragrance/"):
            frag_id = parsed.path.rsplit("/", 1)[-1]
            self.handle_detail(frag_id)
            return

        self.send_error(404)

    def handle_search(self, params):
        q = params.get("q", [""])[0].strip()
        brand = params.get("brand", [""])[0].strip()
        note = params.get("note", [""])[0].strip()
        limit = min(int(params.get("limit", ["24"])[0]), 100)
        offset = max(int(params.get("offset", ["0"])[0]), 0)

        clauses = []
        args = []
        if q:
            clauses.append("(name LIKE ? OR brand LIKE ?)")
            args += [f"%{q}%", f"%{q}%"]
        if brand:
            clauses.append("brand = ?")
            args.append(brand)
        if note:
            clauses.append(
                "(top_notes LIKE ? OR middle_notes LIKE ? OR base_notes LIKE ?)"
            )
            args += [f"%{note}%", f"%{note}%", f"%{note}%"]

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        conn = get_conn()
        total = conn.execute(
            f"SELECT COUNT(*) FROM fragrances {where}", args
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT * FROM fragrances {where}
                ORDER BY rating_count IS NULL, rating_count DESC, name
                LIMIT ? OFFSET ?""",
            args + [limit, offset],
        ).fetchall()
        conn.close()

        self.send_json(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": [row_to_summary(r) for r in rows],
            }
        )

    def handle_detail(self, frag_id):
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM fragrances WHERE id = ?", (frag_id,)
        ).fetchone()
        conn.close()
        if row is None:
            self.send_json({"error": "not found"}, status=404)
            return
        self.send_json(row_to_detail(row))


def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"{DB_PATH} not found. Run scripts/build_db.py first."
        )
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Serving on http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
