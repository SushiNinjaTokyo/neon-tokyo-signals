from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from fetch_prices_jp import ensure_prices_schema, normalize_price_dataframe, upsert_prices  # noqa: E402
from export_prices_public_json_jp import build_payload  # noqa: E402
from lib.war_room_lab_jp import build_data_freshness  # noqa: E402


class PriceSchemaAndExportTests(unittest.TestCase):
    def test_prices_daily_schema_and_upsert_include_canonical_columns(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.duckdb"
            con = duckdb.connect(str(db_path))
            try:
                ensure_prices_schema(con)
                cols = {r[1] for r in con.execute("PRAGMA table_info('prices_daily')").fetchall()}
                self.assertTrue({"ticker", "date", "open", "high", "low", "close", "adj_close", "volume", "traded_value_jpy", "source", "updated_at"}.issubset(cols))
                self.assertNotIn("name", cols)
                raw = pd.DataFrame({"Date": ["2026-06-01", "2026-06-02"], "Open": [100, 105], "High": [110, 108], "Low": [99, 104], "Close": [106, 107], "Adj Close": [105.5, 106.5], "Volume": [1000, 2000]})
                df = normalize_price_dataframe(raw, ticker="7203.T", source="unit")
                self.assertEqual(list(df.columns), ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume", "traded_value_jpy", "source", "updated_at"])
                self.assertEqual(df["traded_value_jpy"].tolist(), [106000, 214000])
                self.assertEqual(upsert_prices(con, df), 2)
                row = con.execute("SELECT adj_close, traded_value_jpy FROM prices_daily WHERE ticker='7203.T' AND date='2026-06-02'").fetchone()
                self.assertEqual(row, (106.5, 214000.0))
            finally:
                con.close()

    def test_public_price_export_is_lightweight_and_duckdb_derived(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            con = duckdb.connect(str(Path(td) / "test.duckdb"))
            try:
                ensure_prices_schema(con)
                now = datetime.now(timezone.utc)
                rows = pd.DataFrame([
                    {"ticker": "7203.T", "date": "2026-06-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "adj_close": 100.0, "volume": 1000, "traded_value_jpy": 100000.0, "source": "unit", "updated_at": now},
                    {"ticker": "7203.T", "date": "2026-06-02", "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0, "adj_close": 102.0, "volume": 2000, "traded_value_jpy": 204000.0, "source": "unit", "updated_at": now},
                ])
                upsert_prices(con, rows)
                payload = build_payload(con, {"7203.T": "Toyota Motor"}, max_stale_calendar_days=9999)
                self.assertEqual(payload["schema_version"], "neon_tokyo_prices_jp_summary_v2")
                self.assertEqual(payload["public_json_mode"], "summary")
                self.assertIs(payload["bars_omitted"], True)
                self.assertEqual(payload["items"][0]["ticker"], "7203.T")
                self.assertEqual(payload["items"][0]["name"], "Toyota Motor")
                self.assertEqual(payload["items"][0]["return_1d_pct"], 2.0)
                self.assertNotIn("bars", payload["items"][0])
            finally:
                con.close()

    def test_data_freshness_flags_stale_inputs(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        ctx = {"raw": {"generated_at": old}, "payloads": {"live": {"generated_at": old}}}
        prices = {"generated_at": old, "latest_price_date": "2020-01-01", "ticker_count": 1, "freshness": {"is_stale": True, "stale_reason": "unit_old"}}
        freshness = build_data_freshness(ctx, prices)
        self.assertEqual(freshness["level"], "stale")
        self.assertIs(freshness["is_stale"], True)
        self.assertIn("unit_old", freshness["stale_reason"])


if __name__ == "__main__":
    unittest.main()
