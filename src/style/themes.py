DARK_STYLESHEET = """
    QMainWindow {
        background-color: #0f0f13;
    }
    QWidget {
        color: #f9f9fb;
    }
    QWidget#sidebar {
        background-color: #0f0f13;
        border-right: 1px solid #22222a;
    }
    QWidget#sidebar QPushButton {
        background-color: transparent;
        color: #94a3b8;
        border: none;
        text-align: left;
        padding: 10px 15px;
        font-size: 13px;
        border-radius: 6px;
    }
    QWidget#sidebar QPushButton:hover {
        background-color: #16161a;
        color: #f9f9fb;
    }
    QWidget#sidebar QPushButton#activeMenu {
        background-color: #16161a;
        color: #f9f9fb;
        font-weight: bold;
    }
    QWidget#sidebar QPushButton#secondaryBtn {
        background-color: #4f46e5;
        color: #ffffff;
        border: none;
        text-align: center;
        border-radius: 6px;
    }
    QWidget#sidebar QPushButton#secondaryBtn:hover {
        background-color: #4338ca;
    }
    QStackedWidget {
        background-color: #0f0f13;
    }
    QGroupBox {
        border: 1px solid #22222a;
        border-radius: 8px;
        margin-top: 16px;
        font-weight: bold;
        font-size: 14px;
        background-color: #16161a;
        padding: 15px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        padding: 0 5px;
        color: #f9f9fb;
    }
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #0f0f13;
        border: 1px solid #22222a;
        border-radius: 6px;
        padding: 8px;
        color: #f9f9fb;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #6366f1;
    }
    QPushButton {
        background-color: #16161a;
        color: #f9f9fb;
        border: 1px solid #22222a;
        border-radius: 6px;
        padding: 10px 18px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #22222a;
    }
    QPushButton:pressed {
        background-color: #0f0f13;
    }
    QPushButton#stopBtn {
        background-color: #22222a;
        border: 1px solid #22222a;
        border-radius: 6px;
    }
    QPushButton#stopBtn:hover {
        background-color: #2d2d37;
    }
    QPushButton#secondaryBtn {
        background-color: #4f46e5;
        color: #ffffff;
        border: none;
        border-radius: 6px;
    }
    QPushButton#secondaryBtn:hover {
        background-color: #4338ca;
    }
    QPushButton#clearBtn {
        background-color: #22222a;
        border: 1px solid #22222a;
        border-radius: 6px;
    }
    QPushButton#clearBtn:hover {
        background-color: #2d2d37;
    }
    QTableWidget {
        background-color: #0f0f13;
        border: 1px solid #22222a;
        border-radius: 8px;
        gridline-color: #16161a;
    }
    QTableWidget::item {
        border-bottom: 1px solid #16161a;
        padding: 6px;
    }
    QTableWidget::item:selected {
        background-color: #16161a;
        color: #f9f9fb;
    }
    QHeaderView::section {
        background-color: #16161a;
        color: #94a3b8;
        padding: 8px;
        border: 1px solid #22222a;
        font-weight: bold;
    }
    QScrollBar:vertical {
        border: none;
        background: #0f0f13;
        width: 8px;
    }
    QScrollBar::handle:vertical {
        background: #2d2d37;
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
        background-color: #0b0b0e;
        color: #f9f9fb;
        border: 1px solid #22222a;
        border-radius: 8px;
        padding: 8px;
    }
    QToolTip {
        background-color: #16161a;
        color: #f9f9fb;
        border: 1px solid #22222a;
        border-radius: 4px;
        padding: 5px;
    }
    /* Chat Workspace Styles */
    QFrame#chatLeftPanel {
        background-color: #16161a;
        border: 1px solid #22222a;
        border-radius: 8px;
    }
    QListWidget#chatList {
        background-color: transparent;
        border: none;
    }
    QListWidget#chatList::item {
        border-bottom: 1px solid #0f0f13;
        padding: 5px;
    }
    QListWidget#chatList::item:hover {
        background-color: #22222a;
        border-radius: 6px;
    }
    QListWidget#chatList::item:selected {
        background-color: #22222a;
        border-radius: 6px;
        color: #f9f9fb;
    }
    QFrame#chatRightPanel {
        background-color: #16161a;
        border: 1px solid #22222a;
        border-radius: 8px;
    }
    QFrame#chatRightPlaceholder {
        background-color: #16161a;
        border: 1px solid #22222a;
        border-radius: 8px;
    }
    QWidget#chatHeader {
        background-color: #16161a;
        border-bottom: 1px solid #22222a;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        padding: 10px 15px;
    }
    QWidget#chatHeader QLabel#chatHeaderName {
        color: #f9f9fb;
        font-weight: bold;
    }
    QWidget#chatHeader QLabel#chatHeaderJid {
        color: #94a3b8;
    }
    QLineEdit#chatInput {
        background-color: #0f0f13;
        border: 1px solid #22222a;
        border-radius: 6px;
        padding: 8px 15px;
        color: #f9f9fb;
    }
    QLineEdit#chatInput:focus {
        border: 1px solid #6366f1;
    }
    QPushButton#chatSendBtn {
        background-color: #4f46e5;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }
    QPushButton#chatSendBtn:hover {
        background-color: #4338ca;
    }
    QWidget#chatInputArea {
        background-color: #16161a;
        border-top: 1px solid #22222a;
        border-bottom-left-radius: 7px;
        border-bottom-right-radius: 7px;
        padding: 10px 15px;
    }
    QPushButton#chatAttachBtn {
        background-color: #0f0f13;
        color: #94a3b8;
        border: 1px solid #22222a;
        border-radius: 6px;
        font-size: 16px;
        padding: 0px;
    }
    QPushButton#chatAttachBtn:hover {
        background-color: #16161a;
        color: #6366f1;
        border: 1px solid #6366f1;
    }
    QWidget#chatAttachmentPreview {
        background-color: #16161a;
        border-top: 1px solid #22222a;
    }
    QWidget#chatAttachmentPreview QLabel {
        color: #f9f9fb;
    }
"""

