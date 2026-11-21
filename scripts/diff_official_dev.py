#!/usr/bin/env python3
"""Compare public seed-1 dev rows with organizer's downloaded reference CSV."""
import csv
import datetime
import sys
from pathlib import Path

scratch = Path(sys.argv[1])
expected_dir = Path(sys.argv[2]) / "dev-answer"
epoch = datetime.date(1970, 1, 1)

def current(table):
    rows = {}
    with (scratch / (table + "_rows.csv")).open(newline="", encoding="utf-8") as f:
        for values in csv.reader(f):
            if table == "user":
                key = (bytes.fromhex(values[0]).decode("utf-8"),
                       (epoch + datetime.timedelta(days=int(values[1]))).isoformat())
                row = (int(values[2]), int(values[3]), int(values[4]),
                       None if values[5] == "NULL" else bytes.fromhex(values[5]).decode("utf-8"))
            else:
                key = (bytes.fromhex(values[0]).decode("utf-8"),
                       (epoch + datetime.timedelta(days=int(values[2]))).isoformat())
                row = (bytes.fromhex(values[1]).decode("utf-8"), *map(int, values[3:]))
            rows[key] = row
    return rows

def expected(table):
    rows = {}
    with (expected_dir / (table + "_daily.csv")).open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if table == "user":
                key = (r["user_id"], r["day"])
                row = (int(r["sessions"]), int(r["events"]), int(r["revenue_cents"]),
                       r["top_category"] or None)
            else:
                key = (r["campaign_id"], r["day"])
                row = (r["channel"], int(r["sessions"]), int(r["purchasing_sessions"]),
                       int(r["revenue_cents"]), int(r["assisted_sessions"]))
            rows[key] = row
    return rows

for table in ("user", "campaign"):
    got, want = current(table), expected(table)
    diff = [(key, want.get(key), got.get(key))
            for key in sorted(set(got) | set(want))
            if want.get(key) != got.get(key)]
    print(f"{table}: {len(got)} actual, {len(want)} expected; {len(diff)} differing keys")
    for key, e, g in diff[:20]:
        print(f"  KEY={key!r} EXPECTED={e!r} GOT={g!r}")
