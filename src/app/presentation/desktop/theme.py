from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #F8FAFC;
        color: #1E293B;
        font-family: 'Segoe UI Variable Display', 'Inter', 'Segoe UI', system-ui;
        font-size: 14px;
    }
    QMainWindow, QDialog, QFrame#contentShell {
        background: #F8FAFC;
    }
    QFrame#sidebar, QFrame#sidebar QWidget {
        background: #0F172A;
    }
    QLabel, QCheckBox, QRadioButton {
        background: transparent;
        border: none;
    }
    QLabel#appTitle {
        color: #F1F5F9;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    QPushButton {
        background: #FFFFFF;
        color: #334155;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #F1F5F9;
        border-color: #CBD5E1;
    }
    QPushButton[nav="true"] {
        background: transparent;
        color: #94A3B8;
        text-align: left;
        border: none;
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 600;
        margin: 2px 8px;
    }
    QPushButton[nav="true"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #F1F5F9;
    }
    QPushButton[nav="true"][active="true"] {
        background: rgba(255, 255, 255, 0.1);
        color: #FFFFFF;
        border-left: 3px solid #6366F1;
        border-radius: 0px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }
    QLineEdit, QComboBox, QSpinBox {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 12px;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #C7D2FE;
    }
    QTableWidget {
        background: #FFFFFF;
        alternate-background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        gridline-color: #F1F5F9;
        font-size: 14px;
        color: #1E293B;
        selection-background-color: #EEF2FF;
        selection-color: #4F46E5;
        outline: none;
    }
    QTableWidget::item {
        padding: 12px 15px;
    }
    QHeaderView::section {
        background: #F8FAFC;
        color: #64748B;
        border: none;
        border-bottom: 2px solid #E2E8F0;
        padding: 15px;
        font-weight: 800;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    QTabWidget::pane {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background: #FFFFFF;
        top: -1px;
    }
    QTabBar::tab {
        background: #F1F5F9;
        color: #64748B;
        padding: 10px 24px;
        margin-right: 4px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        font-weight: 600;
    }
    QTabBar::tab:selected {
        background: #FFFFFF;
        color: #4F46E5;
        border: 1px solid #E2E8F0;
        border-bottom: none;
    }
    QCheckBox {
        spacing: 10px;
        font-weight: 500;
        color: #475569;
    }
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border: 2px solid #E2E8F0;
        border-radius: 6px;
        background: #FFFFFF;
    }
    QCheckBox::indicator:hover {
        border-color: #C7D2FE;
    }
    QCheckBox::indicator:checked {
        background-color: #4F46E5;
        border-color: #4F46E5;
        image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAACXBIWXMAAAsTAAALEwEAmpwYAAABJUlEQVQ4T2P4//8/AyUYREAsC0S7gfgvEAcB8X+oXF4g9gFiXyD+D8X/oXJ5gcwSAsSCQDwFiP8D8X8g/g+Vyw9klRAgFgaSOUD8D4h/APF/qFxBIB6IAHEgkByE4n8g/g/E/6Fy+YEMEALEPEDyPwj/B+L/QPwfKlcAiAciQKIEIPkPhP8D8X+oXH4gHoigMIAkAAn/B+H/QPwfKJcfiAciGAtgCIAE/v8H4f9A/B8olx+IByIYC+BfIPkfBP8D4P9AOfxAByIDvEDYB4h9gfgfEP8H4v9QOfxAByIDrEDkBcK+QPwfKBcXyBwhQGwExFZA7AtE/oDIH6icAiADDAWwAhEnEHMBsR8QCUA5+UAsCKQKQAL/oXIJoYIMADu+e+S4P+5LAAAAAElFTkSuQmCC);
    }
    QProgressBar {
        border: none;
        border-radius: 10px;
        background: #F1F5F9;
        height: 10px;
    }
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #8B5CF6);
        border-radius: 10px;
    }
    """
