#!/usr/bin/env python3
from __future__ import annotations

"""Build the AI Arena Live Lab v5 payload.

This entrypoint is intentionally thin. The implementation lives in
`scripts/lib/war_room_lab_jp.py` so prompt engineering, market context,
hypothesis memory, casting, validation, and output writing can be maintained
without turning this script into another monolith.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from lib.war_room_lab_jp import build_payload, settings_from_env  # noqa: E402


def main() -> int:
    settings = settings_from_env(ROOT)
    payload = build_payload(settings)
    print(
        "AI Arena Live Lab generated:",
        payload.get("current_session", {}).get("session_type"),
        "messages=", payload.get("metrics", {}).get("message_count"),
        "hypotheses=", payload.get("metrics", {}).get("hypothesis_count"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
