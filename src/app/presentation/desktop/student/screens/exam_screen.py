from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.application.adaptive import AdaptiveExamQuestionView
from app.presentation.desktop.student.state import QuestionHistoryEntry, StudentExamSessionState
from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class StudentExamScreen(QWidget):
    exam_finished = Signal(str)

    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._state: StudentExamSessionState | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._option_buttons: list[QRadioButton] = []
        self._option_group = QButtonGroup(self)
        self._option_group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        self.header = SectionHeader("Exam", "Answer one question at a time.")
        layout.addWidget(self.header)
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        top_card = card_container()
        top_layout = QHBoxLayout(top_card)
        self.progress_label = QLabel("Question 0 of 0")
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #d96c06;")
        top_layout.addWidget(self.progress_label)
        top_layout.addStretch(1)
        top_layout.addWidget(self.timer_label)
        layout.addWidget(top_card)

        question_card = card_container()
        question_layout = QVBoxLayout(question_card)
        self.meta_label = QLabel("")
        self.meta_label.setProperty("role", "muted")
        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.options_host = QFrame()
        self.options_layout = QVBoxLayout(self.options_host)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(10)
        question_layout.addWidget(self.meta_label)
        question_layout.addWidget(self.question_label)
        question_layout.addWidget(self.options_host)
        layout.addWidget(question_card, 1)

        actions = QHBoxLayout()
        self.previous_button = PrimaryButton("Previous")
        self.previous_button.setProperty("variant", "")
        self.next_button = PrimaryButton("Next")
        self.submit_button = PrimaryButton("Submit Exam")
        self.previous_button.clicked.connect(self._go_previous)
        self.next_button.clicked.connect(self._go_next)
        self.submit_button.clicked.connect(self._submit_exam)
        actions.addWidget(self.previous_button)
        actions.addWidget(self.next_button)
        actions.addStretch(1)
        actions.addWidget(self.submit_button)
        layout.addLayout(actions)

        self._build_shortcuts()

    def load_session(self, state: StudentExamSessionState) -> None:
        self._state = state
        self._timer.start(1000)
        self._render()

    def stop_session(self) -> None:
        self._timer.stop()

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Return"), self, activated=self._go_next)
        QShortcut(QKeySequence("Enter"), self, activated=self._go_next)
        QShortcut(QKeySequence("Alt+Left"), self, activated=self._go_previous)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self._go_next)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._submit_exam)
        for index, key in enumerate(["1", "2", "3", "4", "A", "B", "C", "D"], start=1):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda idx=index: self._select_by_shortcut(idx))

    def _select_by_shortcut(self, index: int) -> None:
        entry = self._current_entry()
        if entry is None or entry.submitted:
            return
        normalized_index = index - 1 if index <= 4 else index - 5
        if 0 <= normalized_index < len(self._option_buttons):
            self._option_buttons[normalized_index].setChecked(True)

    def _current_entry(self) -> QuestionHistoryEntry | None:
        if self._state is None:
            return None
        return self._state.current_entry

    def _render(self) -> None:
        entry = self._current_entry()
        if self._state is None or entry is None:
            return
        question = entry.question
        self.header.set_text("Exam", self._state.exam.title)
        self.progress_label.setText(
            f"Question {min(self._state.current_index + 1, self._state.exam.question_count)} "
            f"of {self._state.exam.question_count}"
        )
        self.meta_label.setText(
            f"Category: {question.category_name or 'General'} | Difficulty: {question.difficulty_level}"
        )
        self.question_label.setText(question.stem_text)
        self._rebuild_options(question, entry)
        self.previous_button.setEnabled(
            self._state.exam.allow_previous and self._state.current_index > 0
        )
        is_latest = self._state.current_index == self._state.latest_index
        if is_latest and not entry.submitted:
            self.next_button.setText("Next")
            self.next_button.setEnabled(entry.selected_option_id is not None)
        else:
            self.next_button.setText("Continue")
            self.next_button.setEnabled(self._state.current_index < self._state.latest_index)

    def _rebuild_options(self, question: AdaptiveExamQuestionView, entry: QuestionHistoryEntry) -> None:
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._option_buttons = []
        self._option_group = QButtonGroup(self)
        self._option_group.setExclusive(True)
        self._option_group.buttonToggled.connect(self._on_option_toggled)
        for option in question.options:
            button = QRadioButton(f"{option['key']}. {option['text']}")
            button.setProperty("option_id", option["option_id"])
            button.setEnabled(not entry.submitted and self._state.current_index == self._state.latest_index)
            if entry.selected_option_id == option["option_id"]:
                button.setChecked(True)
            button.setStyleSheet("padding: 10px 8px; font-size: 15px;")
            self.options_layout.addWidget(button)
            self._option_group.addButton(button)
            self._option_buttons.append(button)
        self.options_layout.addStretch(1)

    def _on_option_toggled(self, *_args) -> None:
        entry = self._current_entry()
        if entry is None or entry.submitted:
            return
        checked = self._option_group.checkedButton()
        entry.selected_option_id = checked.property("option_id") if checked is not None else None
        self._render()

    def _go_previous(self) -> None:
        if self._state is None or not self._state.exam.allow_previous:
            return
        if self._state.current_index <= 0:
            return
        self._state.current_index -= 1
        self._render()

    def _go_next(self) -> None:
        self.banner.clear_message()
        if self._state is None:
            return
        entry = self._current_entry()
        if entry is None:
            return
        is_latest = self._state.current_index == self._state.latest_index
        if not is_latest or entry.submitted:
            if self._state.current_index < self._state.latest_index:
                self._state.current_index += 1
                self._render()
            return
        if entry.selected_option_id is None:
            self.banner.show_error("Select an option before continuing.")
            return
        progress = self._app_context.exam_portal.submit_answer(
            attempt_id=self._state.attempt_id,
            question_id=entry.question.question_id,
            selected_option_id=entry.selected_option_id,
        )
        entry.submitted = True
        if progress.next_question is not None:
            self._state.history.append(QuestionHistoryEntry(progress.next_question))
            self._state.current_index = self._state.latest_index
            self._render()
            return
        result = self._app_context.exam_portal.get_result(self._state.attempt_id)
        self.stop_session()
        self.exam_finished.emit(result.attempt_id)

    def _submit_exam(self) -> None:
        if self._state is None:
            return
        answer = QMessageBox.question(
            self,
            "Submit Exam",
            "Submit the exam now? Unanswered questions will remain blank.",
        )
        if answer != QMessageBox.Yes:
            return
        self._app_context.exam_portal.finalize_attempt(self._state.attempt_id)
        self.stop_session()
        self.exam_finished.emit(self._state.attempt_id)

    def _tick(self) -> None:
        if self._state is None or self._state.ends_at is None:
            return
        remaining = int((self._state.ends_at - datetime.now()).total_seconds())
        if remaining <= 0:
            self.timer_label.setText("00:00")
            self.stop_session()
            self._app_context.exam_portal.finalize_attempt(self._state.attempt_id)
            self.exam_finished.emit(self._state.attempt_id)
            return
        minutes, seconds = divmod(remaining, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
