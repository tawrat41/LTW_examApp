from __future__ import annotations

import csv
import html
from pathlib import Path

from app.infrastructure.reporting.repositories import ReportingRepository

from .dto import ExamSummaryView, StudentResultView


class ReportingError(Exception):
    pass


class ReportingService:
    def __init__(self, repository: ReportingRepository) -> None:
        self._repository = repository

    def list_student_results(self) -> list[StudentResultView]:
        return self._repository.list_student_results()

    def list_exam_summaries(self) -> list[ExamSummaryView]:
        return self._repository.list_exam_summaries()

    def export_student_results_csv(self, output_path: str | Path) -> Path:
        results = self.list_student_results()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "attempt_id",
                    "student_id",
                    "student_code",
                    "student_name",
                    "exam_id",
                    "exam_code",
                    "exam_title",
                    "completed_at",
                    "total_questions",
                    "answered_questions",
                    "correct_answers",
                    "wrong_answers",
                    "unanswered_questions",
                    "score",
                    "percentage",
                    "status",
                ]
            )
            for item in results:
                writer.writerow(
                    [
                        item.attempt_id,
                        item.student_id,
                        item.student_code,
                        item.student_name,
                        item.exam_id,
                        item.exam_code,
                        item.exam_title,
                        item.completed_at_iso or "",
                        item.total_questions,
                        item.answered_questions,
                        item.correct_answers,
                        item.wrong_answers,
                        item.unanswered_questions,
                        f"{item.score:.2f}",
                        f"{item.percentage:.2f}",
                        item.status,
                    ]
                )
        return path

    def export_exam_summaries_csv(self, output_path: str | Path) -> Path:
        summaries = self.list_exam_summaries()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "exam_id",
                    "exam_code",
                    "exam_title",
                    "total_attempts",
                    "completed_attempts",
                    "average_score",
                    "average_percentage",
                    "highest_score",
                    "lowest_score",
                ]
            )
            for item in summaries:
                writer.writerow(
                    [
                        item.exam_id,
                        item.exam_code,
                        item.exam_title,
                        item.total_attempts,
                        item.completed_attempts,
                        f"{item.average_score:.2f}",
                        f"{item.average_percentage:.2f}",
                        f"{item.highest_score:.2f}",
                        f"{item.lowest_score:.2f}",
                    ]
                )
        return path

    def export_printable_student_results(self, output_path: str | Path) -> Path:
        results = self.list_student_results()
        rows = "\n".join(
            (
                "<tr>"
                f"<td>{html.escape(item.student_code)}</td>"
                f"<td>{html.escape(item.student_name)}</td>"
                f"<td>{html.escape(item.exam_title)}</td>"
                f"<td>{item.correct_answers}/{item.total_questions}</td>"
                f"<td>{item.score:.2f}</td>"
                f"<td>{item.percentage:.2f}%</td>"
                f"<td>{html.escape(item.status)}</td>"
                "</tr>"
            )
            for item in results
        )
        return self._write_html_report(
            output_path,
            title="Student Results Report",
            content=(
                "<table>"
                "<thead><tr><th>Student ID</th><th>Name</th><th>Exam</th><th>Correct</th>"
                "<th>Score</th><th>Percentage</th><th>Status</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            ),
        )

    def export_printable_exam_summaries(self, output_path: str | Path) -> Path:
        summaries = self.list_exam_summaries()
        rows = "\n".join(
            (
                "<tr>"
                f"<td>{html.escape(item.exam_code)}</td>"
                f"<td>{html.escape(item.exam_title)}</td>"
                f"<td>{item.total_attempts}</td>"
                f"<td>{item.completed_attempts}</td>"
                f"<td>{item.average_score:.2f}</td>"
                f"<td>{item.average_percentage:.2f}%</td>"
                f"<td>{item.highest_score:.2f}</td>"
                f"<td>{item.lowest_score:.2f}</td>"
                "</tr>"
            )
            for item in summaries
        )
        return self._write_html_report(
            output_path,
            title="Exam Summary Report",
            content=(
                "<table>"
                "<thead><tr><th>Code</th><th>Exam</th><th>Total Attempts</th><th>Completed</th>"
                "<th>Avg Score</th><th>Avg %</th><th>High</th><th>Low</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            ),
        )

    def _write_html_report(self, output_path: str | Path, *, title: str, content: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; margin: 32px; color: #1f2933; }}
    h1 {{ color: #143642; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #cbd2d9; padding: 10px; text-align: left; }}
    thead th {{ background: #e9dfcf; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  {content}
</body>
</html>"""
        path.write_text(page, encoding="utf-8")
        return path
