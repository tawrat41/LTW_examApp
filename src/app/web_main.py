from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, List, Optional, Dict
from pydantic import BaseModel

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.infrastructure.persistence.session import create_all, create_sqlite_engine, create_session_factory
from app.bootstrap.desktop import _seed_default_admin
from app.bootstrap.student_desktop import _seed_default_student

from app.bootstrap.admin_services import (
    build_admin_query_service,
    build_exam_management_service,
    build_question_bank_service,
    build_reporting_service,
    build_student_management_service,
)
from app.bootstrap.student_services import build_student_exam_portal_service
from app.bootstrap.auth import build_authentication_controller
from app.infrastructure.auth import InMemorySessionStore
from app.application.auth import LoginRequest, AuthenticationError
from app.application.exams.dto import CreateExamInput, UpdateExamInput, ExamSearchFilters
from app.application.students.dto import CreateStudentInput, UpdateStudentInput, StudentSearchFilters
from app.application.question_bank.dto import (
    CreateQuestionInput,
    UpdateQuestionInput,
    QuestionSearchFilters,
    QuestionOptionInput,
    BulkImportRequest,
)
from app.application.exams import ExamManagementError
from app.application.students import StudentManagementError
from app.application.question_bank import QuestionBankError
from app.application.student_exam import StudentExamPortalError
from app.application.adaptive import AdaptiveExamError

app = FastAPI(title="Lead The Way - AI English Assessment Platform")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.error(f"Validation error for {request.method} {request.url.path}: {exc.errors()}")
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request, exc)

DATABASE_PATH = Path("data") / "adaptive_exam.db"
engine = create_sqlite_engine(DATABASE_PATH)
try:
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE questions ADD COLUMN attempt_id VARCHAR(36) REFERENCES attempts(id) ON DELETE CASCADE"))
except Exception:
    pass
create_all(engine)


def seed_cefr_exams(session: Session) -> None:
    from app.infrastructure.persistence.models import User, Exam, Section, Question
    from app.application.importing.ai_generator import AIGeneratorService
    from sqlalchemy import select, func
    
    # Ensure default admin and student
    _seed_default_admin(session)
    _seed_default_student(session)
    
    admin_user = session.scalar(select(User).limit(1))
    if not admin_user:
        return
        
    levels = [
        ("STARTER", "Starter (A1-)", "Basic introduction, alphabets, simple pronouns and matching tasks.", 20, 20, 0.0),
        ("ELEMENTARY", "Elementary (A1)", "Simple present/past tense verbs, daily vocabulary, and sentence unscrambles.", 20, 20, 50.0),
        ("PRE_INTERMEDIATE", "Pre-Intermediate (A2)", "Present perfect tense, comparatives, prepositions, and short reading passages.", 20, 20, 50.0),
        ("INTERMEDIATE", "Intermediate (B1)", "Modals, passive voice, cloze exercises, and inferential reading tasks.", 20, 20, 60.0),
        ("UPPER_INTERMEDIATE", "Upper-Intermediate (B2)", "Future perfect, phrasal verbs, idioms, and long detail passages.", 20, 20, 60.0),
        ("ADVANCED", "Advanced (C1/C2)", "Inversion, nuances, tone recognition, and academic reading topics.", 20, 20, 70.0),
    ]
    
    ai_gen = AIGeneratorService(session)
    
    for code, title, desc, min_q, max_q, pass_s in levels:
        existing = session.scalar(select(Exam).where(Exam.code == code))
        if existing:
            # Sync min/max questions to 20
            if existing.settings:
                existing.settings.min_questions = 20
                existing.settings.max_questions = 20
                session.commit()
            # Seed default questions if database has less than 40 questions
            q_count = session.scalar(select(func.count(Question.id)).where(Question.exam_id == existing.id, Question.attempt_id.is_(None)))
            if q_count < 40:
                section = existing.sections[0]
                ai_gen.generate_questions(str(existing.id), str(section.id), title.split(" ")[0], count=40 - q_count)
            continue
            
        # Create new CEFR level exam
        from app.infrastructure.exams.repositories import ExamRepository
        repo = ExamRepository(session)
        created = repo.create_exam(CreateExamInput(
            code=code,
            title=title,
            created_by_user_id=str(admin_user.id),
            description=desc,
            subject="English",
            time_limit_minutes=20 if "Starter" in title or "Elementary" in title else 45,
            min_questions=min_q,
            max_questions=max_q,
            passing_score=pass_s
        ))
        
        # Activate exam
        created.status = "active"
        session.commit()
        
        # Ingest 40 initial validated questions
        section = created.sections[0]
        ai_gen.generate_questions(str(created.id), str(section.id), title.split(" ")[0], count=40)


