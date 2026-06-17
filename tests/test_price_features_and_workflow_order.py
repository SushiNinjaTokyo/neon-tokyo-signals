from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib.duckdb_schema import initialize_schema  # noqa: E402
from sync_universe_master_from_csv_jp import sync_universe_master  # noqa: E402


class PriceFeaturesAndWorkflowOrderTests(unittest.TestCase):
    def test_build_price_features_after_universe_and_prices(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            db_path = tmp / "arena.duckdb"
            universe_csv = tmp / "universe.csv"
            out_dir = tmp / "site"
            universe_csv.write_text(
                "ticker,name,bucket,asset_type,is_excluded\n"
                "7203.T,Toyota,core,equity,false\n"
                "6758.T,Sony,core,equity,false\n",
                encoding="utf-8",
            )
            sync_universe_master(str(db_path), str(universe_csv))

            start = date(2026, 1, 1)
            rows = []
            for ticker, base in [("7203.T", 2500.0), ("6758.T", 3000.0)]:
                for i in range(80):
                    d = start + timedelta(days=i)
                    close = base + i
                    rows.append({
                        "ticker": ticker,
                        "date": d,
                        "open": close - 1,
                        "high": close + 2,
                        "low": close - 2,
                        "close": close,
                        "adj_close": close,
                        "volume": 1_000_000 + i,
                        "traded_value_jpy": close * (1_000_000 + i),
                        "source": "unit",
                        "updated_at": datetime(2026, 1, 1),
                    })
            con = duckdb.connect(str(db_path))
            initialize_schema(con)
            df = pd.DataFrame(rows)
            con.register("_prices", df)
            con.execute(
                """
                INSERT INTO prices_daily
                (ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy, source, updated_at)
                SELECT ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy, source, updated_at
                FROM _prices
                """
            )
            con.unregister("_prices")
            con.close()

            env = os.environ.copy()
            env["PRICE_DUCKDB_PATH"] = str(db_path)
            env["OUT_DIR"] = str(out_dir)
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_price_features_jp.py")],
                cwd=str(ROOT),
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            con = duckdb.connect(str(db_path), read_only=True)
            n = con.execute("SELECT COUNT(*) FROM features_daily").fetchone()[0]
            tickers = con.execute("SELECT COUNT(DISTINCT ticker) FROM features_daily").fetchone()[0]
            con.close()
            self.assertGreater(n, 0)
            self.assertEqual(tickers, 2)
            self.assertTrue((out_dir / "data/japan/ai-arena/diagnostics/price-features.json").exists())

    def test_refresh_workflows_materialize_universe_and_features_before_value(self) -> None:
        workflows = [
            ".github/workflows/ai-arena-jp-live-update.yml",
            ".github/workflows/ai-arena-jp-season-rebuild.yml",
            ".github/workflows/ai-arena-jp-war-room.yml",
        ]
        for wf in workflows:
            text = (ROOT / wf).read_text(encoding="utf-8")
            with self.subTest(workflow=wf):
                self.assertIn("scripts/sync_universe_master_from_csv_jp.py", text)
                self.assertIn("scripts/build_price_features_jp.py", text)
                sync_idx = text.index("- name: Sync universe_master")
                price_feature_idx = text.index("- name: Build JP price features")
                value_idx = text.index("- name: Build value features")
                self.assertLess(sync_idx, price_feature_idx)
                self.assertLess(price_feature_idx, value_idx)

    def test_live_update_order_prevents_bootstrap_next_failure(self) -> None:
        text = (ROOT / ".github/workflows/ai-arena-jp-live-update.yml").read_text(encoding="utf-8")
        names = [
            "- name: Restore canonical DuckDB or bootstrap new DB",
            "- name: Ensure JP index universe exists",
            "- name: Sync universe_master to DuckDB",
            "- name: Fetch JP prices",
            "- name: Build JP price features",
            "- name: Ensure JP fundamentals",
            "- name: Build value features",
            "- name: Build agent scores",
        ]
        positions = [text.index(n) for n in names]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
