from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.application.reporting.dto import ExamSummaryView, StudentResultView
from app.infrastructure.persistence.models import Answer, Attempt, Exam, Student


class ReportingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_student_results(self) -> list[StudentResultView]:
        stmt = (
            select(Attempt)
            .options(
                joinedload(Attempt.student),
                joinedload(Attempt.exam).joinedload(Exam.settings),
                joinedload(Attempt.answers).joinedload(Answer.question),
            )
            .order_by(Attempt.completed_at.desc(), Attempt.created_at.desc())
        )
        attempts = self._session.scalars(stmt).unique().all()
        return [self._to_student_result(item) for item in attempts]

    def list_exam_summaries(self) -> list[ExamSummaryView]:
        stmt = (
            select(Exam)
            .options(
                joinedload(Exam.attempts).joinedload(Attempt.answers),
                joinedload(Exam.settings),
            )
            .order_by(Exam.title.asc())
        )
        exams = self._session.scalars(stmt).unique().all()
        return [self._to_exam_summary(item) for item in exams]

    def _to_student_result(self, attempt: Attempt) -> StudentResultView:
        answers = list(attempt.answers)
        correct_answers = len([item for item in answers if item.is_correct is True])
        wrong_answers = len([item for item in answers if item.is_correct is False])
        answered_questions = len(answers)
        total_questions = attempt.target_question_count
        unanswered_questions = max(total_questions - answered_questions, 0)
        score = float(sum(float(item.awarded_marks) for item in answers))
        percentage = (score / total_questions) * 100 if total_questions else 0.0
        passing_score = float(attempt.exam.settings.passing_score) if (attempt.exam and attempt.exam.settings) else 40.0
        return StudentResultView(
            attempt_id=str(attempt.id),
            student_id=str(attempt.student.id),
            student_code=attempt.student.student_code,
            student_name=attempt.student.full_name,
            exam_id=str(attempt.exam.id),
            exam_code=attempt.exam.code,
            exam_title=attempt.exam.title,
            completed_at_iso=attempt.completed_at.isoformat() if attempt.completed_at else None,
            total_questions=total_questions,
            answered_questions=answered_questions,
            correct_answers=correct_answers,
            wrong_answers=wrong_answers,
            unanswered_questions=unanswered_questions,
            score=score,
            percentage=percentage,
            status="passed" if percentage >= passing_score else "failed" if attempt.status.value == "completed" else attempt.status.value,
        )

    def _to_exam_summary(self, exam: Exam) -> ExamSummaryView:
        attempts = list(exam.attempts)
        completed_attempts = [item for item in attempts if item.completed_at is not None]
        scores = [float(sum(float(answer.awarded_marks) for answer in attempt.answers)) for attempt in attempts]
        percentages = [
            ((float(sum(float(answer.awarded_marks) for answer in attempt.answers)) / attempt.target_question_count) * 100)
            if attempt.target_question_count
            else 0.0
            for attempt in attempts
        ]
        return ExamSummaryView(
            exam_id=str(exam.id),
            exam_code=exam.code,
            exam_title=exam.title,
            total_attempts=len(attempts),
            completed_attempts=len(completed_attempts),
            average_score=(sum(scores) / len(scores)) if scores else 0.0,
            average_percentage=(sum(percentages) / len(percentages)) if percentages else 0.0,
            highest_score=max(scores) if scores else 0.0,
            lowest_score=min(scores) if scores else 0.0,
        )
