from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.application.reporting import ReportingService
from app.infrastructure.persistence import (
    Answer,
    Attempt,
    AttemptStatus,
    Exam,
    ExamSetting,
    ExamStatus,
    Question,
    QuestionOption,
    Section,
    Student,
    User,
    UserRole,
    create_all,
    create_session_factory,
    create_sqlite_engine,
)
from app.infrastructure.reporting import ReportingRepository


def _build_reporting_service(tmp_path: Path) -> ReportingService:
    engine = create_sqlite_engine(tmp_path / "reporting.db")
    create_all(engine)
    session = create_session_factory(engine)()

    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password_hash="hashed",
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.flush()

    exam = Exam(
        code="ENG-REP",
        title="Reporting Exam",
        subject="English",
        status=ExamStatus.ACTIVE,
        created_by_user_id=admin.id,
    )
    exam.settings = ExamSetting(
        time_limit_minutes=30,
        min_questions=2,
        max_questions=2,
        passing_score=1,
    )
    session.add(exam)
    session.flush()

    section = Section(exam_id=exam.id, name="General", display_order=1)
    session.add(section)
    session.flush()

    student = Student(
        student_code="STU-REP",
        full_name="Report Student",
        email="student@example.com",
        password_hash="hashed",
        is_active=True,
    )
    session.add(student)
    session.flush()

    q1 = Question(
        exam_id=exam.id,
        section_id=section.id,
        external_ref="q1",
        stem_text="Question 1",
        difficulty_level=2,
        marks=1,
        is_active=True,
    )
    q1.options = [
        QuestionOption(option_key="A", option_text="Correct", is_correct=True, display_order=1),
        QuestionOption(option_key="B", option_text="Wrong", is_correct=False, display_order=2),
    ]
    q2 = Question(
        exam_id=exam.id,
        section_id=section.id,
        external_ref="q2",
        stem_text="Question 2",
        difficulty_level=2,
        marks=1,
        is_active=True,
    )
    q2.options = [
        QuestionOption(option_key="A", option_text="Wrong", is_correct=False, display_order=1),
        QuestionOption(option_key="B", option_text="Correct", is_correct=True, display_order=2),
    ]
    session.add_all([q1, q2])
    session.flush()

    attempt = Attempt(
        student_id=student.id,
        exam_id=exam.id,
        attempt_number=1,
        status=AttemptStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        target_question_count=2,
        current_question_number=2,
        total_answered=2,
    )
    session.add(attempt)
    session.flush()

    session.add_all(
        [
            Answer(
                attempt_id=attempt.id,
                question_id=q1.id,
                selected_option_id=q1.options[0].id,
                answered_at=datetime.now(timezone.utc),
                is_correct=True,
                awarded_marks=1,
            ),
            Answer(
                attempt_id=attempt.id,
                question_id=q2.id,
                selected_option_id=q2.options[0].id,
                answered_at=datetime.now(timezone.utc),
                is_correct=False,
                awarded_marks=0,
            ),
        ]
    )
    session.commit()
    return ReportingService(ReportingRepository(session))


def test_reporting_service_builds_student_results_and_exam_summaries(tmp_path: Path) -> None:
    service = _build_reporting_service(tmp_path)

    student_results = service.list_student_results()
    exam_summaries = service.list_exam_summaries()

    assert len(student_results) == 1
    assert student_results[0].student_code == "STU-REP"
    assert student_results[0].correct_answers == 1
    assert student_results[0].wrong_answers == 1
    assert student_results[0].score == 1.0
    assert student_results[0].percentage == 50.0

    assert len(exam_summaries) == 1
    assert exam_summaries[0].exam_code == "ENG-REP"
    assert exam_summaries[0].total_attempts == 1
    assert exam_summaries[0].completed_attempts == 1
    assert exam_summaries[0].average_score == 1.0
    assert exam_summaries[0].average_percentage == 50.0


def test_reporting_service_exports_csv_and_html(tmp_path: Path) -> None:
    service = _build_reporting_service(tmp_path)

    results_csv = service.export_student_results_csv(tmp_path / "student-results.csv")
    summaries_csv = service.export_exam_summaries_csv(tmp_path / "exam-summaries.csv")
    results_html = service.export_printable_student_results(tmp_path / "student-results.html")
    summaries_html = service.export_printable_exam_summaries(tmp_path / "exam-summaries.html")

    assert results_csv.exists()
    assert summaries_csv.exists()
    assert results_html.exists()
    assert summaries_html.exists()
    assert "student_code" in results_csv.read_text(encoding="utf-8")
    assert "ENG-REP" in summaries_csv.read_text(encoding="utf-8")
    assert "Student Results Report" in results_html.read_text(encoding="utf-8")
    assert "Exam Summary Report" in summaries_html.read_text(encoding="utf-8")
