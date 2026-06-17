# AI Arena canonical DuckDB bootstrap fix

## Fixed issue

The previous `AI Arena JP live update` workflow failed before it could create or refresh DuckDB when the GitHub Release existed without the expected `neon_tokyo_jp_latest.duckdb.zst` asset, or when the Release did not exist yet.

Observed error:

```text
no assets match the file pattern
```

That was not a DuckDB SQL/schema failure. It was a workflow bootstrap failure: the workflow that is supposed to publish the canonical DuckDB required the canonical DuckDB to already exist.

## New behavior

`.github/workflows/ai-arena-jp-live-update.yml` now does this:

1. Try to restore `neon_tokyo_jp_latest.duckdb.zst` from the canonical GitHub Release.
2. If the Release or asset is missing, enter controlled bootstrap mode.
3. In bootstrap mode, continue to `fetch_prices_jp.py`, which creates and initializes `data/cache/neon_tokyo_jp.duckdb`.
4. Build value features, scores, AI Arena outputs, War Room payload, and static pages.
5. Stamp metadata.
6. Compress and publish `neon_tokyo_jp_latest.duckdb.zst` back to the canonical Release.

## Guardrail

If `skip_price_fetch=true` and no canonical DuckDB was restored, the workflow still hard-fails. This is intentional: without either an existing DB or a fresh price fetch, continuing would generate stale/invalid outputs.

## Apply

Copy this folder over the repository root and overwrite the existing file:

```text
.github/workflows/ai-arena-jp-live-update.yml
```

Then commit and push.

## Validation performed

```bash
python - <<'PY'
import yaml
from pathlib import Path
for p in Path('.github/workflows').glob('*.yml'):
    yaml.safe_load(p.read_text())
print('yaml_ok')
PY

python -m compileall scripts tests
python -m unittest discover -s tests -v
OUT_DIR=site python scripts/render_all.py
```

Result:

```text
yaml_ok
Ran 3 tests ... OK
render_all.py completed
```
