#!/usr/bin/env python3
"""Validate the official seed-1, 1M-event data without committing answer rows.

Fingerprints computed from the organizer-supplied dev-answer.zip.
"""
import hashlib
import json
import os
from pathlib import Path
import duckdb

REFERENCE = {
    "user_daily": (117038, "e45d027cb13dc403cdfa822d9d1c795f76d39a1412bef83b449c09898e8a16c6"),
    "campaign_daily": (27400, "e4c1dc234e92968ac078ea5acef82b75c7fd2e8cfa5dab11a93b2fbf243e3ce6"),
}
COLUMNS = {
    "user_daily": ("user_id", "day", "sessions", "events", "revenue_cents", "top_category"),
    "campaign_daily": ("campaign_id", "channel", "day", "sessions", "purchasing_sessions", "revenue_cents", "assisted_sessions"),
}
NUMERIC = {"sessions", "events", "revenue_cents", "purchasing_sessions", "assisted_sessions"}
INTEGER_TYPES = {"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT", "UHUGEINT"}
def main():
    conn = duckdb.connect(database=":memory:")
    output = Path(os.environ.get("OUTPUT_DIR", "/tmp/shopping-output"))
    ok = True
    for table, cols in COLUMNS.items():
        paths = sorted((output / table).glob("*.parquet"))
        if not paths:
            raise RuntimeError(f"{table} has no parquet files")
        q = "read_parquet(?)"
        schema = conn.execute("DESCRIBE SELECT * FROM "+q, [list(map(str,paths))]).fetchall()
        types = {x[0]:x[1] for x in schema}
        assert set(types) == set(cols), (table,types)
        assert types["day"] == "DATE", (table,types["day"])
        for k in cols:
            if k in NUMERIC:assert types[k] in INTEGER_TYPES,(table,k,types[k])
            elif k!="day":assert types[k] == "VARCHAR",(table,k,types[k])
        ordered = ",".join('"' + c + '"' for c in cols)
        rows = conn.execute(f"SELECT {ordered} FROM "+q,[list(map(str,paths))]).fetchall()
        encoded = []
        for row in rows:
            vals=[v.isoformat() if hasattr(v,"isoformat") else v for v in row]
            encoded.append(json.dumps(vals,ensure_ascii=False,separators=(",",":")).encode("utf-8"))
        h = hashlib.sha256()
        for item in sorted(encoded): h.update(item+bytes([10]))
        observed = (len(rows),h.hexdigest())
        expected = REFERENCE[table]
        passed=observed==expected
        ok &= passed
        print(f"{table}: {'PASS' if passed else 'FAIL'}; rows={observed[0]} sha256={observed[1]} expected={expected}",flush=True)
    if not ok:raise SystemExit(1)

if __name__=="__main__": main()
