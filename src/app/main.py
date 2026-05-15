from __future__ import annotations

from pathlib import Path

from app.bootstrap.desktop import run_admin_desktop


def main() -> int:
    return run_admin_desktop(Path("data") / "adaptive_exam.db")


if __name__ == "__main__":
    raise SystemExit(main())