# Run Seeding
db_session = create_session_factory(engine)()
seed_cefr_exams(db_session)
db_session.close()

SessionLocal = create_session_factory(engine)
shared_session_store = InMemorySessionStore(ttl_minutes=480)

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Helper to calculate radar chart sub-skills
def get_skills_breakdown(session: Session, attempt_id: str) -> Dict[str, float]:
    from app.infrastructure.persistence.models import Attempt
    attempt = session.get(Attempt, uuid.UUID(attempt_id))
    if not attempt:
        return {}
    
    breakdown = {"Grammar": {"total": 0, "correct": 0}, "Vocabulary": {"total": 0, "correct": 0}, "Reading": {"total": 0, "correct": 0}}
    
    for ans in attempt.answers:
        cat = ans.question.category.name if ans.question.category else "Grammar"
        if cat not in breakdown:
            breakdown[cat] = {"total": 0, "correct": 0}
        breakdown[cat]["total"] += 1
        if ans.is_correct:
            breakdown[cat]["correct"] += 1
            
    result = {}
    for cat, stats in breakdown.items():
        if stats["total"] > 0:
            result[cat] = round((stats["correct"] / stats["total"]) * 100, 1)
        else:
            result[cat] = 0.0
    return result


# Pydantic schemas for requests
class LoginBody(BaseModel):
    username: str
    password: str
    role: str  # "admin" or "student"

