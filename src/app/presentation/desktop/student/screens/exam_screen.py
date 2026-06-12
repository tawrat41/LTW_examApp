from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.application.adaptive import AdaptiveExamQuestionView
from app.presentation.desktop.student.state import QuestionHistoryEntry, StudentExamSessionState
from app.presentation.desktop.widgets.common import Badge, MessageBanner, PrimaryButton, SectionHeader, StatsWidget, card_container


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
        
        header_layout = QHBoxLayout()
        self.header = SectionHeader("Exam", "Exam Title")
        self.stats = StatsWidget()
        header_layout.addWidget(self.header)
        header_layout.addStretch(1)
        header_layout.addWidget(self.stats)
        layout.addLayout(header_layout)
        
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        info_bar = QHBoxLayout()
        self.progress_label = QLabel("Question 0 of 0")
        self.progress_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #4F46E5;")
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A; background: #F1F5F9; padding: 5px 15px; border-radius: 8px;")
        info_bar.addWidget(self.progress_label)
        info_bar.addStretch(1)
        info_bar.addWidget(self.timer_label)
        layout.addLayout(info_bar)

        question_card = card_container()
        question_card.setStyleSheet("background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 20px;")
        
        # Shadow effect for the main question card
        question_shadow = QGraphicsDropShadowEffect(question_card)
        question_shadow.setBlurRadius(30)
        question_shadow.setXOffset(0)
        question_shadow.setYOffset(10)
        question_shadow.setColor(Qt.GlobalColor.black if hasattr(Qt, 'GlobalColor') else Qt.black)
        question_shadow.color().setAlpha(10)
        question_card.setGraphicsEffect(question_shadow)

        question_layout = QVBoxLayout(question_card)
        question_layout.setContentsMargins(40, 40, 40, 40)
        question_layout.setSpacing(25)
        
        self.meta_layout = QHBoxLayout()
        self.meta_layout.setSpacing(10)
        self.category_badge = Badge("", color="#4F46E5", bg="#EEF2FF")
        self.difficulty_badge = Badge("", color="#059669", bg="#ECFDF5")
        # self.meta_layout.addWidget(self.category_badge)
        # self.meta_layout.addWidget(self.difficulty_badge)
        self.meta_layout.addStretch(1)
        
        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A; line-height: 140%;")
        
        self.options_host = QFrame()
        self.options_layout = QVBoxLayout(self.options_host)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(12)
        
        question_layout.addLayout(self.meta_layout)
        question_layout.addWidget(self.question_label)
        question_layout.addWidget(self.options_host)
        question_layout.addStretch(1)
        layout.addWidget(question_card, 1)

        self._opacity_effect = QGraphicsOpacityEffect(question_card)
        question_card.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        actions = QHBoxLayout()
        self.previous_button = QPushButton("←  Previous")
        self.previous_button.setCursor(Qt.PointingHandCursor)
        self.previous_button.setFixedHeight(46)
        self.previous_button.setStyleSheet("padding: 0 25px;")
        
        self.skip_button = QPushButton("Skip Question")
        self.skip_button.setCursor(Qt.PointingHandCursor)
        self.skip_button.setFixedHeight(46)
        self.skip_button.setStyleSheet("padding: 0 25px; color: #64748B;")
        
        self.next_button = PrimaryButton("Next Question  →")
        self.next_button.setFixedWidth(200)
        
        self.submit_button = PrimaryButton("Finish & Submit")
        self.submit_button.setProperty("variant", "destructive")
        self.submit_button.setFixedWidth(180)
        
        self.previous_button.clicked.connect(self._go_previous)
        self.skip_button.clicked.connect(self._go_skip)
        self.next_button.clicked.connect(self._go_next)
        self.submit_button.clicked.connect(self._submit_exam)
        
        actions.addWidget(self.previous_button)
        actions.addWidget(self.skip_button)
        actions.addStretch(1)
        actions.addWidget(self.next_button)
        actions.addSpacing(20)
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
        
        # Trigger fade animation on change
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(0)
        self._fade_anim.start()

        question = entry.question
        self.header.set_text("Exam", self._state.exam.title)
        self.progress_label.setText(
            f"Question {min(self._state.current_index + 1, self._state.exam.question_count)} "
            f"of {self._state.exam.question_count}"
        )
        self.category_badge.setText(question.category_name or "General")
        
        if question.difficulty_level >= 3:
            self.difficulty_badge.setText("HARD")
            self.difficulty_badge.setStyleSheet("padding: 4px 10px; border-radius: 6px; background: #FEF2F2; color: #DC2626; font-size: 11px; font-weight: 700; text-transform: uppercase; border: 1px solid #DC262633;")
        elif question.difficulty_level == 2:
            self.difficulty_badge.setText("MEDIUM")
            self.difficulty_badge.setStyleSheet("padding: 4px 10px; border-radius: 6px; background: #FFFBEB; color: #D97706; font-size: 11px; font-weight: 700; text-transform: uppercase; border: 1px solid #D9770633;")
        else:
            self.difficulty_badge.setText("EASY")
            self.difficulty_badge.setStyleSheet("padding: 4px 10px; border-radius: 6px; background: #F0FDF4; color: #16A34A; font-size: 11px; font-weight: 700; text-transform: uppercase; border: 1px solid #16A34A33;")

        self.question_label.setText(question.stem_text)
        self._rebuild_options(question, entry)
        
        # Stats update
        answered = sum(1 for e in self._state.history if e.submitted or e.selected_option_id is not None)
        self.stats.update_stats(answered, self._state.exam.question_count)

        self.previous_button.setEnabled(self._state.current_index > 0)
        is_latest = self._state.current_index == self._state.latest_index
        
        if is_latest and not entry.submitted:
            self.next_button.setText("Submit Answer  →")
            self.skip_button.show()
        else:
            self.next_button.setText("Continue  →")
            self.skip_button.hide()
            
        self.next_button.setEnabled(not is_latest or entry.selected_option_id is not None)

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
            button = QRadioButton(f" {option['key']}. {option['text']}")
            button.setProperty("option_id", option["option_id"])
            button.setEnabled(not entry.submitted and self._state.current_index == self._state.latest_index)
            button.setCursor(Qt.PointingHandCursor)
            if entry.selected_option_id == option["option_id"]:
                button.setChecked(True)
            
            # Modern radio button styling with indicator
            button.setStyleSheet("""
                QRadioButton {
                    padding: 18px 24px;
                    padding-left: 50px;
                    font-size: 17px;
                    font-weight: 500;
                    border: 2px solid #E2E8F0;
                    border-radius: 12px;
                    background: #FFFFFF;
                }
                QRadioButton:hover {
                    background: #F8FAFC;
                    border-color: #CBD5E1;
                }
                QRadioButton:checked {
                    background: #EEF2FF;
                    border-color: #4F46E5;
                    color: #4338CA;
                    font-weight: 700;
                }
                QRadioButton::indicator {
                    width: 22px;
                    height: 22px;
                    border: 2px solid #CBD5E1;
                    border-radius: 11px;
                    background: #FFFFFF;
                    position: absolute;
                    left: 20px;
                }
                QRadioButton::indicator:checked {
                    border: 6px solid #4F46E5;
                    background: #FFFFFF;
                }
            """)
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
        if self._state is None:
            return
        if self._state.current_index <= 0:
            return
        self._state.current_index -= 1
        self._render()

    def _go_skip(self) -> None:
        self._go_next(force_skip=True)

    def _go_next(self, force_skip: bool = False) -> None:
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
        if entry.selected_option_id is None and not force_skip:
            self.banner.show_error("Select an option or use 'Skip' to continue.")
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
