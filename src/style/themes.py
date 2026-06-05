LIGHT_STYLESHEET = """
    QMainWindow {
        background-color: #ffffff;
    }
    QWidget {
        color: #0f172a;
        font-family: 'Poppins', 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    QWidget#sidebar {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    QWidget#sidebar QPushButton {
        background-color: transparent;
        color: #475569;
        border: none;
        text-align: left;
        padding: 10px 15px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 8px;
        text-transform: uppercase;
        margin: 2px 8px;
    }
    QWidget#sidebar QPushButton:hover {
        background-color: #f1f5f9;
        color: #0f172a;
    }
    QWidget#sidebar QPushButton#activeMenu {
        background-color: #0f172a;
        color: #ffffff;
        font-weight: 700;
        border: none;
    }
    QWidget#sidebar QPushButton#secondaryBtn {
        background-color: #0f172a;
        color: #ffffff;
        border: none;
        text-align: center;
        border-radius: 8px;
        margin: 5px 8px;
    }
    QWidget#sidebar QPushButton#secondaryBtn:hover {
        background-color: #1e293b;
        color: #ffffff;
    }
    QStackedWidget {
        background-color: #ffffff;
    }
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-top: 16px;
        font-weight: 700;
        font-size: 14px;
        background-color: #ffffff;
        padding: 15px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        padding: 0 5px;
        color: #0f172a;
    }
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px;
        color: #0f172a;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
        background-color: #ffffff;
        border: 1px solid #2563eb;
    }
    QPushButton {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 700;
        font-size: 13px;
        text-transform: uppercase;
    }
    QPushButton:hover {
        background-color: #f8fafc;
        border-color: #94a3b8;
    }
    QPushButton:pressed {
        background-color: #f1f5f9;
        border-color: #cbd5e1;
    }
    QPushButton#stopBtn {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #0f172a;
    }
    QPushButton#stopBtn:hover {
        background-color: #e2e8f0;
    }
    QPushButton#secondaryBtn {
        background-color: #0f172a;
        color: #ffffff;
        border: none;
        border-radius: 8px;
    }
    QPushButton#secondaryBtn:hover {
        background-color: #1e293b;
        color: #ffffff;
    }
    QPushButton#secondaryBtn:pressed {
        background-color: #334155;
    }
    QPushButton#dangerBtn {
        background-color: #ef4444;
        color: #ffffff;
        border: none;
        border-radius: 8px;
    }
    QPushButton#dangerBtn:hover {
        background-color: #dc2626;
        color: #ffffff;
    }
    QPushButton#clearBtn {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #0f172a;
    }
    QPushButton#clearBtn:hover {
        background-color: #f8fafc;
        border-color: #94a3b8;
    }
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        gridline-color: #f1f5f9;
    }
    QTableWidget::item {
        border-bottom: 1px solid #f1f5f9;
        padding: 6px;
    }
    QTableWidget::item:selected {
        background-color: #f1f5f9;
        color: #0f172a;
        font-weight: normal;
    }
    QHeaderView::section {
        background-color: #f8fafc;
        color: #475569;
        padding: 8px;
        border: none;
        border-bottom: 1px solid #e2e8f0;
        font-weight: 700;
        border-radius: 0px;
    }
    QScrollBar:vertical {
        border: none;
        background: #f8fafc;
        width: 8px;
    }
    QScrollBar::handle:vertical {
        background: #cbd5e1;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QPlainTextEdit#logConsole {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px;
        font-family: 'Courier New', Courier, monospace;
    }
    QToolTip {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 5px;
    }
    /* Chat Workspace Styles */
    QFrame#chatLeftPanel {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    QListWidget#chatList {
        background-color: transparent;
        border: none;
    }
    QListWidget#chatList::item {
        border-bottom: none;
        padding: 8px;
        border-radius: 8px;
        margin: 2px 4px;
    }
    QListWidget#chatList::item:hover {
        background-color: #f1f5f9;
    }
    QListWidget#chatList::item:selected {
        background-color: #0f172a;
    }
    QWidget#chatItem {
        background-color: transparent;
    }
    QWidget#chatItem[selected="true"] {
        background-color: #0f172a;
    }
    QWidget#chatItemTextWidget, QWidget#chatItemHeaderWidget {
        background: transparent;
    }
    QLabel#chatAvatar {
        background-color: #f1f5f9;
        color: #0f172a;
        border: none;
        border-radius: 20px;
    }
    QLabel#chatAvatar[selected="true"] {
        background-color: #ffffff;
        color: #0f172a;
        border: none;
    }
    QLabel#chatItemName {
        color: #0f172a;
        font-weight: bold;
        background: transparent;
    }
    QLabel#chatItemName[selected="true"] {
        color: #ffffff;
    }
    QLabel#chatItemTime {
        color: #64748b;
        background: transparent;
    }
    QLabel#chatItemTime[selected="true"] {
        color: #cbd5e1;
    }
    QLabel#chatItemPreview {
        color: #64748b;
        background: transparent;
    }
    QLabel#chatItemPreview[selected="true"] {
        color: #cbd5e1;
    }
    QFrame#chatRightPanel {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    QFrame#chatRightPlaceholder {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    QWidget#chatHeader {
        background-color: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        padding: 10px 15px;
    }
    QWidget#chatHeader QLabel#chatHeaderName {
        color: #0f172a;
        font-weight: 700;
    }
    QWidget#chatHeader QLabel#chatHeaderJid {
        color: #64748b;
        font-family: 'Courier New', Courier, monospace;
    }
    QLineEdit#chatInput {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px 15px;
        color: #0f172a;
    }
    QLineEdit#chatInput:focus {
        background-color: #ffffff;
        border: 1px solid #2563eb;
    }
    QPushButton#chatSendBtn {
        background-color: #0f172a;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 700;
    }
    QPushButton#chatSendBtn:hover {
        background-color: #1e293b;
        color: #ffffff;
    }
    QWidget#chatInputArea {
        background-color: #f8fafc;
        border-top: 1px solid #e2e8f0;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        padding: 10px 15px;
    }
    QPushButton#chatAttachBtn {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        font-size: 16px;
        padding: 0px;
    }
    QPushButton#chatAttachBtn:hover {
        background-color: #f8fafc;
        border-color: #94a3b8;
    }
    QWidget#chatAttachmentPreview {
        background-color: #f8fafc;
        border-top: 1px solid #e2e8f0;
    }
    QWidget#chatAttachmentPreview QLabel {
        color: #0f172a;
    }
"""

DARK_STYLESHEET = LIGHT_STYLESHEET
