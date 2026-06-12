from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.application.question_bank.dto import CreateQuestionInput, QuestionSearchFilters, UpdateQuestionInput
from app.infrastructure.persistence.models import Category, Exam, Question, QuestionOption, QuestionTag, Section


class QuestionBankRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_question(self, data: CreateQuestionInput) -> Question:
        exam_id = uuid.UUID(data.exam_id)
        section_id = uuid.UUID(data.section_id)
        self._require_exam(exam_id)
        section = self._require_section(section_id, exam_id)
        category = self._get_or_create_category(section.id, data.category_name) if data.category_name else None
        tags = self._get_or_create_tags(data.tags)

        question = Question(
            exam_id=exam_id,
            section_id=section.id,
            category_id=category.id if category else None,
            attempt_id=uuid.UUID(data.attempt_id) if data.attempt_id else None,
            external_ref=data.external_ref or f"manual-{uuid.uuid4().hex}",
            stem_text=data.stem_text.strip(),
            explanation_text=data.explanation_text.strip() if data.explanation_text else None,
            difficulty_level=data.difficulty_level,
            marks=data.marks,
            is_active=data.is_active,
        )
        question.options = [
            QuestionOption(
                option_key=option.key.strip().upper(),
                option_text=option.text.strip(),
                is_correct=option.is_correct,
                display_order=index,
            )
            for index, option in enumerate(data.options, start=1)
        ]
        question.tags = tags

        self._session.add(question)
        self._session.commit()
        return self.get_question(str(question.id))

    def update_question(self, question_id: str, data: UpdateQuestionInput) -> Question | None:
        question = self.get_question(question_id)
        if question is None:
            return None

        if data.stem_text is not None:
            question.stem_text = data.stem_text.strip()
        if data.explanation_text is not None:
            question.explanation_text = data.explanation_text.strip() or None
        if data.difficulty_level is not None:
            question.difficulty_level = data.difficulty_level
        if data.marks is not None:
            question.marks = data.marks
        if data.is_active is not None:
            question.is_active = data.is_active
        if data.category_name is not None:
            category = self._get_or_create_category(question.section_id, data.category_name) if data.category_name else None
            question.category = category
        if data.tags is not None:
            question.tags = self._get_or_create_tags(data.tags)
        if data.options is not None:
            question.options.clear()
            self._session.flush()
            question.options.extend(
                QuestionOption(
                    option_key=option.key.strip().upper(),
                    option_text=option.text.strip(),
                    is_correct=option.is_correct,
                    display_order=index,
                )
                for index, option in enumerate(data.options, start=1)
            )

        self._session.add(question)
        self._session.commit()
        return self.get_question(question_id)

    def delete_question(self, question_id: str) -> bool:
        question = self._session.get(Question, uuid.UUID(question_id))
        if question is None:
            return False
        self._session.delete(question)
        self._session.commit()
        return True

    def get_question(self, question_id: str) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.id == uuid.UUID(question_id))
            .options(
                joinedload(Question.category),
                joinedload(Question.options),
                joinedload(Question.tags),
            )
        )
        return self._session.scalars(stmt).unique().one_or_none()

    def search_questions(self, filters: QuestionSearchFilters) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.exam_id == uuid.UUID(filters.exam_id))
            .options(
                joinedload(Question.category),
                joinedload(Question.options),
                joinedload(Question.tags),
            )
        )

        if not filters.include_inactive:
            stmt = stmt.where(Question.is_active.is_(True))
        if filters.query:
            pattern = f"%{filters.query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Question.stem_text).like(pattern),
                    func.lower(Question.explanation_text).like(pattern),
                )
            )
        if filters.category_name:
            stmt = stmt.join(Question.category).where(Category.name == filters.category_name.strip())
        if filters.difficulty_level is not None:
            stmt = stmt.where(Question.difficulty_level == filters.difficulty_level)
        if filters.tags:
            normalized_tags = [tag.strip() for tag in filters.tags if tag.strip()]
            if normalized_tags:
                stmt = (
                    stmt.join(Question.tags)
                    .where(QuestionTag.name.in_(normalized_tags))
                    .distinct()
                )

        stmt = stmt.order_by(Question.created_at.desc())
        return list(self._session.scalars(stmt).unique().all())

    def _require_exam(self, exam_id: uuid.UUID) -> Exam:
        exam = self._session.get(Exam, exam_id)
        if exam is None:
            raise ValueError("Exam not found.")
        return exam

    def _require_section(self, section_id: uuid.UUID, exam_id: uuid.UUID) -> Section:
        stmt = select(Section).where(Section.id == section_id, Section.exam_id == exam_id)
        section = self._session.scalar(stmt)
        if section is None:
            raise ValueError("Section not found for exam.")
        return section

    def _get_or_create_category(self, section_id: uuid.UUID, name: str | None) -> Category | None:
        if name is None or not name.strip():
            return None
        normalized_name = name.strip()
        stmt = select(Category).where(Category.section_id == section_id, Category.name == normalized_name)
        category = self._session.scalar(stmt)
        if category is not None:
            return category

        category = Category(section_id=section_id, name=normalized_name)
        self._session.add(category)
        self._session.flush()
        return category

    def _get_or_create_tags(self, tag_names: list[str]) -> list[QuestionTag]:
        normalized_names = sorted({name.strip() for name in tag_names if name.strip()})
        if not normalized_names:
            return []

        stmt = select(QuestionTag).where(QuestionTag.name.in_(normalized_names))
        existing_tags = {tag.name: tag for tag in self._session.scalars(stmt).all()}
        resolved_tags: list[QuestionTag] = []

        for name in normalized_names:
            tag = existing_tags.get(name)
            if tag is None:
                tag = QuestionTag(name=name)
                self._session.add(tag)
                self._session.flush()
            resolved_tags.append(tag)

        return resolved_tags
