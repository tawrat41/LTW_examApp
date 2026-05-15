from __future__ import annotations

from app.domain.adaptive import (
    AdaptiveAnswerRecord,
    AdaptiveExamConfig,
    AdaptiveExamEngine,
    AdaptiveExamState,
    AdaptiveQuestionCandidate,
)


def _candidate(question_id: str, difficulty: int, category: str, stem: str) -> AdaptiveQuestionCandidate:
    return AdaptiveQuestionCandidate(
        question_id=question_id,
        difficulty_level=difficulty,
        category_name=category,
        stem_text=stem,
        external_ref=question_id,
    )


def test_engine_starts_at_medium_difficulty() -> None:
    engine = AdaptiveExamEngine()
    result = engine.select_next_question(
        state=AdaptiveExamState(),
        candidates=[
            _candidate("q1", 1, "Grammar", "easy"),
            _candidate("q2", 2, "Vocabulary", "medium"),
            _candidate("q3", 3, "Reading", "hard"),
        ],
        config=AdaptiveExamConfig(question_count=5),
    )

    assert result is not None
    assert result.question_id == "q2"
    assert result.target_difficulty == 2
    assert result.actual_difficulty == 2


def test_engine_moves_harder_after_correct_answer_and_easier_after_wrong_answer() -> None:
    engine = AdaptiveExamEngine()
    candidates = [
        _candidate("q1", 1, "Grammar", "easy"),
        _candidate("q2", 2, "Vocabulary", "medium"),
        _candidate("q3", 3, "Reading", "hard"),
    ]

    harder = engine.select_next_question(
        state=AdaptiveExamState(
            asked_questions=[AdaptiveAnswerRecord("q2", 2, "Vocabulary", True)]
        ),
        candidates=candidates,
        config=AdaptiveExamConfig(question_count=5),
    )
    easier = engine.select_next_question(
        state=AdaptiveExamState(
            asked_questions=[AdaptiveAnswerRecord("q2", 2, "Vocabulary", False)]
        ),
        candidates=candidates,
        config=AdaptiveExamConfig(question_count=5),
    )

    assert harder is not None and harder.question_id == "q3"
    assert easier is not None and easier.question_id == "q1"


def test_engine_avoids_repeats_and_uses_nearest_available_difficulty() -> None:
    engine = AdaptiveExamEngine()
    result = engine.select_next_question(
        state=AdaptiveExamState(
            asked_questions=[
                AdaptiveAnswerRecord("q2", 2, "Vocabulary", True),
                AdaptiveAnswerRecord("q3", 3, "Reading", True),
            ]
        ),
        candidates=[
            _candidate("q1", 1, "Grammar", "easy"),
            _candidate("q2", 2, "Vocabulary", "medium"),
            _candidate("q3", 3, "Reading", "hard"),
        ],
        config=AdaptiveExamConfig(question_count=5),
    )

    assert result is not None
    assert result.question_id == "q1"
    assert result.target_difficulty == 3
    assert result.actual_difficulty == 1


def test_engine_balances_categories_deterministically() -> None:
    engine = AdaptiveExamEngine()
    result = engine.select_next_question(
        state=AdaptiveExamState(
            asked_questions=[
                AdaptiveAnswerRecord("q1", 2, "Vocabulary", True),
                AdaptiveAnswerRecord("q2", 2, "Vocabulary", False),
            ]
        ),
        candidates=[
            _candidate("q3", 2, "Vocabulary", "vocab candidate"),
            _candidate("q4", 2, "Grammar", "grammar candidate"),
        ],
        config=AdaptiveExamConfig(question_count=5, enable_category_balancing=True),
    )

    assert result is not None
    assert result.question_id == "q4"


def test_engine_respects_configured_question_count() -> None:
    engine = AdaptiveExamEngine()
    result = engine.select_next_question(
        state=AdaptiveExamState(
            asked_questions=[
                AdaptiveAnswerRecord("q1", 2, "Vocabulary", True),
                AdaptiveAnswerRecord("q2", 3, "Reading", False),
            ]
        ),
        candidates=[
            _candidate("q1", 2, "Vocabulary", "one"),
            _candidate("q2", 3, "Reading", "two"),
            _candidate("q3", 1, "Grammar", "three"),
        ],
        config=AdaptiveExamConfig(question_count=2),
    )

    assert result is None
