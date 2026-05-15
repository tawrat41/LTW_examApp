from __future__ import annotations

from app.application.importing import QuestionBankImportService
from app.infrastructure.importers.docx import DocxQuestionBankParser


def test_parser_extracts_complete_question_blocks() -> None:
    parser = DocxQuestionBankParser()
    paragraphs = [
        "Question:",
        'What is the synonym of "happy"?',
        "Options:",
        "A. Angry",
        "B. Joyful",
        "C. Sad",
        "D. Tired",
        "Correct Answer:",
        "B",
        "Difficulty: Medium",
        "Category: Vocabulary",
        "Explanation: Joyful has the closest meaning to happy.",
        "",
        "Question: Choose the correct article.",
        "Options:",
        "A. a",
        "B. an",
        "Correct Answer: B",
    ]

    parsed_questions, issues = parser.parse_paragraphs(paragraphs)

    assert issues == []
    assert len(parsed_questions) == 2
    assert parsed_questions[0].question_text == 'What is the synonym of "happy"?'
    assert parsed_questions[0].options["B"] == "Joyful"
    assert parsed_questions[0].correct_answer == "B"
    assert parsed_questions[0].difficulty == "Medium"
    assert parsed_questions[0].category == "Vocabulary"
    assert parsed_questions[0].explanation == "Joyful has the closest meaning to happy."


def test_import_service_skips_malformed_entries_and_reports_duplicates() -> None:
    service = QuestionBankImportService()
    paragraphs = [
        "Question: Valid question one?",
        "Options:",
        "A. First",
        "B. Second",
        "Correct Answer: A",
        "",
        "Question: Broken question",
        "Options:",
        "A. Only one option",
        "Correct Answer: A",
        "",
        "Question: Valid question one?",
        "Options:",
        "A. Duplicate",
        "B. Different",
        "Correct Answer: B",
    ]

    report = service.import_from_paragraphs(paragraphs)

    assert len(report.parsed_questions) == 1
    assert report.parsed_questions[0].question_text == "Valid question one?"
    assert len(report.duplicates) == 1
    assert report.duplicates[0].original_sequence_number == 1
    assert report.duplicates[0].duplicate_sequence_number == 3
    assert any(issue.sequence_number == 2 for issue in report.issues)
    assert any(issue.sequence_number == 3 for issue in report.issues)


def test_parser_extracts_supported_workbook_questions() -> None:
    parser = DocxQuestionBankParser()
    paragraphs = [
        "4 She's a photographer",
        "B Circle the subject pronoun.",
        "1 He / We is an actor.",
        "2 We / She are teachers.",
        "1 a/an",
        "A Right (√) or wrong (×)?",
        "1 an office __________ 2 an university __________",
        "3 a station __________ 4 a airport __________",
    ]

    parsed_questions, issues = parser.parse_paragraphs(paragraphs)

    assert len(parsed_questions) == 6
    assert parsed_questions[0].options == {"A": "He", "B": "We"}
    assert parsed_questions[0].correct_answer == "A"
    assert parsed_questions[1].correct_answer == "A"
    assert parsed_questions[2].options == {"A": "Right", "B": "Wrong"}
    assert parsed_questions[2].correct_answer == "A"
    assert parsed_questions[3].correct_answer == "B"
    assert parsed_questions[5].correct_answer == "B"
    assert issues == []


def test_parser_reports_unsupported_workbook_entries_without_crashing() -> None:
    parser = DocxQuestionBankParser()
    paragraphs = [
        "1 Your Body",
        "A Circle the correct word in each pair.",
        "1 shoulder / knee",
        "2 finger / toe",
        "3 Describing character",
        "A Complete the sentences with the words in the box.",
        "1 Alsana's a clever person.",
    ]

    parsed_questions, issues = parser.parse_paragraphs(paragraphs)

    assert parsed_questions == []
    assert len(issues) >= 2
    assert all("Skipped workbook entry" in issue.message for issue in issues)
