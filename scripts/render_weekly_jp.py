from __future__ import annotations

from render_common import OUT_DIR, env, generated_at, read_json, write_text, copy_asset


def main() -> None:
    e = env()
    weekly = read_json(OUT_DIR / "data" / "weekly-jp" / "latest.json", {"date": "Unknown", "items": []})

    html = e.get_template("weekly_jp.html.j2").render(
        generated_at=generated_at(),
        weekly=weekly,
        items=weekly.get("items", []),
    )

    write_text(OUT_DIR / "japan" / "weekly" / "index.html", html)
    copy_asset("base.css", "base.css")
    copy_asset("weekly_jp.css", "weekly_jp.css")


if __name__ == "__main__":
    main()
