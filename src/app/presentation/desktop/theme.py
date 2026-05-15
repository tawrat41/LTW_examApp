from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #f4efe7;
        color: #1f2933;
        font-family: 'Segoe UI Variable Display', 'Bahnschrift', 'Segoe UI';
        font-size: 13px;
    }
    QMainWindow, QDialog {
        background: #f4efe7;
    }
    QFrame#sidebar {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #143642, stop:1 #0f2a33);
        border-right: 1px solid #0c1f25;
    }
    QFrame#contentShell {
        background: #f7f3ee;
    }
    QLabel#appTitle {
        color: #fdfcf8;
        font-size: 26px;
        font-weight: 700;
    }
    QLabel#sectionTitle {
        color: #102a43;
        font-size: 22px;
        font-weight: 700;
    }
    QLabel#sectionSubtitle {
        color: #52606d;
        font-size: 12px;
    }
    QPushButton {
        background: #ffffff;
        border: 1px solid #d6d2cb;
        border-radius: 10px;
        padding: 10px 14px;
    }
    QPushButton:hover {
        border-color: #b8aea0;
        background: #fbfaf7;
    }
    QPushButton:pressed {
        background: #f1ede6;
    }
    QPushButton[variant="primary"] {
        background: #d96c06;
        color: #ffffff;
        border: none;
        font-weight: 600;
    }
    QPushButton[variant="primary"]:hover {
        background: #bf5e04;
    }
    QPushButton[nav="true"] {
        background: transparent;
        color: #f5efe6;
        text-align: left;
        border: none;
        border-radius: 12px;
        padding: 12px 14px;
        font-weight: 600;
    }
    QPushButton[nav="true"]:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    QPushButton[nav="true"][active="true"] {
        background: #f0b429;
        color: #102a43;
    }
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: #ffffff;
        border: 1px solid #d6d2cb;
        border-radius: 10px;
        padding: 9px 10px;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
        border: 1px solid #d96c06;
    }
    QTableWidget, QListWidget {
        background: #ffffff;
        border: 1px solid #d6d2cb;
        border-radius: 12px;
        gridline-color: #ece6dd;
    }
    QHeaderView::section {
        background: #efe7dc;
        color: #243b53;
        border: none;
        border-bottom: 1px solid #d6d2cb;
        padding: 10px;
        font-weight: 700;
    }
    QTabWidget::pane {
        border: 1px solid #d6d2cb;
        border-radius: 12px;
        background: #ffffff;
    }
    QTabBar::tab {
        background: #eadfce;
        padding: 10px 14px;
        margin-right: 4px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }
    QTabBar::tab:selected {
        background: #ffffff;
    }
    QFrame.card {
        background: #ffffff;
        border: 1px solid #ddd5cb;
        border-radius: 16px;
    }
    QLabel[role="muted"] {
        color: #7b8794;
    }
    QLabel[role="error"] {
        color: #b42318;
        font-weight: 600;
    }
    QLabel[role="success"] {
        color: #087443;
        font-weight: 600;
    }
    QProgressBar {
        border: 1px solid #d6d2cb;
        border-radius: 8px;
        background: #f9f6f0;
        text-align: center;
    }
    QProgressBar::chunk {
        background: #d96c06;
        border-radius: 8px;
    }
    """
