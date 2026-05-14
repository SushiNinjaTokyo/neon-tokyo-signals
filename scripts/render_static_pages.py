from __future__ import annotations

from render_common import OUT_DIR, env, generated_at, write_text


def main() -> None:
    e = env()
    for name, out_path in [
        ("disclaimer.html.j2", OUT_DIR / "disclaimer" / "index.html"),
        ("privacy.html.j2", OUT_DIR / "privacy" / "index.html"),
    ]:
        html = e.get_template(name).render(generated_at=generated_at())
        write_text(out_path, html)


if __name__ == "__main__":
    main()
