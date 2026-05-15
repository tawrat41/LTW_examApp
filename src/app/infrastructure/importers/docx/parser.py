from __future__ import annotations

import re
from pathlib import Path

from .models import ImportIssue, ImportIssueSeverity, ParsedQuestion


QUESTION_PREFIX = "Question:"
OPTIONS_PREFIX = "Options:"
CORRECT_ANSWER_PREFIX = "Correct Answer:"
DIFFICULTY_PREFIX = "Difficulty:"
CATEGORY_PREFIX = "Category:"
EXPLANATION_PREFIX = "Explanation:"
OPTION_PATTERN = re.compile(r"^([A-Z])\.\s*(.+)$")
CHAPTER_PATTERN = re.compile(r"^\d+\s+(.+)$")
NUMBERED_LINE_PATTERN = re.compile(r"^\d+[\)\.]?\s*(.+)$")
INLINE_OPTION_PATTERN = re.compile(r"\b([A-Za-z][A-Za-z'’-]*)\s*/\s*([A-Za-z][A-Za-z'’-]*)\b")


class DocxQuestionBankParser:
    def parse_file(self, file_path: str | Path) -> tuple[list[ParsedQuestion], list[ImportIssue]]:
        path = Path(file_path)
        if not path.exists():
            return [], [
                ImportIssue(
                    sequence_number=None,
                    severity=ImportIssueSeverity.ERROR,
                    message=f"DOCX file not found: {path}",
                )
            ]

        try:
            from docx import Document
        except ModuleNotFoundError:
            return [], [
                ImportIssue(
                    sequence_number=None,
                    severity=ImportIssueSeverity.ERROR,
                    message="python-docx is not installed in the active virtual environment.",
                )
            ]

        try:
            document = Document(str(path))
        except Exception as exc:
            return [], [
                ImportIssue(
                    sequence_number=None,
                    severity=ImportIssueSeverity.ERROR,
                    message=f"Failed to open DOCX file: {exc}",
                )
            ]

        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
        return self.parse_paragraphs(paragraphs)

    def parse_paragraphs(self, paragraphs: list[str]) -> tuple[list[ParsedQuestion], list[ImportIssue]]:
        normalized_paragraphs = [paragraph.strip() for paragraph in paragraphs]
        if any(paragraph.startswith(QUESTION_PREFIX) for paragraph in normalized_paragraphs if paragraph):
            return self._parse_structured_question_bank(normalized_paragraphs)
        return self._parse_workbook_document(normalized_paragraphs)

    def _parse_structured_question_bank(self, paragraphs: list[str]) -> tuple[list[ParsedQuestion], list[ImportIssue]]:
        blocks = self._split_into_blocks(paragraphs)
        parsed_questions: list[ParsedQuestion] = []
        issues: list[ImportIssue] = []

        for sequence_number, block in enumerate(blocks, start=1):
            try:
                parsed_questions.append(self._parse_block(block, sequence_number))
            except ValueError as exc:
                issues.append(
                    ImportIssue(
                        sequence_number=sequence_number,
                        severity=ImportIssueSeverity.ERROR,
                        message=str(exc),
                        raw_block="\n".join(block),
                    )
                )

        return parsed_questions, issues

    def _parse_workbook_document(self, paragraphs: list[str]) -> tuple[list[ParsedQuestion], list[ImportIssue]]:
        parsed_questions: list[ParsedQuestion] = []
        issues: list[ImportIssue] = []
        current_category: str | None = None
        current_instruction: str | None = None
        sequence_number = 1

        for line_number, raw_line in enumerate(paragraphs, start=1):
            line = raw_line.strip()
            if not line:
                continue

            chapter_match = CHAPTER_PATTERN.match(line)
            if chapter_match and not line.startswith("1 ") and not line.startswith("2 "):
                current_category = chapter_match.group(1).strip()
                current_instruction = None
                continue
            if chapter_match and len(line.split()) <= 8:
                current_category = chapter_match.group(1).strip()
                current_instruction = None
                continue

            if re.match(r"^[A-Z]\s+", line):
                current_instruction = line
                continue

            numbered_segments = self._split_numbered_segments(line)
            if not numbered_segments:
                continue

            for question_text in numbered_segments:
                extracted = self._extract_workbook_question(
                    question_text=question_text,
                    sequence_number=sequence_number,
                    category=current_category,
                    instruction=current_instruction,
                )
                if extracted is None:
                    issues.append(
                        ImportIssue(
                            sequence_number=sequence_number,
                            severity=ImportIssueSeverity.WARNING,
                            message="Skipped workbook entry: could not infer a reliable MCQ with answer key.",
                            raw_block=f"{current_instruction or ''}\n{question_text}".strip(),
                        )
                    )
                    sequence_number += 1
                    continue

                parsed_questions.append(extracted)
                sequence_number += 1

        return parsed_questions, issues

    def _split_into_blocks(self, paragraphs: list[str]) -> list[list[str]]:
        blocks: list[list[str]] = []
        current_block: list[str] = []

        for raw_paragraph in paragraphs:
            paragraph = raw_paragraph.strip()
            if not paragraph:
                continue

            if paragraph.startswith(QUESTION_PREFIX) and current_block:
                blocks.append(current_block)
                current_block = [paragraph]
                continue

            current_block.append(paragraph)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _parse_block(self, block: list[str], sequence_number: int) -> ParsedQuestion:
        if not block:
            raise ValueError("Encountered an empty question block.")
        if not block[0].startswith(QUESTION_PREFIX):
            raise ValueError("Question block must start with 'Question:'.")

        options: dict[str, str] = {}
        correct_answer: str | None = None
        difficulty: str | None = None
        category: str | None = None
        explanation_lines: list[str] = []
        question_lines: list[str] = []
        in_options = False
        in_explanation = False
        awaiting_question_text = False
        awaiting_correct_answer = False

        first_question_line = block[0][len(QUESTION_PREFIX) :].strip()
        if first_question_line:
            question_lines.append(first_question_line)
        else:
            awaiting_question_text = True

        for line in block[1:]:
            if awaiting_question_text:
                if line in {OPTIONS_PREFIX, CORRECT_ANSWER_PREFIX}:
                    raise ValueError("Question text is missing.")
                if self._is_metadata_line(line):
                    raise ValueError("Question text is missing.")
                question_lines.append(line)
                awaiting_question_text = False
                continue

            if awaiting_correct_answer:
                if not line:
                    continue
                if self._is_metadata_line(line):
                    raise ValueError("Correct Answer value is missing.")
                correct_answer = line.strip()
                awaiting_correct_answer = False
                continue

            if line == OPTIONS_PREFIX:
                in_options = True
                in_explanation = False
                continue
            if line.startswith(CORRECT_ANSWER_PREFIX):
                in_options = False
                in_explanation = False
                correct_answer_value = line[len(CORRECT_ANSWER_PREFIX) :].strip()
                if correct_answer_value:
                    correct_answer = correct_answer_value
                else:
                    awaiting_correct_answer = True
                continue
            if line.startswith(DIFFICULTY_PREFIX):
                in_explanation = False
                difficulty = line[len(DIFFICULTY_PREFIX) :].strip() or None
                continue
            if line.startswith(CATEGORY_PREFIX):
                in_explanation = False
                category = line[len(CATEGORY_PREFIX) :].strip() or None
                continue
            if line.startswith(EXPLANATION_PREFIX):
                in_options = False
                in_explanation = True
                explanation_value = line[len(EXPLANATION_PREFIX) :].strip()
                if explanation_value:
                    explanation_lines.append(explanation_value)
                continue

            if in_options:
                option_match = OPTION_PATTERN.match(line)
                if option_match is None:
                    raise ValueError(f"Invalid option line: '{line}'")
                option_key, option_text = option_match.groups()
                if option_key in options:
                    raise ValueError(f"Duplicate option key '{option_key}'.")
                options[option_key] = option_text.strip()
                continue

            if in_explanation:
                explanation_lines.append(line)
                continue

            raise ValueError(f"Unexpected line in question block: '{line}'")

        question_text = "\n".join(question_lines).strip()
        if not question_text:
            raise ValueError("Question text is missing.")
        if not options:
            raise ValueError("Options section is missing or empty.")
        if len(options) < 2:
            raise ValueError("At least two options are required.")
        if correct_answer is None:
            raise ValueError("Correct Answer is missing.")

        correct_answer = correct_answer.strip().upper()
        if correct_answer not in options:
            raise ValueError("Correct Answer does not match any option key.")

        explanation = "\n".join(explanation_lines).strip() or None

        return ParsedQuestion(
            sequence_number=sequence_number,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            difficulty=difficulty,
            category=category,
            explanation=explanation,
        )

    def _is_metadata_line(self, line: str) -> bool:
        return (
            line == OPTIONS_PREFIX
            or line.startswith(CORRECT_ANSWER_PREFIX)
            or line.startswith(DIFFICULTY_PREFIX)
            or line.startswith(CATEGORY_PREFIX)
            or line.startswith(EXPLANATION_PREFIX)
        )

    def _extract_workbook_question(
        self,
        *,
        question_text: str,
        sequence_number: int,
        category: str | None,
        instruction: str | None,
    ) -> ParsedQuestion | None:
        instruction_text = (instruction or "").lower()

        right_wrong = self._extract_article_validity_question(question_text, sequence_number, category, instruction_text)
        if right_wrong is not None:
            return right_wrong

        slash_question = self._extract_inline_choice_question(question_text, sequence_number, category, instruction_text)
        if slash_question is not None:
            return slash_question

        return None

    def _extract_article_validity_question(
        self,
        question_text: str,
        sequence_number: int,
        category: str | None,
        instruction_text: str,
    ) -> ParsedQuestion | None:
        if "right" not in instruction_text or "wrong" not in instruction_text:
            return None

        tokens = question_text.replace("_", " ").split()
        if len(tokens) < 2:
            return None
        first_token = tokens[0].lower()
        if first_token not in {"a", "an"}:
            return None

        noun = tokens[1]
        is_correct = self._article_matches_word(first_token, noun)
        return ParsedQuestion(
            sequence_number=sequence_number,
            question_text=f"Is the phrase '{first_token} {noun}' grammatically correct?",
            options={"A": "Right", "B": "Wrong"},
            correct_answer="A" if is_correct else "B",
            difficulty="Medium",
            category=category,
            explanation="Determined from the article used before the following word.",
        )

    def _extract_inline_choice_question(
        self,
        question_text: str,
        sequence_number: int,
        category: str | None,
        instruction_text: str,
    ) -> ParsedQuestion | None:
        if question_text.count("/") != 1:
            return None
        option_match = INLINE_OPTION_PATTERN.search(question_text)
        if option_match is None:
            return None

        option_a = option_match.group(1)
        option_b = option_match.group(2)
        correct_option = self._infer_inline_choice_answer(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            instruction_text=instruction_text,
        )
        if correct_option is None:
            return None

        replaced = INLINE_OPTION_PATTERN.sub("____", question_text, count=1)
        return ParsedQuestion(
            sequence_number=sequence_number,
            question_text=f"Choose the correct option to complete the sentence: {replaced}",
            options={"A": option_a, "B": option_b},
            correct_answer="A" if correct_option == option_a else "B",
            difficulty="Medium",
            category=category,
            explanation="Determined from deterministic grammar pattern matching.",
        )

    def _infer_inline_choice_answer(
        self,
        *,
        question_text: str,
        option_a: str,
        option_b: str,
        instruction_text: str,
    ) -> str | None:
        lower_text = question_text.lower()
        normalized_a = option_a.lower()
        normalized_b = option_b.lower()
        pair_match = INLINE_OPTION_PATTERN.search(question_text)
        if pair_match is None:
            return None
        trailing_text = lower_text[pair_match.end() :].strip()
        trailing_padded = f" {trailing_text} "

        if {"he", "she", "it", "we", "they", "i", "you"} & {normalized_a, normalized_b}:
            if trailing_text.startswith("am ") or " am " in trailing_padded:
                return self._pick_from_set(option_a, option_b, {"i"})
            if trailing_text.startswith("is ") or " is " in trailing_padded:
                return self._pick_from_set(option_a, option_b, {"he", "she", "it"})
            if trailing_text.startswith("are ") or " are " in trailing_padded:
                return self._pick_from_set(option_a, option_b, {"we", "they", "you"})

        if {"a", "an"} == {normalized_a, normalized_b}:
            next_word = trailing_text.split()[0] if trailing_text.split() else ""
            if next_word:
                return option_a if self._article_matches_word(normalized_a, next_word) else option_b

        if {"have", "has"} == {normalized_a, normalized_b}:
            subject = trailing_text.split()[0] if trailing_text.split() else ""
            if subject in {"i", "you", "we", "they"}:
                return option_a if normalized_a == "have" else option_b
            if subject in {"he", "she", "it"}:
                return option_a if normalized_a == "has" else option_b

        if {"is", "are", "am"} & {normalized_a, normalized_b}:
            subject = trailing_text.split()[0] if trailing_text.split() else ""
            if subject == "i":
                return self._pick_from_set(option_a, option_b, {"am"})
            if subject in {"you", "we", "they"}:
                return self._pick_from_set(option_a, option_b, {"are"})
            if subject in {"he", "she", "it"}:
                return self._pick_from_set(option_a, option_b, {"is"})

        if "subject pronoun" in instruction_text:
            if trailing_text.startswith("is ") or " is " in trailing_padded:
                return self._pick_from_set(option_a, option_b, {"he", "she", "it"})
            if trailing_text.startswith("are ") or " are " in trailing_padded:
                return self._pick_from_set(option_a, option_b, {"we", "they", "you"})

        return None

    def _pick_from_set(self, option_a: str, option_b: str, valid_values: set[str]) -> str | None:
        if option_a.lower() in valid_values:
            return option_a
        if option_b.lower() in valid_values:
            return option_b
        return None

    def _article_matches_word(self, article: str, word: str) -> bool:
        cleaned = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", word).lower()
        if not cleaned:
            return False

        an_exceptions = ("honest", "hour", "heir", "honour")
        a_exceptions = ("university", "unicorn", "european", "one", "user", "ewe")
        if cleaned.startswith(an_exceptions):
            expected = "an"
        elif cleaned.startswith(a_exceptions):
            expected = "a"
        elif cleaned[0] in {"a", "e", "i", "o", "u"}:
            expected = "an"
        else:
            expected = "a"
        return article == expected

    def _split_numbered_segments(self, line: str) -> list[str]:
        if NUMBERED_LINE_PATTERN.match(line) is None:
            return []
        matches = list(re.finditer(r"(?<!\S)\d+[\)\.]?\s*", line))
        if not matches:
            return []

        segments: list[str] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(line)
            segment = line[start:end].strip()
            if segment:
                segments.append(segment)
        return segments
