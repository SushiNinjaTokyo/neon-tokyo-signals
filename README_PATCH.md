# Neon Tokyo Signals / AI Arena patch

## Scope
This patch is a full-file replacement package for the changed source/workflow/test files.

## Main changes
- Unifies `prices_daily` around the canonical DuckDB schema: `ticker,date,open,high,low,close,adj_close,volume,traded_value_jpy,source,updated_at`.
- Adds `scripts/export_prices_public_json_jp.py` to regenerate lightweight `site/data/prices-jp/latest.json` from DuckDB.
- Adds freshness validation in live/season workflows.
- Converts War Room workflow to `build_only` / `refresh_then_build` modes; scheduled runs use refresh mode and share the canonical DB concurrency lock.
- Adds `data_freshness` to War Room payload and prompt context.
- Simplifies Live Lab UI around the agent conversation; removes reveal-all / fast-preview controls.
- Makes the browser reveal queue global-time based, so all visitors see the same visible state at the same time.
- Adds unit tests for price schema, public JSON export, and War Room freshness classification.

## Local checks run
```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python - <<'PY'
import yaml
from pathlib import Path
for p in Path('.github/workflows').glob('*.yml'):
    yaml.safe_load(p.read_text())
print('yaml_ok')
PY
AI_ARENA_WAR_ROOM_MOCK_OPENAI=true AI_ARENA_WAR_ROOM_MARKET_CONTEXT=false OUT_DIR=site python scripts/build_ai_arena_war_room_jp.py
OUT_DIR=site python scripts/render_ai_arena_war_room_jp.py
```

## Notes
- Scheduled War Room refresh uses short yfinance timeout and Stooq fallback disabled by default.
- `site/data/prices-jp/latest.json` remains a compatibility artifact, not the canonical source. DuckDB is canonical.
- The package intentionally excludes generated `site/data/...` JSON and generated HTML except generated War Room CSS/JS assets.
