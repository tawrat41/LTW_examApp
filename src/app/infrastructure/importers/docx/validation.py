from __future__ import annotations

from .models import ImportIssue, ImportIssueSeverity, ParsedQuestion


class QuestionBankValidator:
    VALID_DIFFICULTIES = {"easy", "medium", "hard"}

    def validate(self, questions: list[ParsedQuestion]) -> list[ImportIssue]:
        issues: list[ImportIssue] = []

        for question in questions:
            if len(question.question_text.strip()) < 3:
                issues.append(
                    ImportIssue(
                        sequence_number=question.sequence_number,
                        severity=ImportIssueSeverity.ERROR,
                        message="Question text is too short.",
                    )
                )

            if len(question.options) < 2:
                issues.append(
                    ImportIssue(
                        sequence_number=question.sequence_number,
                        severity=ImportIssueSeverity.ERROR,
                        message="Question must have at least two options.",
                    )
                )

            correct_option_text = question.options.get(question.correct_answer)
            if not correct_option_text:
                issues.append(
                    ImportIssue(
                        sequence_number=question.sequence_number,
                        severity=ImportIssueSeverity.ERROR,
                        message="Correct answer key is missing from options.",
                    )
                )

            if question.difficulty:
                normalized_difficulty = question.difficulty.strip().lower()
                if normalized_difficulty not in self.VALID_DIFFICULTIES:
                    issues.append(
                        ImportIssue(
                            sequence_number=question.sequence_number,
                            severity=ImportIssueSeverity.WARNING,
                            message=(
                                "Difficulty should be one of: Easy, Medium, Hard."
                            ),
                        )
                    )

            option_values = [value.strip() for value in question.options.values()]
            if len(option_values) != len(set(option_values)):
                issues.append(
                    ImportIssue(
                        sequence_number=question.sequence_number,
                        severity=ImportIssueSeverity.WARNING,
                        message="Option texts contain exact duplicates.",
                    )
                )

        return issues
