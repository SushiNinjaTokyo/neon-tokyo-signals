from __future__ import annotations

import duckdb


def ensure_columns(conn: duckdb.DuckDBPyConnection, table: str, columns: dict[str, str]) -> None:
    """Add newly introduced columns to existing DuckDB tables.

    CREATE TABLE IF NOT EXISTS does not evolve existing tables.  This helper is
    intentionally conservative and only performs ADD COLUMN for known fields.
    """
    try:
        existing = {r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}
    except Exception:
        return
    for name, dtype in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {dtype}")


def initialize_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS universe_master (
          ticker TEXT,
          code TEXT,
          name TEXT,
          market TEXT,
          sector TEXT,
          industry TEXT,
          theme TEXT,
          bucket TEXT,
          priority TEXT,
          asset_type TEXT,
          is_topix500 BOOLEAN,
          is_jpx_prime150 BOOLEAN,
          is_growth250 BOOLEAN,
          is_jpx_startup100 BOOLEAN,
          is_core BOOLEAN,
          is_growth BOOLEAN,
          is_small_discovery BOOLEAN,
          is_value_candidate BOOLEAN,
          is_excluded BOOLEAN,
          exclude_reason TEXT,
          source_detail TEXT,
          source_url TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices_daily (
          ticker TEXT,
          date DATE,
          open DOUBLE,
          high DOUBLE,
          low DOUBLE,
          close DOUBLE,
          adj_close DOUBLE,
          volume BIGINT,
          traded_value_jpy DOUBLE,
          source TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS price_fetch_failures (
          run_id TEXT,
          ticker TEXT,
          name TEXT,
          asset_type TEXT,
          reason TEXT,
          source_errors TEXT,
          created_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS features_daily (
          ticker TEXT,
          date DATE,
          close DOUBLE,
          volume BIGINT,
          traded_value_jpy DOUBLE,
          return_1d_pct DOUBLE,
          return_3d_pct DOUBLE,
          return_5d_pct DOUBLE,
          return_10d_pct DOUBLE,
          return_20d_pct DOUBLE,
          return_60d_pct DOUBLE,
          return_120d_pct DOUBLE,
          ma_5 DOUBLE,
          ma_10 DOUBLE,
          ma_20 DOUBLE,
          ma_50 DOUBLE,
          ma_60 DOUBLE,
          ma_120 DOUBLE,
          ma_200 DOUBLE,
          price_vs_ma20_pct DOUBLE,
          price_vs_ma50_pct DOUBLE,
          price_vs_ma60_pct DOUBLE,
          price_vs_ma120_pct DOUBLE,
          price_vs_ma200_pct DOUBLE,
          high_20d DOUBLE,
          high_60d DOUBLE,
          high_120d DOUBLE,
          high_252d DOUBLE,
          low_20d DOUBLE,
          low_60d DOUBLE,
          low_120d DOUBLE,
          low_252d DOUBLE,
          distance_from_20d_high_pct DOUBLE,
          distance_from_52w_high_pct DOUBLE,
          distance_from_20d_low_pct DOUBLE,
          distance_from_52w_low_pct DOUBLE,
          range_position_20d_0_1 DOUBLE,
          range_position_60d_0_1 DOUBLE,
          range_position_252d_0_1 DOUBLE,
          avg_volume_20d DOUBLE,
          avg_volume_50d DOUBLE,
          avg_traded_value_20d_jpy DOUBLE,
          avg_traded_value_50d_jpy DOUBLE,
          volume_ratio_20d DOUBLE,
          volume_ratio_50d DOUBLE,
          volume_dryup_10d DOUBLE,
          volume_reaccumulation_score DOUBLE,
          volatility_20d_annualized_pct DOUBLE,
          volatility_60d_annualized_pct DOUBLE,
          max_drawdown_20d_pct DOUBLE,
          max_drawdown_60d_pct DOUBLE,
          max_drawdown_120d_pct DOUBLE,
          rsi_14 DOUBLE,
          williams_r_14 DOUBLE,
          bollinger_b_20 DOUBLE,
          bollinger_width_20_pct DOUBLE,
          compression_20d_pct DOUBLE,
          trend_score_daily DOUBLE,
          trend_score_weekly_proxy DOUBLE,
          momentum_score_short DOUBLE,
          liquidity_score DOUBLE,
          risk_score DOUBLE,
          reversal_exhaustion_score DOUBLE,
          feature_quality TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fundamentals_latest (
          ticker TEXT,
          fiscal_period TEXT,
          fiscal_date DATE,
          market_cap_jpy DOUBLE,
          enterprise_value_jpy DOUBLE,
          per DOUBLE,
          pbr DOUBLE,
          psr DOUBLE,
          ev_ebitda DOUBLE,
          dividend_yield_pct DOUBLE,
          roe_pct DOUBLE,
          roa_pct DOUBLE,
          operating_margin_pct DOUBLE,
          net_margin_pct DOUBLE,
          equity_ratio_pct DOUBLE,
          revenue_growth_yoy_pct DOUBLE,
          operating_profit_growth_yoy_pct DOUBLE,
          eps_growth_yoy_pct DOUBLE,
          revenue_ttm DOUBLE,
          operating_profit_ttm DOUBLE,
          net_income_ttm DOUBLE,
          operating_cf_ttm DOUBLE,
          free_cf_ttm DOUBLE,
          source TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS value_features_daily (
          ticker TEXT,
          date DATE,
          valuation_discount_score DOUBLE,
          quality_guard_score DOUBLE,
          earnings_stability_score DOUBLE,
          shareholder_return_score DOUBLE,
          re_rating_signal_score DOUBLE,
          value_trap_penalty DOUBLE,
          value_mispricing_score DOUBLE,
          valuation_bucket TEXT,
          value_status TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_scores_daily (
          date DATE,
          agent_id TEXT,
          agent_name TEXT,
          ticker TEXT,
          name TEXT,
          universe_bucket TEXT,
          raw_score DOUBLE,
          normalized_score DOUBLE,
          rank INTEGER,
          action TEXT,
          signal_strength TEXT,
          entry_score DOUBLE,
          exit_score DOUBLE,
          risk_penalty DOUBLE,
          liquidity_penalty DOUBLE,
          reason_code_1 TEXT,
          reason_code_2 TEXT,
          reason_code_3 TEXT,
          reason_text TEXT,
          is_trade_candidate BOOLEAN,
          is_watch_candidate BOOLEAN,
          is_ignored BOOLEAN,
          created_at TIMESTAMP
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_daily_ticker_date ON prices_daily(ticker, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_features_daily_date_ticker ON features_daily(date, ticker)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_scores_daily ON agent_scores_daily(date, agent_id, rank)")

    # ------------------------------------------------------------------
    # AI Arena calendar-year season tables.
    # These tables are run_id-scoped so that live runs and rebuild runs can
    # coexist. This allows strategy-rule tuning during development without
    # destroying prior results.
    # ------------------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS company_master_jp (
          ticker TEXT,
          code TEXT,
          name_ja TEXT,
          name_en TEXT,
          market TEXT,
          sector TEXT,
          industry TEXT,
          description_en TEXT,
          website TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fundamentals_latest_jp (
          ticker TEXT,
          fiscal_period TEXT,
          market_cap_jpy DOUBLE,
          revenue_jpy DOUBLE,
          operating_profit_jpy DOUBLE,
          net_income_jpy DOUBLE,
          equity_jpy DOUBLE,
          roe_pct DOUBLE,
          roa_pct DOUBLE,
          per DOUBLE,
          pbr DOUBLE,
          psr DOUBLE,
          dividend_yield_pct DOUBLE,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_simulation_runs (
          run_id TEXT,
          year INTEGER,
          run_type TEXT,
          status TEXT,
          start_date DATE,
          end_date DATE,
          initial_capital_jpy DOUBLE,
          share_lot_size INTEGER,
          reset_positions_at_year_start BOOLEAN,
          force_close_positions_at_year_end BOOLEAN,
          strategy_rules_version TEXT,
          portfolio_rules_version TEXT,
          rules_hash TEXT,
          source_data_start_date DATE,
          source_data_end_date DATE,
          parent_run_id TEXT,
          promoted_from_run_id TEXT,
          is_display_run BOOLEAN,
          is_official BOOLEAN,
          rules_locked BOOLEAN,
          created_at TIMESTAMP,
          updated_at TIMESTAMP,
          frozen_at TIMESTAMP,
          note TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_display_runs (
          year INTEGER,
          display_type TEXT,
          run_id TEXT,
          status TEXT,
          selected_at TIMESTAMP,
          note TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_orders (
          run_id TEXT,
          order_id TEXT,
          agent_id TEXT,
          ticker TEXT,
          name TEXT,
          signal_date DATE,
          execution_date DATE,
          side TEXT,
          order_type TEXT,
          planned_price DOUBLE,
          execution_price DOUBLE,
          shares INTEGER,
          order_value_jpy DOUBLE,
          commission_jpy DOUBLE,
          slippage_jpy DOUBLE,
          order_status TEXT,
          reason_code TEXT,
          reason_text TEXT,
          created_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_open_positions (
          run_id TEXT,
          position_id TEXT,
          agent_id TEXT,
          ticker TEXT,
          name TEXT,
          entry_signal_date DATE,
          entry_date DATE,
          entry_price DOUBLE,
          shares INTEGER,
          cost_basis_jpy DOUBLE,
          last_date DATE,
          last_price DOUBLE,
          market_value_jpy DOUBLE,
          unrealized_pnl_jpy DOUBLE,
          unrealized_return_pct DOUBLE,
          holding_days INTEGER,
          high_water_return_pct DOUBLE,
          status TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_trades (
          run_id TEXT,
          trade_id TEXT,
          agent_id TEXT,
          ticker TEXT,
          name TEXT,
          entry_signal_date DATE,
          entry_date DATE,
          entry_price DOUBLE,
          exit_signal_date DATE,
          exit_date DATE,
          exit_price DOUBLE,
          shares INTEGER,
          realized_pnl_jpy DOUBLE,
          realized_return_pct DOUBLE,
          holding_days INTEGER,
          entry_reason_code TEXT,
          entry_reason_text TEXT,
          exit_reason_code TEXT,
          exit_reason_text TEXT,
          created_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_equity_curve (
          run_id TEXT,
          agent_id TEXT,
          date DATE,
          cash_jpy DOUBLE,
          market_value_jpy DOUBLE,
          realized_pnl_jpy DOUBLE,
          unrealized_pnl_jpy DOUBLE,
          portfolio_equity_jpy DOUBLE,
          daily_return_pct DOUBLE,
          total_return_pct DOUBLE,
          open_positions INTEGER,
          created_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_yearly_rankings (
          run_id TEXT,
          year INTEGER,
          agent_id TEXT,
          start_equity_jpy DOUBLE,
          end_equity_jpy DOUBLE,
          total_return_pct DOUBLE,
          realized_pnl_jpy DOUBLE,
          unrealized_pnl_jpy DOUBLE,
          max_drawdown_pct DOUBLE,
          win_rate_pct DOUBLE,
          trade_count INTEGER,
          rank INTEGER,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_monthly_rankings (
          run_id TEXT,
          year INTEGER,
          month INTEGER,
          agent_id TEXT,
          month_start_equity_jpy DOUBLE,
          month_end_equity_jpy DOUBLE,
          monthly_return_pct DOUBLE,
          realized_pnl_jpy DOUBLE,
          unrealized_pnl_jpy DOUBLE,
          rank INTEGER,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS arena_trade_rankings (
          run_id TEXT,
          year INTEGER,
          ranking_type TEXT,
          rank INTEGER,
          agent_id TEXT,
          ticker TEXT,
          name TEXT,
          entry_date DATE,
          exit_date DATE,
          entry_price DOUBLE,
          exit_price DOUBLE,
          shares INTEGER,
          realized_pnl_jpy DOUBLE,
          realized_return_pct DOUBLE,
          holding_days INTEGER,
          entry_reason_text TEXT,
          exit_reason_text TEXT,
          updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_pick_notes_daily (
          date DATE,
          agent_id TEXT,
          ticker TEXT,
          note_version TEXT,
          company_brief_en TEXT,
          signal_thesis_en TEXT,
          valuation_comment_en TEXT,
          risk_comment_en TEXT,
          generated_by TEXT,
          generated_at TIMESTAMP
        )
        """
    )

    ensure_columns(conn, "fundamentals_latest_jp", {
        "enterprise_value_jpy": "DOUBLE",
        "ev_ebitda": "DOUBLE",
        "operating_margin_pct": "DOUBLE",
        "net_margin_pct": "DOUBLE",
        "equity_ratio_pct": "DOUBLE",
        "revenue_growth_yoy_pct": "DOUBLE",
        "operating_profit_growth_yoy_pct": "DOUBLE",
        "eps_growth_yoy_pct": "DOUBLE",
        "source": "TEXT",
        "source_quality": "TEXT",
        "error": "TEXT",
    })
    ensure_columns(conn, "value_features_daily", {
        "fundamental_coverage_score": "DOUBLE",
        "source": "TEXT",
    })
    ensure_columns(conn, "arena_simulation_runs", {
        "finalized_season": "BOOLEAN",
    })

    conn.execute("CREATE INDEX IF NOT EXISTS idx_arena_equity_run_agent_date ON arena_equity_curve(run_id, agent_id, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_arena_trades_run_agent ON arena_trades(run_id, agent_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_arena_orders_run_date ON arena_orders(run_id, execution_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_arena_positions_run_agent ON arena_open_positions(run_id, agent_id)")