LIGHT_STYLESHEET = """
    QMainWindow {
        background-color: #f8fafc;
    }
    QWidget {
        color: #0f172a;
    }
    QWidget#sidebar {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    QWidget#sidebar QPushButton {
        background-color: transparent;
        color: #64748b;
        border: none;
        text-align: left;
        padding: 10px 15px;
        font-size: 13px;
        border-radius: 6px;
    }
    QWidget#sidebar QPushButton:hover {
        background-color: #f1f5f9;
        color: #0f172a;
    }
    QWidget#sidebar QPushButton#activeMenu {
        background-color: #e2e8f0;
        color: #0f172a;
        font-weight: bold;
    }
    QWidget#sidebar QPushButton#secondaryBtn {
        background-color: #4f46e5;
        color: #ffffff;
        border: none;
        text-align: center;
        border-radius: 6px;
    }
    QWidget#sidebar QPushButton#secondaryBtn:hover {
        background-color: #4338ca;
    }
    QStackedWidget {
        background-color: #f8fafc;
    }
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 16px;
        font-weight: bold;
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
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px;
        color: #0f172a;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #6366f1;
    }
    QPushButton {
        background-color: #f1f5f9;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 10px 18px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #e2e8f0;
    }
    QPushButton:pressed {
        background-color: #cbd5e1;
    }
    QPushButton#stopBtn {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
    QPushButton#stopBtn:hover {
        background-color: #f1f5f9;
    }
    QPushButton#secondaryBtn {
        background-color: #4f46e5;
        color: #ffffff;
        border: none;
        border-radius: 6px;
    }
    QPushButton#secondaryBtn:hover {
        background-color: #4338ca;
    }
    QPushButton#clearBtn {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
    QPushButton#clearBtn:hover {
        background-color: #f1f5f9;
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
        background-color: #e2e8f0;
        color: #0f172a;
    }
    QHeaderView::section {
        background-color: #f8fafc;
        color: #64748b;
        padding: 8px;
        border: 1px solid #e2e8f0;
        font-weight: bold;
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
        background: #64748b;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QPlainTextEdit#logConsole {
        background-color: #f1f5f9;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px;
    }
    QToolTip {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 5px;
    }
    /* Chat Workspace Styles */
    QFrame#chatLeftPanel {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    QListWidget#chatList {
        background-color: transparent;
        border: none;
    }
    QListWidget#chatList::item {
        border-bottom: 1px solid #f1f5f9;
        padding: 5px;
    }
    QListWidget#chatList::item:hover {
        background-color: #f1f5f9;
        border-radius: 6px;
    }
    QListWidget#chatList::item:selected {
        background-color: #e2e8f0;
        border-radius: 6px;
        color: #0f172a;
    }
    QFrame#chatRightPanel {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    QFrame#chatRightPlaceholder {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    QWidget#chatHeader {
        background-color: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        padding: 10px 15px;
    }
    QWidget#chatHeader QLabel#chatHeaderName {
        color: #0f172a;
        font-weight: bold;
    }
    QWidget#chatHeader QLabel#chatHeaderJid {
        color: #64748b;
    }
    QLineEdit#chatInput {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 15px;
        color: #0f172a;
    }
    QLineEdit#chatInput:focus {
        border: 1px solid #6366f1;
    }
    QPushButton#chatSendBtn {
        background-color: #4f46e5;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }
    QPushButton#chatSendBtn:hover {
        background-color: #4338ca;
    }
    QWidget#chatInputArea {
        background-color: #ffffff;
        border-top: 1px solid #e2e8f0;
        border-bottom-left-radius: 7px;
        border-bottom-right-radius: 7px;
        padding: 10px 15px;
    }
    QPushButton#chatAttachBtn {
        background-color: #ffffff;
        color: #64748b;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        font-size: 16px;
        padding: 0px;
    }
    QPushButton#chatAttachBtn:hover {
        background-color: #f1f5f9;
        color: #6366f1;
        border: 1px solid #6366f1;
    }
    QWidget#chatAttachmentPreview {
        background-color: #ffffff;
        border-top: 1px solid #e2e8f0;
    }
    QWidget#chatAttachmentPreview QLabel {
        color: #0f172a;
    }
"""
