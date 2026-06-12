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
            min_questions=20,
            max_questions=20,
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

    # Seed 10 easy questions
    for i in range(10):
        question_service.add_question(
            CreateQuestionInput(
                exam_id=exam.exam_id,
                section_id=section_id,
                stem_text=f"Easy grammar question {i}",
                options=[
                    QuestionOptionInput("A", "Correct", True),
                    QuestionOptionInput("B", "Wrong"),
                ],
                category_name="Grammar",
                difficulty_level=1,
            )
        )

    # Seed 10 medium questions
    for i in range(10):
        question_service.add_question(
            CreateQuestionInput(
                exam_id=exam.exam_id,
                section_id=section_id,
                stem_text=f"Medium vocabulary question {i}",
                options=[
                    QuestionOptionInput("A", "Wrong"),
                    QuestionOptionInput("B", "Correct", True),
                ],
                category_name="Vocabulary",
                difficulty_level=2,
            )
        )

    # Seed 10 hard questions
    for i in range(10):
        question_service.add_question(
            CreateQuestionInput(
                exam_id=exam.exam_id,
                section_id=section_id,
                stem_text=f"Hard reading question {i}",
                options=[
                    QuestionOptionInput("A", "Correct", True),
                    QuestionOptionInput("B", "Wrong"),
                ],
                category_name="Reading",
                difficulty_level=3,
            )
        )

    start = adaptive_service.start_exam(
        StartAdaptiveExamInput(student_id=student.student_id, exam_id=exam.exam_id, question_count=20, generate_ai_questions=False)
    )
    assert start.total_questions == 20
    assert start.next_question is not None
    assert start.next_question.difficulty_level == 2

    progress = start
    for step in range(20):
        assert progress.next_question is not None
        current_q = progress.next_question

        # Step 0: Answer medium question correctly (correct is B)
        if step == 0:
            assert current_q.difficulty_level == 2
            selected_option_id = next(opt["option_id"] for opt in current_q.options if opt["key"] == "B")
        # Step 1: Answer hard question incorrectly (correct is A, so choose B)
        elif step == 1:
            assert current_q.difficulty_level == 3
            selected_option_id = next(opt["option_id"] for opt in current_q.options if opt["key"] == "B")
        # Remaining steps: answer correctly
        else:
            if current_q.difficulty_level == 1:
                correct_key = "A"
            elif current_q.difficulty_level == 2:
                correct_key = "B"
            else:
                correct_key = "A"
            selected_option_id = next(opt["option_id"] for opt in current_q.options if opt["key"] == correct_key)

        progress = adaptive_service.submit_answer(
            SubmitAnswerInput(
                attempt_id=start.attempt_id,
                question_id=current_q.question_id,
                selected_option_id=selected_option_id,
            )
        )

    assert progress.is_complete is True
    assert progress.next_question is None
    assert progress.answered_questions == 20

