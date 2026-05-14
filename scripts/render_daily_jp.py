from __future__ import annotations

from render_common import OUT_DIR, env, generated_at, read_json, write_text, copy_asset


def main() -> None:
    e = env()
    daily = read_json(OUT_DIR / "data" / "daily-v2-jp" / "latest.json", {"date": "Unknown", "items": []})

    html = e.get_template("daily_jp.html.j2").render(
        generated_at=generated_at(),
        daily=daily,
        items=daily.get("items", []),
    )

    write_text(OUT_DIR / "japan" / "daily" / "index.html", html)
    copy_asset("base.css", "base.css")
    copy_asset("daily_jp.css", "daily_jp.css")


if __name__ == "__main__":
    main()