class CreateExamBody(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    subject: str = "English"
    time_limit_minutes: int = 30
    min_questions: int = 20
    max_questions: int = 20
    passing_score: float = 0.0

class UpdateExamBody(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    min_questions: Optional[int] = None
    max_questions: Optional[int] = None
    passing_score: Optional[float] = None

class CreateStudentBody(BaseModel):
    student_code: str
    full_name: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class UpdateStudentBody(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class QuestionOptionBody(BaseModel):
    key: str
    text: str
    is_correct: bool = False

class CreateQuestionBody(BaseModel):
    exam_id: str
    section_id: str
    stem_text: str
    options: List[QuestionOptionBody]
    category_name: Optional[str] = None
    difficulty_level: int = 1
    explanation_text: Optional[str] = None
    tags: List[str] = []
    marks: float = 1.0
    is_active: bool = True

class UpdateQuestionBody(BaseModel):
    stem_text: Optional[str] = None
    options: Optional[List[QuestionOptionBody]] = None
    category_name: Optional[str] = None
    difficulty_level: Optional[int] = None
    explanation_text: Optional[str] = None
    tags: Optional[List[str]] = None
    marks: Optional[float] = None
    is_active: Optional[bool] = None

class SubmitAnswerBody(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None

class AIGenerateBody(BaseModel):
    exam_id: str
    section_id: str
    level_name: str
    count: int = 5

class StartExamBody(BaseModel):
    student_name: str


# Auth Dependency
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    session_id = authorization.split(" ")[1]
    auth_session = shared_session_store.get(session_id)
    if not auth_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )
    return auth_session.principal

def require_admin(principal=Depends(get_current_user)):
    if principal.principal_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privilege required",
        )
    return principal

def require_student(principal=Depends(get_current_user)):
    if principal.principal_type != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student privilege required",
        )
    return principal


# AUTH ENDPOINTS
@app.post("/api/auth/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    auth_controller = build_authentication_controller(db, session_store=shared_session_store)
    request_dto = LoginRequest(username=body.username, password=body.password)
    try:
        if body.role == "admin":
            result = auth_controller.handle_admin_login(request_dto)
        else:
            result = auth_controller.handle_student_login(request_dto)
        return {
            "session_id": str(result.session_id),
            "principal_id": str(result.principal_id),
            "principal_type": str(result.principal_type),
            "username": result.username,
            "display_name": result.display_name,
            "expires_at_iso": result.expires_at_iso,
        }
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

@app.post("/api/auth/logout")
def logout(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization header")
    session_id = authorization.split(" ")[1]
    shared_session_store.revoke(session_id)
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
def get_me(principal=Depends(get_current_user)):
    return {
        "id": str(principal.id),
        "role": str(principal.principal_type),
        "username": principal.username,
        "display_name": principal.display_name,
    }


# ADMIN ENDPOINTS
@app.get("/api/admin/dashboard")
def get_admin_dashboard(db: Session = Depends(get_db), admin=Depends(require_admin)):
    queries = build_admin_query_service(db)
    stats = queries.get_dashboard_stats()
    return {
        "exams_count": stats.exams_count,
        "students_count": stats.students_count,
        "questions_count": stats.questions_count,
        "active_students_count": stats.active_students_count,
    }

@app.get("/api/admin/exams/lookup")
def get_exam_lookup(db: Session = Depends(get_db), admin=Depends(require_admin)):
    queries = build_admin_query_service(db)
    return [{"id": item.id, "label": item.label} for item in queries.list_exam_options()]

@app.get("/api/admin/exams/{exam_id}/sections/lookup")
def get_section_lookup(exam_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    queries = build_admin_query_service(db)
    return [{"id": item.id, "label": item.label} for item in queries.list_section_options(exam_id)]

# EXAMS CRUD
@app.get("/api/admin/exams")
def search_exams(query: Optional[str] = None, status_filter: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_exam_management_service(db)
    filters = ExamSearchFilters(query=query, status=status_filter)
    exams = service.search_exams(filters)
    return exams

@app.post("/api/admin/exams")
def create_exam(body: CreateExamBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_exam_management_service(db)
    input_dto = CreateExamInput(
        code=body.code,
        title=body.title,
        created_by_user_id=str(admin.id),
        description=body.description,
        subject=body.subject,
        time_limit_minutes=body.time_limit_minutes,
        min_questions=body.min_questions,
        max_questions=body.max_questions,
        passing_score=body.passing_score,
    )
    try:
        return service.add_exam(input_dto)
    except ExamManagementError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@app.put("/api/admin/exams/{exam_id}")
def update_exam(exam_id: str, body: UpdateExamBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_exam_management_service(db)
    input_dto = UpdateExamInput(
        title=body.title,
        description=body.description,
        subject=body.subject,
        status=body.status,
        time_limit_minutes=body.time_limit_minutes,
        min_questions=body.min_questions,
        max_questions=body.max_questions,
        passing_score=body.passing_score,
    )
    try:
        return service.edit_exam(exam_id, input_dto)
    except ExamManagementError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@app.delete("/api/admin/exams/{exam_id}")
def delete_exam(exam_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_exam_management_service(db)
    try:
        service.delete_exam(exam_id)
        return {"message": "Exam deleted successfully"}
    except ExamManagementError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# STUDENTS CRUD
@app.get("/api/admin/students")
def search_students(query: Optional[str] = None, is_active: Optional[bool] = None, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_student_management_service(db)
    filters = StudentSearchFilters(query=query, is_active=is_active)
    students = service.search_students(filters)
    return students

@app.post("/api/admin/students")
def create_student(body: CreateStudentBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_student_management_service(db)
    input_dto = CreateStudentInput(
        student_code=body.student_code,
        full_name=body.full_name,
        password=body.password,
        email=body.email,
        phone=body.phone,
        is_active=body.is_active,
    )
    try:
        return service.add_student(input_dto)
    except StudentManagementError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@app.put("/api/admin/students/{student_id}")
def update_student(student_id: str, body: UpdateStudentBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_student_management_service(db)
    input_dto = UpdateStudentInput(
        full_name=body.full_name,
        password=body.password,
        email=body.email,
        phone=body.phone,
        is_active=body.is_active,
    )
    try:
        return service.edit_student(student_id, input_dto)
    except StudentManagementError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@app.delete("/api/admin/students/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_student_management_service(db)
    try:
        service.delete_student(student_id)
        return {"message": "Student deleted successfully"}
    except StudentManagementError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# QUESTION BANK CRUD
@app.get("/api/admin/questions")
def search_questions(
    exam_id: str,
    query: Optional[str] = None,
    category_name: Optional[str] = None,
    difficulty_level: Optional[int] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    service = build_question_bank_service(db)
    filters = QuestionSearchFilters(
        exam_id=exam_id,
        query=query,
        category_name=category_name,
        difficulty_level=difficulty_level,
        include_inactive=include_inactive,
    )
    questions = service.search_questions(filters)
    return questions

@app.post("/api/admin/questions")
def create_question(body: CreateQuestionBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_question_bank_service(db)
    input_dto = CreateQuestionInput(
        exam_id=body.exam_id,
        section_id=body.section_id,
        stem_text=body.stem_text,
        options=[
            QuestionOptionInput(key=opt.key, text=opt.text, is_correct=opt.is_correct)
            for opt in body.options
        ],
        category_name=body.category_name,
        difficulty_level=body.difficulty_level,
        explanation_text=body.explanation_text,
        tags=body.tags,
        marks=body.marks,
        is_active=body.is_active,
    )
    try:
        return service.add_question(input_dto)
    except QuestionBankError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@app.put("/api/admin/questions/{question_id}")
def update_question(question_id: str, body: UpdateQuestionBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_question_bank_service(db)
    options_dto = None
    if body.options is not None:
        options_dto = [
            QuestionOptionInput(key=opt.key, text=opt.text, is_correct=opt.is_correct)
            for opt in body.options
        ]
    input_dto = UpdateQuestionInput(
        stem_text=body.stem_text,
        options=options_dto,
        category_name=body.category_name,
        difficulty_level=body.difficulty_level,
        explanation_text=body.explanation_text,
        tags=body.tags,
        marks=body.marks,
        is_active=body.is_active,
    )
    try:
        return service.edit_question(question_id, input_dto)
    except QuestionBankError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@app.delete("/api/admin/questions/{question_id}")
def delete_question(question_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_question_bank_service(db)
    try:
        service.delete_question(question_id)
        return {"message": "Question deleted successfully"}
    except QuestionBankError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# AI GENERATION TRIGGER ENDPOINT
@app.post("/api/admin/ai/generate")
def trigger_ai_generation(body: AIGenerateBody, db: Session = Depends(get_db), admin=Depends(require_admin)):
    from app.application.importing.ai_generator import AIGeneratorService
    generator = AIGeneratorService(db)
    try:
        res = generator.generate_questions(
            exam_id=body.exam_id,
            section_id=body.section_id,
            level_name=body.level_name,
            count=body.count
        )
        return res
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# QUESTION DOCX IMPORT
@app.post("/api/admin/questions/import/preview")
def preview_import(file: UploadFile = File(...), db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_question_bank_service(db)
    suffix = Path(file.filename).suffix
    if suffix.lower() != ".docx":
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        finally:
            tmp.close()

    try:
        report = service._import_service.import_from_docx(tmp_path)
        issues_list = []
        for issue in report.issues:
            issues_list.append({
                "sequence_number": issue.sequence_number,
                "severity": str(issue.severity.value),
                "message": issue.message,
                "raw_block": issue.raw_block,
            })
        
        parsed_list = []
        for pq in report.parsed_questions:
            parsed_list.append({
                "sequence_number": pq.sequence_number,
                "question_text": pq.question_text,
                "options": pq.options,
                "correct_answer": pq.correct_answer,
                "difficulty": pq.difficulty,
                "explanation": pq.explanation,
                "category": pq.category,
            })

        duplicates_list = []
        for dup in report.duplicates:
            duplicates_list.append({
                "original_sequence_number": dup.original_sequence_number,
                "duplicate_sequence_number": dup.duplicate_sequence_number,
                "question_text": dup.question_text,
            })

        return {
            "parsed_questions": parsed_list,
            "issues": issues_list,
            "duplicates": duplicates_list,
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/api/admin/questions/import/commit")
def commit_import(
    exam_id: str = Form(...),
    section_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    service = build_question_bank_service(db)
    suffix = Path(file.filename).suffix
    if suffix.lower() != ".docx":
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        finally:
            tmp.close()

    try:
        request_dto = BulkImportRequest(exam_id=exam_id, section_id=section_id)
        result = service.bulk_import_from_docx(tmp_path, request_dto)
        
        issues_list = []
        for issue in result.issues:
            issues_list.append({
                "sequence_number": issue.sequence_number,
                "severity": str(issue.severity.value),
                "message": issue.message,
                "raw_block": issue.raw_block,
            })
            
        return {
            "imported_count": len(result.imported_questions),
            "issues": issues_list,
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# REPORTING ENDPOINTS
@app.get("/api/admin/reports/student-results")
def get_student_results(db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_reporting_service(db)
    results = service.list_student_results()
    return [{
        "attempt_id": r.attempt_id,
        "student_id": r.student_id,
        "student_code": r.student_code,
        "student_name": r.student_name,
        "exam_id": r.exam_id,
        "exam_code": r.exam_code,
        "exam_title": r.exam_title,
        "completed_at_iso": r.completed_at_iso,
        "total_questions": r.total_questions,
        "answered_questions": r.answered_questions,
        "correct_answers": r.correct_answers,
        "wrong_answers": r.wrong_answers,
        "unanswered_questions": r.unanswered_questions,
        "score": float(r.score),
        "percentage": float(r.percentage),
        "status": r.status,
    } for r in results]

@app.get("/api/admin/reports/exam-summaries")
def get_exam_summaries(db: Session = Depends(get_db), admin=Depends(require_admin)):
    service = build_reporting_service(db)
    summaries = service.list_exam_summaries()
    return [{
        "exam_id": s.exam_id,
        "exam_code": s.exam_code,
        "exam_title": s.exam_title,
        "total_attempts": s.total_attempts,
        "completed_attempts": s.completed_attempts,
        "average_score": float(s.average_score),
        "average_percentage": float(s.average_percentage),
        "highest_score": float(s.highest_score),
        "lowest_score": float(s.lowest_score),
    } for s in summaries]


# STUDENT PORTAL ENDPOINTS
@app.get("/api/student/exams")
def list_student_exams(db: Session = Depends(get_db)):
    portal = build_student_exam_portal_service(db)
    exams = portal.list_available_exams()
    return [{
        "exam_id": e.exam_id,
        "code": e.code,
        "title": e.title,
        "description": e.description,
        "subject": e.subject,
        "time_limit_minutes": e.time_limit_minutes,
        "question_count": e.question_count,
        "allow_previous": e.allow_previous,
    } for e in exams]

@app.get("/api/student/exams/{exam_id}/instructions")
def get_student_exam_instructions(exam_id: str, db: Session = Depends(get_db)):
    portal = build_student_exam_portal_service(db)
    try:
        instructions = portal.get_exam_instructions(exam_id)
        return {
            "exam_id": instructions.exam_id,
            "code": instructions.code,
            "title": instructions.title,
            "description": instructions.description,
            "subject": instructions.subject,
            "time_limit_minutes": instructions.time_limit_minutes,
            "question_count": instructions.question_count,
            "allow_previous": instructions.allow_previous,
            "instructions": instructions.instructions,
        }
    except StudentExamPortalError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.post("/api/student/exams/{exam_id}/start")
def start_student_exam(exam_id: str, body: StartExamBody, db: Session = Depends(get_db)):
    from app.infrastructure.persistence.models import Student
    from sqlalchemy import select
    
    normalized_name = body.student_name.strip()
    if not normalized_name:
        raise HTTPException(status_code=400, detail="Candidate name cannot be empty")
        
    student = db.scalar(
        select(Student)
        .where(Student.full_name == normalized_name)
        .limit(1)
    )
    
    if not student:
        import random
        import string
        from app.infrastructure.auth.passwords import PasswordHasher
        hasher = PasswordHasher()
        clean_name_slug = "".join(c for c in normalized_name.lower() if c.isalnum() or c in (" ", "_")).replace(" ", "_")
        random_suffix = "".join(random.choices(string.digits, k=5))
        student_code = f"guest_{clean_name_slug}_{random_suffix}"
        pwd_hash = hasher.hash_password("password")
        
        student = Student(
            id=uuid.uuid4(),
            student_code=student_code,
            full_name=normalized_name,
            password_hash=pwd_hash,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        
    portal = build_student_exam_portal_service(db)
    try:
        session_view = portal.start_exam(student_id=str(student.id), exam_id=exam_id)
        
        current_q = None
        if session_view.current_question:
            current_q = {
                "question_id": session_view.current_question.question_id,
                "stem_text": session_view.current_question.stem_text,
                "category_name": session_view.current_question.category_name,
                "difficulty_level": session_view.current_question.difficulty_level,
                "sequence_number": session_view.current_question.sequence_number,
                "total_questions": session_view.current_question.total_questions,
                "options": session_view.current_question.options,
            }
            
        return {
            "attempt_id": str(session_view.attempt_id),
            "is_complete": session_view.is_complete,
            "answered_questions": session_view.answered_questions,
            "remaining_questions": session_view.remaining_questions,
            "current_question": current_q,
            "student_id": str(student.id),
            "student_name": student.full_name,
            "student_code": student.student_code
        }
    except (StudentExamPortalError, AdaptiveExamError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/student/attempts/history")
def get_attempts_history(db: Session = Depends(get_db)):
    service = build_reporting_service(db)
    results = service.list_student_results()
    return [{
        "attempt_id": r.attempt_id,
        "student_code": r.student_code,
        "student_name": r.student_name,
        "exam_title": r.exam_title,
        "completed_at_iso": r.completed_at_iso,
        "total_questions": r.total_questions,
        "answered_questions": r.answered_questions,
        "correct_answers": r.correct_answers,
        "wrong_answers": r.wrong_answers,
        "score": float(r.score),
        "percentage": float(r.percentage),
        "status": r.status,
    } for r in results]

@app.get("/api/student/attempts/{attempt_id}")
def get_student_attempt(attempt_id: str, db: Session = Depends(get_db)):
    portal = build_student_exam_portal_service(db)
    try:
        progress = portal._adaptive_service.get_progress(attempt_id)
        current_q = None
        if progress.next_question:
            current_q = {
                "question_id": progress.next_question.question_id,
                "stem_text": progress.next_question.stem_text,
                "category_name": progress.next_question.category_name,
                "difficulty_level": progress.next_question.difficulty_level,
                "sequence_number": progress.next_question.sequence_number,
                "total_questions": progress.next_question.total_questions,
                "options": progress.next_question.options,
            }
        return {
            "attempt_id": attempt_id,
            "is_complete": progress.is_complete,
            "answered_questions": progress.answered_questions,
            "remaining_questions": progress.remaining_questions,
            "current_question": current_q,
        }
    except (StudentExamPortalError, AdaptiveExamError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/student/attempts/{attempt_id}/submit-answer")
def submit_student_answer(attempt_id: str, body: SubmitAnswerBody, db: Session = Depends(get_db)):
    portal = build_student_exam_portal_service(db)
    try:
        progress = portal.submit_answer(
            attempt_id=attempt_id,
            question_id=body.question_id,
            selected_option_id=body.selected_option_id,
        )
        
        current_q = None
        if progress.next_question:
            current_q = {
                "question_id": progress.next_question.question_id,
                "stem_text": progress.next_question.stem_text,
                "category_name": progress.next_question.category_name,
                "difficulty_level": progress.next_question.difficulty_level,
                "sequence_number": progress.next_question.sequence_number,
                "total_questions": progress.next_question.total_questions,
                "options": progress.next_question.options,
            }
            
        return {
            "attempt_id": attempt_id,
            "is_complete": progress.is_complete,
            "answered_questions": progress.answered_questions,
            "remaining_questions": progress.remaining_questions,
            "current_question": current_q,
        }
    except (StudentExamPortalError, AdaptiveExamError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/student/attempts/{attempt_id}/finish")
def finish_student_exam(attempt_id: str, db: Session = Depends(get_db)):
    portal = build_student_exam_portal_service(db)
    try:
        result = portal.finalize_attempt(attempt_id)
        skills = get_skills_breakdown(db, attempt_id)
        return {
            "attempt_id": result.attempt_id,
            "exam_title": result.exam_title,
            "total_questions": result.total_questions,
            "answered_questions": result.answered_questions,
            "correct_answers": result.correct_answers,
            "wrong_answers": result.wrong_answers,
            "score": float(result.score),
            "percentage": float(result.percentage),
            "skills_breakdown": skills
        }
    except (StudentExamPortalError, AdaptiveExamError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/student/attempts/{attempt_id}/result")
def get_student_exam_result(attempt_id: str, db: Session = Depends(get_db)):
    portal = build_student_exam_portal_service(db)
    try:
        result = portal.get_result(attempt_id)
        skills = get_skills_breakdown(db, attempt_id)
        return {
            "attempt_id": result.attempt_id,
            "exam_title": result.exam_title,
            "total_questions": result.total_questions,
            "answered_questions": result.answered_questions,
            "correct_answers": result.correct_answers,
            "wrong_answers": result.wrong_answers,
            "score": float(result.score),
            "percentage": float(result.percentage),
            "skills_breakdown": skills
        }
    except (StudentExamPortalError, AdaptiveExamError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/student/lookup")
def get_student_lookup(db: Session = Depends(get_db)):
    from app.infrastructure.persistence.models import Student
    from sqlalchemy import select
    students = db.scalars(select(Student).where(Student.is_active.is_(True)).order_by(Student.full_name.asc())).all()
    return [{"student_id": str(s.id), "full_name": s.full_name, "student_code": s.student_code} for s in students]

# Serve static files in production if frontend/dist exists
from fastapi.staticfiles import StaticFiles
frontend_dist_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist_path), html=True), name="frontend")

# attempts/history route moved above {attempt_id} to avoid route shadowing
