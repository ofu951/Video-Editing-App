"""Uygulamanin genel Qt stylesheet tanimi (Modern Dark / Fluent Design)."""

STYLESHEET = """
/* ── Zemin ─────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0F0F1A;
    color: #D0D0E0;
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    font-size: 13px;
}

/* ── Tab Bar ───────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2A2A40;
    background: #14142A;
    border-radius: 6px;
}
QTabBar::tab {
    background: #0F0F1A;
    color: #7070A0;
    padding: 9px 18px;
    border: 1px solid #2A2A40;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background: #14142A;
    color: #00FFCC;
    font-weight: bold;
    border-bottom: 2px solid #00FFCC;
}
QTabBar::tab:hover:!selected {
    background: #1E1E30;
    color: #CCCCFF;
}

/* ── Butonlar ──────────────────────────────────────────────────── */
QPushButton {
    background-color: #00D2D3;
    color: #0A0A1A;
    border: none;
    border-radius: 7px;
    padding: 9px 16px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #00FFCC;
}
QPushButton:pressed {
    background-color: #009999;
}
QPushButton:disabled {
    background-color: #252535;
    color: #44445A;
    border: 1px solid #1A1A2A;
}

/* ── Input / TextEdit ──────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1A1A2C;
    border: 1px solid #2A2A45;
    color: #E0E0F0;
    border-radius: 6px;
    padding: 7px 10px;
    selection-background-color: #00D2D3;
    selection-color: #000;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #00FFCC;
    background-color: #1C1C30;
}
QComboBox::drop-down { border: none; }
QComboBox::down-arrow { color: #00D2D3; }

/* ── Progress Bar ──────────────────────────────────────────────── */
QProgressBar {
    background-color: #1A1A2C;
    border: 1px solid #2A2A45;
    border-radius: 6px;
    text-align: center;
    color: #E0E0F0;
    font-size: 12px;
    height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00BFFF, stop:1 #00FFCC);
    border-radius: 6px;
}

/* ── Tablo ─────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #14142A;
    border: 1px solid #2A2A40;
    color: #D0D0E0;
    gridline-color: #252540;
    selection-background-color: #00D2D3;
    selection-color: #0A0A1A;
    alternate-background-color: #17172D;
}
QHeaderView::section {
    background-color: #20203A;
    color: #00D2D3;
    padding: 7px;
    border: 1px solid #1A1A2A;
    font-weight: bold;
    font-size: 12px;
}

/* ── ScrollBar ─────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #14142A;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2A2A45;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #00D2D3; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── Frame (DropZone hariç özel stillenmiş) ────────────────────── */
QFrame {
    background-color: #14142A;
    border: 1px dashed #2A2A45;
    border-radius: 6px;
}

/* ── CheckBox ──────────────────────────────────────────────────── */
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #2A2A45;
    border-radius: 4px;
    background: #1A1A2C;
}
QCheckBox::indicator:checked {
    background: #00D2D3;
    border-color: #00FFCC;
}

/* ── Label genel ───────────────────────────────────────────────── */
QLabel {
    background: transparent;
    border: none;
}
"""
