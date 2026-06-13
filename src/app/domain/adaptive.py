from __future__ import annotations

from dataclasses import dataclass, field


EASY_DIFFICULTY = 1
MEDIUM_DIFFICULTY = 2
HARD_DIFFICULTY = 3


@dataclass(slots=True, frozen=True)
class AdaptiveQuestionCandidate:
    question_id: str
    difficulty_level: int
    category_name: str | None
    stem_text: str
    external_ref: str


@dataclass(slots=True, frozen=True)
class AdaptiveAnswerRecord:
    question_id: str
    difficulty_level: int
    category_name: str | None
    is_correct: bool
    stem_text: str | None = None
    external_ref: str | None = None


@dataclass(slots=True, frozen=True)
class AdaptiveExamConfig:
    question_count: int
    starting_difficulty: int = MEDIUM_DIFFICULTY
    enable_category_balancing: bool = True


@dataclass(slots=True, frozen=True)
class AdaptiveSelectionResult:
    question_id: str
    target_difficulty: int
    actual_difficulty: int
    category_name: str | None


@dataclass(slots=True)
class AdaptiveExamState:
    asked_questions: list[AdaptiveAnswerRecord] = field(default_factory=list)


class AdaptiveExamEngine:
    """Deterministic adaptive item selection."""

    def select_next_question(
        self,
        *,
        state: AdaptiveExamState,
        candidates: list[AdaptiveQuestionCandidate],
        config: AdaptiveExamConfig,
    ) -> AdaptiveSelectionResult | None:
        if config.question_count <= 0:
            return None
        if len(state.asked_questions) >= config.question_count:
            return None

        asked_ids = {item.question_id for item in state.asked_questions}
        asked_stems = {item.stem_text.strip().lower() for item in state.asked_questions if item.stem_text}
        asked_refs = {item.external_ref for item in state.asked_questions if item.external_ref}

        remaining_candidates = [
            item for item in candidates
            if item.question_id not in asked_ids
            and (not item.stem_text or item.stem_text.strip().lower() not in asked_stems)
            and (not item.external_ref or item.external_ref not in asked_refs)
        ]
        if not remaining_candidates:
            return None

        target_difficulty = self._resolve_target_difficulty(state, config)
        chosen_candidate = self._choose_candidate(
            remaining_candidates,
            state.asked_questions,
            target_difficulty,
            config.enable_category_balancing,
        )
        return AdaptiveSelectionResult(
            question_id=chosen_candidate.question_id,
            target_difficulty=target_difficulty,
            actual_difficulty=chosen_candidate.difficulty_level,
            category_name=chosen_candidate.category_name,
        )

    def _resolve_target_difficulty(
        self,
        state: AdaptiveExamState,
        config: AdaptiveExamConfig,
    ) -> int:
        if not state.asked_questions:
            return self._normalize_difficulty(config.starting_difficulty)

        last_answer = state.asked_questions[-1]
        current = self._normalize_difficulty(last_answer.difficulty_level)
        if last_answer.is_correct:
            return min(HARD_DIFFICULTY, current + 1)
        return max(EASY_DIFFICULTY, current - 1)

    def _choose_candidate(
        self,
        candidates: list[AdaptiveQuestionCandidate],
        asked_questions: list[AdaptiveAnswerRecord],
        target_difficulty: int,
        enable_category_balancing: bool,
    ) -> AdaptiveQuestionCandidate:
        nearest_distance = min(
            abs(self._normalize_difficulty(item.difficulty_level) - target_difficulty)
            for item in candidates
        )
        difficulty_filtered = [
            item
            for item in candidates
            if abs(self._normalize_difficulty(item.difficulty_level) - target_difficulty) == nearest_distance
        ]

        category_counts = self._build_category_counts(asked_questions)
        if enable_category_balancing:
            min_category_count = min(
                category_counts.get(item.category_name or "", 0) for item in difficulty_filtered
            )
            difficulty_filtered = [
                item
                for item in difficulty_filtered
                if category_counts.get(item.category_name or "", 0) == min_category_count
            ]

        return sorted(
            difficulty_filtered,
            key=lambda item: (
                category_counts.get(item.category_name or "", 0),
                item.category_name or "",
                item.external_ref,
                item.stem_text,
                item.question_id,
            ),
        )[0]

    def _build_category_counts(self, asked_questions: list[AdaptiveAnswerRecord]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in asked_questions:
            key = item.category_name or ""
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _normalize_difficulty(self, difficulty_level: int) -> int:
        if difficulty_level <= EASY_DIFFICULTY:
            return EASY_DIFFICULTY
        if difficulty_level >= HARD_DIFFICULTY:
            return HARD_DIFFICULTY
        return MEDIUM_DIFFICULTY
