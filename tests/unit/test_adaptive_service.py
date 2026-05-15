from __future__ import annotations

from pathlib import Path

from app.application.adaptive import AdaptiveExamService, StartAdaptiveExamInput, SubmitAnswerInput
from app.application.exams import CreateExamInput, ExamManagementService
from app.application.question_bank import CreateQuestionInput, QuestionBankService, QuestionOptionInput
from app.application.students import CreateStudentInput, StudentManagementService
from app.infrastructure.adaptive import AdaptiveExamRepository
from app.infrastructure.auth.passwords import PasswordHasher
from app.infrastructure.exams import ExamRepository
from app.infrastructure.persistence import Section, User, UserRole, create_all, create_session_factory, create_sqlite_engine
from app.infrastructure.question_bank import QuestionBankRepository
from app.infrastructure.students import StudentRepository


def _build_services(tmp_path: Path):
    engine = create_sqlite_engine(tmp_path / "adaptive.db")
    create_all(engine)
    session = create_session_factory(engine)()

    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password_hash=PasswordHasher().hash_password("secret123"),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()

    exam_service = ExamManagementService(ExamRepository(session))
    student_service = StudentManagementService(StudentRepository(session))
    question_service = QuestionBankService(QuestionBankRepository(session))
    adaptive_service = AdaptiveExamService(AdaptiveExamRepository(session))

    exam = exam_service.add_exam(
        CreateExamInput(
            code="ENG-ADAPT",
            title="Adaptive English",
            created_by_user_id=str(admin.id),
            min_questions=3,
            max_questions=3,
        )
    )
    student = student_service.add_student(
        CreateStudentInput(
            student_code="STD-100",
            full_name="Student One",
            password="password1",
        )
    )

    return session, exam, student, question_service, adaptive_service


def test_adaptive_exam_service_runs_deterministic_flow(tmp_path: Path) -> None:
    session, exam, student, question_service, adaptive_service = _build_services(tmp_path)
    section = session.query(Section).filter_by(exam_id=exam.exam_id).one()
    section_id = str(section.id)

    q_easy = question_service.add_question(
        CreateQuestionInput(
            exam_id=exam.exam_id,
            section_id=section_id,
            stem_text="Easy grammar question",
            options=[
                QuestionOptionInput("A", "Correct", True),
                QuestionOptionInput("B", "Wrong"),
            ],
            category_name="Grammar",
            difficulty_level=1,
        )
    )
    q_medium = question_service.add_question(
        CreateQuestionInput(
            exam_id=exam.exam_id,
            section_id=section_id,
            stem_text="Medium vocabulary question",
            options=[
                QuestionOptionInput("A", "Wrong"),
                QuestionOptionInput("B", "Correct", True),
            ],
            category_name="Vocabulary",
            difficulty_level=2,
        )
    )
    q_hard = question_service.add_question(
        CreateQuestionInput(
            exam_id=exam.exam_id,
            section_id=section_id,
            stem_text="Hard reading question",
            options=[
                QuestionOptionInput("A", "Correct", True),
                QuestionOptionInput("B", "Wrong"),
            ],
            category_name="Reading",
            difficulty_level=3,
        )
    )

    start = adaptive_service.start_exam(
        StartAdaptiveExamInput(student_id=student.student_id, exam_id=exam.exam_id, question_count=3)
    )
    assert start.total_questions == 3
    assert start.next_question is not None
    assert start.next_question.question_id == q_medium.question_id
    assert start.next_question.difficulty_level == 2

    medium_correct_option = next(
        option["option_id"] for option in start.next_question.options if option["key"] == "B"
    )
    after_first = adaptive_service.submit_answer(
        SubmitAnswerInput(
            attempt_id=start.attempt_id,
            question_id=start.next_question.question_id,
            selected_option_id=medium_correct_option,
        )
    )
    assert after_first.next_question is not None
    assert after_first.next_question.question_id == q_hard.question_id
    assert after_first.next_question.difficulty_level == 3

    hard_wrong_option = next(
        option["option_id"] for option in after_first.next_question.options if option["key"] == "B"
    )
    after_second = adaptive_service.submit_answer(
        SubmitAnswerInput(
            attempt_id=start.attempt_id,
            question_id=after_first.next_question.question_id,
            selected_option_id=hard_wrong_option,
        )
    )
    assert after_second.next_question is not None
    assert after_second.next_question.question_id == q_easy.question_id
    assert after_second.next_question.difficulty_level == 1

    easy_correct_option = next(
        option["option_id"] for option in after_second.next_question.options if option["key"] == "A"
    )
    final_progress = adaptive_service.submit_answer(
        SubmitAnswerInput(
            attempt_id=start.attempt_id,
            question_id=after_second.next_question.question_id,
            selected_option_id=easy_correct_option,
        )
    )
    assert final_progress.is_complete is True
    assert final_progress.next_question is None
    assert final_progress.answered_questions == 3
