from __future__ import annotations

from pathlib import Path

from render_common import OUT_DIR, env, generated_at, read_json, write_text, copy_asset


def main() -> None:
    e = env()
    daily = read_json(OUT_DIR / "data" / "daily-v2-jp" / "latest.json", {"items": []})
    weekly = read_json(OUT_DIR / "data" / "weekly-jp" / "latest.json", {"items": []})

    top = daily.get("items", [{}])[0] if daily.get("items") else {}

    html = e.get_template("index.html.j2").render(
        brand="Neon Tokyo Signals",
        tagline="Japan equity signals after the Tokyo close.",
        generated_at=generated_at(),
        top=top,
        daily=daily,
        weekly=weekly,
    )

    write_text(OUT_DIR / "index.html", html)
    copy_asset("base.css", "base.css")
    copy_asset("index.css", "index.css")


if __name__ == "__main__":
    main()
