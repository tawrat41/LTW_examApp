from __future__ import annotations

from pathlib import Path

from app.bootstrap.student_desktop import run_student_desktop


def main() -> int:
    return run_student_desktop(Path("data") / "adaptive_exam.db")


if __name__ == "__main__":
    raise SystemExit(main())
