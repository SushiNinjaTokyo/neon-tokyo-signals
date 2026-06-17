from pathlib import Path
import tempfile
import unittest

import duckdb

from scripts.sync_universe_master_from_csv_jp import sync_universe_master


class UniverseMasterSyncTests(unittest.TestCase):
    def test_sync_universe_master_from_symbol_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "universe.csv"
            db_path = root / "arena.duckdb"
            csv_path.write_text(
                "symbol,name,theme,bucket,priority,market,sector,asset_type,is_topix500,is_jpx_prime150,is_growth250,is_jpx_startup100,source_detail,source_url\n"
                "7203.T,Toyota,,Core,A,Prime,Transportation,equity,true,false,false,false,topix500,url\n"
                "218A.T,Liberaware,Drone,Discovery,A,Growth,,equity,false,false,true,true,growth250|jpx_startup100,url\n",
                encoding="utf-8",
            )

            result = sync_universe_master(str(db_path), str(csv_path))
            self.assertEqual(result["csv_rows_loaded"], 2)
            self.assertEqual(result["universe_master_equity_rows"], 2)

            con = duckdb.connect(str(db_path), read_only=True)
            rows = con.execute(
                """
                SELECT ticker, code, name, asset_type, is_core, is_growth, is_small_discovery, is_value_candidate
                FROM universe_master
                ORDER BY ticker
                """
            ).fetchall()
            con.close()
            self.assertEqual(rows[0][0], "218A.T")
            self.assertEqual(rows[0][1], "218A")
            self.assertTrue(rows[0][5])
            self.assertTrue(rows[0][6])
            self.assertTrue(rows[0][7])
            self.assertEqual(rows[1][0], "7203.T")
            self.assertTrue(rows[1][4])


if __name__ == "__main__":
    unittest.main()
