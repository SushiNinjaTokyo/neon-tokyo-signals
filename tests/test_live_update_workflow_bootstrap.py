from pathlib import Path
import unittest


class LiveUpdateWorkflowBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = Path('.github/workflows/ai-arena-jp-live-update.yml').read_text(encoding='utf-8')

    def test_live_update_can_bootstrap_missing_canonical_duckdb(self) -> None:
        self.assertIn('Restore canonical DuckDB or bootstrap new DB', self.workflow)
        self.assertIn('CANONICAL_DUCKDB_BOOTSTRAP=true', self.workflow)
        self.assertIn('Guard skip price fetch during bootstrap', self.workflow)
        self.assertIn('gh release create "${CANONICAL_DUCKDB_RELEASE_TAG}"', self.workflow)

    def test_live_update_ensures_fundamentals_before_value_features(self) -> None:
        ensure_idx = self.workflow.index('- name: Ensure JP fundamentals')
        value_idx = self.workflow.index('- name: Build value features')
        self.assertLess(ensure_idx, value_idx)
        self.assertIn('fundamentals_latest_jp is empty or missing', self.workflow)
        self.assertIn('python scripts/fetch_fundamentals_jp.py', self.workflow)
        self.assertIn('fundamentals_latest_jp is still empty after fetch_fundamentals_jp.py', self.workflow)

    def test_live_update_sets_price_fetch_timeout_envs(self) -> None:
        self.assertIn('STOOQ_FALLBACK_ENABLED: "false"', self.workflow)
        self.assertIn('YFINANCE_TIMEOUT_SECONDS: "10"', self.workflow)
        self.assertIn('PRICE_FETCH_SLEEP_SECONDS: "0.05"', self.workflow)


if __name__ == '__main__':
    unittest.main()
