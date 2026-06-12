from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.presentation.desktop.widgets.common import ActionCard, QuickLink, SectionHeader, StatCard, card_container


class DashboardScreen(QWidget):
    navigation_requested = Signal(str)

    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        self.header = SectionHeader("Dashboard", "Welcome back! Here's an overview of your exam system.")
        layout.addWidget(self.header)

        # Top Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        self._cards = {
            "exams": StatCard("Total Exams", "#4F46E5"),
            "students": StatCard("Registered Students", "#10B981"),
            "questions": StatCard("Question Bank", "#F59E0B"),
            "active_students": StatCard("Current Attempts", "#8B5CF6"),
        }
        for card in self._cards.values():
            stats_layout.addWidget(card, 1)
        layout.addLayout(stats_layout)

        # Main Content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # Left Side: Action Center
        actions_column = QVBoxLayout()
        actions_column.setSpacing(20)
        
        actions_lbl = QLabel("ACTION CENTER")
        actions_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        actions_column.addWidget(actions_lbl)
        
        self.manage_exams = ActionCard("Manage Exams", "Configure and publish new exams", "🎯", "#4F46E5")
        self.manage_questions = ActionCard("Question Bank Manager", "Update and review question repository", "📚", "#F59E0B")
        self.view_reports = ActionCard("Analyze Reports", "View student performance and analytics", "📊", "#10B981")
        
        self.manage_exams.clicked.connect(lambda: self.navigation_requested.emit("exams"))
        self.manage_questions.clicked.connect(lambda: self.navigation_requested.emit("questions"))
        self.view_reports.clicked.connect(lambda: self.navigation_requested.emit("reporting"))
        
        actions_column.addWidget(self.manage_exams)
        actions_column.addWidget(self.manage_questions)
        actions_column.addWidget(self.view_reports)
        actions_column.addStretch(1)
        
        content_layout.addLayout(actions_column, 2)
        
        # Right Side: Quick Links & System
        side_column = QVBoxLayout()
        side_column.setSpacing(20)
        
        side_card = card_container()
        side_layout = QVBoxLayout(side_card)
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(15)
        
        side_lbl = QLabel("QUICK LINKS")
        side_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        side_layout.addWidget(side_lbl)
        
        side_layout.addWidget(QuickLink("Import DOCX Questions", "📥"))
        side_layout.addWidget(QuickLink("Manage Students", "👤"))
        side_layout.addWidget(QuickLink("System Settings", "⚙️"))
        side_layout.addStretch(1)
        
        side_column.addWidget(side_card)
        content_layout.addLayout(side_column, 1)
        
        layout.addLayout(content_layout, 1)

    def refresh(self) -> None:
        stats = self._app_context.admin_queries.get_dashboard_stats()
        self._cards["exams"].set_value(str(stats.exams_count))
        self._cards["students"].set_value(str(stats.students_count))
        self._cards["questions"].set_value(str(stats.questions_count))
        self._cards["active_students"].set_value(str(stats.active_students_count))
