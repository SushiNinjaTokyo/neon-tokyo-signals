# Neon Tokyo Signals

Prototype static site for Japan equity signals after the Tokyo close.

## Structure

- `data/` input/sample data
- `scripts/` Python render scripts
- `templates/` Jinja2 templates and CSS
- `site/` generated Vercel output
- `.github/workflows/` GitHub Actions

## Vercel

Use these settings:

- Framework Preset: Other
- Build Command: blank
- Output Directory: `site`

## Browser-only update flow

1. Upload this folder to GitHub.
2. Import the repository into Vercel.
3. To regenerate pages, run GitHub Actions → `render-only` → `Run workflow`.

## Local render command

```bash
pip install -r requirements.txt
python scripts/render_all.py
```

Informational only. Not investment advice.
