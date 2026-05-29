# AI Arena Season Engine - Safe Implementation Steps

## 0. Commit the diff files

Copy the files in this ZIP into the repository root and commit them.
Do not delete old Daily / Weekly / old AI Arena files yet.

## 1. First smoke test: season rebuild, no GPT

Run workflow manually:

- Workflow: `AI Arena JP season rebuild`
- year: `2026`
- start_date: `2026-01-01`
- end_date: blank or today's date
- universe_limit: `300`
- run_mode: `rebuild`
- reset_run: `true`
- promote_display_run: `true`
- enable_gpt_signal_notes: `false`
- commit_outputs: `true`

Expected generated outputs:

- `site/data/japan/ai-arena/live/latest.json`
- `site/data/japan/ai-arena/ranking/latest.json`
- `site/data/japan/ai-arena/positions/latest.json`
- `site/data/japan/ai-arena/summary/latest.json`
- `site/data/japan/ai-arena/summary/2026/latest.json`
- `site/data/japan/ai-arena/signals/latest.json`
- `site/data/japan/ai-arena/agents/latest.json`
- `site/data/japan/ai-arena/log/latest.json`
- `site/japan/ai-arena/summary/index.html`
- `site/japan/ai-arena/signals/index.html`
- `site/japan/ai-arena/agents/index.html`

## 2. Verify the site

Open:

- `/japan/ai-arena/summary/`
- `/japan/ai-arena/signals/`
- `/japan/ai-arena/agents/`

Check:

- 7 agents are shown.
- Ranking rows exist.
- Signals cards exist.
- No Daily / Weekly JSON is required by the new season rebuild.
- Repository size does not grow from dated price JSONs.

## 3. Run prune dry run

Run workflow manually:

- Workflow: `AI Arena JP prune generated artifacts`
- dry_run: `true`
- commit_outputs: `true`

Review:

- `site/data/japan/ai-arena/prune-report.json`

Then run again with:

- dry_run: `false`

## 4. Live update workflow

Run workflow manually:

- Workflow: `AI Arena JP live update`
- year: `2026`
- commit_outputs: `true`

Only after repeated success should you uncomment the schedule block in:

- `.github/workflows/ai-arena-jp-live-update.yml`
- `.github/workflows/ai-arena-jp-prune-generated-artifacts.yml`

## 5. Rule tuning and historical rebuilds

During development, change YAML rules and run `AI Arena JP season rebuild` again.
Each rebuild creates a new run_id such as:

- `arena_jp_rebuild_2026_v001`
- `arena_jp_rebuild_2026_v002`

Use `promote_display_run=true` to make the new result the visible run.

## 6. Legacy cleanup - not yet

Do not delete old workflows/scripts until the new AI Arena pages have been stable.
The generated list is here:

- `site/data/japan/ai-arena/legacy_cleanup_candidates.json`
- `site/data/japan/ai-arena/legacy_cleanup_candidates.md`

Delete candidates only after:

- season rebuild works
- live update works
- summary/signals/agents pages render correctly
- ranking/positions old pages are migrated or confirmed compatible
- no page depends on Daily / Weekly generated JSON anymore
