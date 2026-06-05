from PySide6.QtCore import Qt, Signal, QDateTime, QPoint
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QMenu

# Import database manager
import db_manager


class ProfileCard(QFrame):
    clicked = Signal(int) # Emits account_id
    rename_clicked = Signal(int, str) # Emits account_id, current_name
    toggle_bot_clicked = Signal(int) # Emits account_id
    
    def __init__(self, account_id, name, phone, session_name, is_connected, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.setObjectName("profileCard")
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        self.avatar = QLabel()
        self.avatar.setObjectName("profileAvatar")
        self.avatar.setFixedSize(70, 70)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFont(QFont("Arial", 28, QFont.Bold))
        initial = name[0].upper() if name else "N"
        self.avatar.setText(initial)
        layout.addWidget(self.avatar, 0, Qt.AlignCenter)
        
        self.name_label = QLabel(name or "New Account")
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("color: #e8ecf1; background: transparent;")
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        phone_label = QLabel(phone or "Not Linked")
        phone_label.setFont(QFont("Arial", 9))
        phone_label.setAlignment(Qt.AlignCenter)
        phone_label.setStyleSheet("color: #8494a7; background: transparent;")
        layout.addWidget(phone_label)
        
        status_label = QLabel("● Connected" if is_connected else "● Disconnected")
        status_label.setFont(QFont("Arial", 9, QFont.Bold))
        status_label.setAlignment(Qt.AlignCenter)
        if is_connected:
            status_label.setStyleSheet("color: #3daa6d; background: transparent;")
        else:
            status_label.setStyleSheet("color: #d4544a; background: transparent;")
        layout.addWidget(status_label)

        # Toggle bot connection button overlay
        bot_icon = "⏹️" if is_connected else "▶️"
        self.toggle_bot_btn = QPushButton(bot_icon, self)
        self.toggle_bot_btn.setFixedSize(24, 24)
        self.toggle_bot_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_bot_btn.setToolTip("Stop Bot Connection" if is_connected else "Start Bot Connection")
        self.toggle_bot_btn.move(8, 8)
        self.toggle_bot_btn.clicked.connect(self.on_toggle_bot_clicked)

        # Rename button overlay
        self.rename_btn = QPushButton("✏️", self)
        self.rename_btn.setFixedSize(24, 24)
        self.rename_btn.setCursor(Qt.PointingHandCursor)
        self.rename_btn.setToolTip("Rename this profile")
        self.rename_btn.move(160 - 24 - 8, 8)
        self.rename_btn.clicked.connect(self.on_rename_clicked)
 
        is_dark = db_manager.get_theme() == "dark"
        self.apply_card_theme(is_dark)

    def on_rename_clicked(self):
        self.rename_clicked.emit(self.account_id, self.name_label.text())

    def on_toggle_bot_clicked(self):
        self.toggle_bot_clicked.emit(self.account_id)

    def apply_card_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QFrame#profileCard {
                    background-color: #1e1e24;
                    border: 1px solid #3f3f46;
                    border-radius: 12px;
                }
                QFrame#profileCard:hover {
                    background-color: #27272a;
                    border-color: #52525b;
                }
                QLabel#profileAvatar {
                    background-color: #27272a;
                    color: #ffffff;
                    border: 1px solid #3f3f46;
                    border-radius: 35px;
                }
            """)
            self.rename_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27272a;
                    border: none;
                    border-radius: 12px;
                    color: #ffffff;
                    font-size: 10px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #3f3f46;
                }
            """)
            self.toggle_bot_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27272a;
                    border: none;
                    border-radius: 12px;
                    color: #ffffff;
                    font-size: 10px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #3f3f46;
                }
            """)
            self.name_label.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        else:
            self.setStyleSheet("""
                QFrame#profileCard {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                }
                QFrame#profileCard:hover {
                    background-color: #f8fafc;
                    border-color: #cbd5e1;
                }
                QLabel#profileAvatar {
                    background-color: #f1f5f9;
                    color: #0f172a;
                    border: 1px solid #e2e8f0;
                    border-radius: 35px;
                }
            """)
            self.rename_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    border: none;
                    border-radius: 12px;
                    color: #0f172a;
                    font-size: 10px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                }
            """)
            self.toggle_bot_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    border: none;
                    border-radius: 12px;
                    color: #0f172a;
                    font-size: 10px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                }
            """)
            self.name_label.setStyleSheet("color: #0f172a; background: transparent; border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.account_id)
        super().mousePressEvent(event)


class AddProfileCard(QFrame):
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("addProfileCard")
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        plus_label = QLabel("＋")
        plus_label.setFont(QFont("Arial", 42, QFont.Bold))
        plus_label.setAlignment(Qt.AlignCenter)
        plus_label.setStyleSheet("color: #8494a7; background: transparent;")
        layout.addWidget(plus_label, 0, Qt.AlignCenter)
        
        text_label = QLabel("Add Profile")
        text_label.setFont(QFont("Arial", 12, QFont.Bold))
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #8494a7; background: transparent;")
        layout.addWidget(text_label)
        
        is_dark = db_manager.get_theme() == "dark"
        self.apply_card_theme(is_dark)

    def apply_card_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QFrame#addProfileCard {
                    background-color: #1e1e24;
                    border: 1px dashed #3f3f46;
                    border-radius: 12px;
                }
                QFrame#addProfileCard:hover {
                    background-color: #27272a;
                    border-color: #52525b;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#addProfileCard {
                    background-color: #ffffff;
                    border: 1px dashed #cbd5e1;
                    border-radius: 12px;
                }
                QFrame#addProfileCard:hover {
                    background-color: #f8fafc;
                    border-color: #94a3b8;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ChatItemWidget(QWidget):
    def __init__(self, chat_name, last_msg, msg_time, is_group=False, parent=None):
        super().__init__(parent)
        self.setObjectName("chatItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        self.avatar = QLabel()
        self.avatar.setObjectName("chatAvatar")
        self.avatar.setFixedSize(40, 40)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFont(QFont("Arial", 14, QFont.Bold))
        
        initial = chat_name[0].upper() if chat_name else "?"
        if is_group:
            self.avatar.setText("👥")
        else:
            self.avatar.setText(initial)
            
        layout.addWidget(self.avatar)
        
        text_widget = QWidget()
        text_widget.setObjectName("chatItemTextWidget")
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        
        header_widget = QWidget()
        header_widget.setObjectName("chatItemHeaderWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.name_label = QLabel(chat_name)
        self.name_label.setObjectName("chatItemName")
        self.name_label.setFont(QFont("Arial", 11, QFont.Bold))
        
        time_str = ""
        if msg_time:
            try:
                dt = QDateTime.fromSecsSinceEpoch(int(msg_time))
                now = QDateTime.currentDateTime()
                if dt.date() == now.date():
                    time_str = dt.toString("HH:mm")
                else:
                    time_str = dt.toString("dd/MM")
            except Exception:
                time_str = str(msg_time)
                
        self.time_label = QLabel(time_str)
        self.time_label.setObjectName("chatItemTime")
        self.time_label.setFont(QFont("Arial", 9))
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        header_layout.addWidget(self.name_label, 1)
        header_layout.addWidget(self.time_label)
        text_layout.addWidget(header_widget)
        
        preview_text = last_msg[:40] + "..." if last_msg and len(last_msg) > 40 else (last_msg or "")
        self.preview_label = QLabel(preview_text)
        self.preview_label.setObjectName("chatItemPreview")
        self.preview_label.setFont(QFont("Arial", 9))
        text_layout.addWidget(self.preview_label)
        
        layout.addWidget(text_widget, 1)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def setSelected(self, selected):
        sel_val = "true" if selected else "false"
        self.setProperty("selected", sel_val)
        self.avatar.setProperty("selected", sel_val)
        self.name_label.setProperty("selected", sel_val)
        self.time_label.setProperty("selected", sel_val)
        self.preview_label.setProperty("selected", sel_val)
        
        # Polish/unpolish to refresh stylesheet
        self.style().unpolish(self)
        self.style().polish(self)
        self.avatar.style().unpolish(self.avatar)
        self.avatar.style().polish(self.avatar)
        self.name_label.style().unpolish(self.name_label)
        self.name_label.style().polish(self.name_label)
        self.time_label.style().unpolish(self.time_label)
        self.time_label.style().polish(self.time_label)
        self.preview_label.style().unpolish(self.preview_label)
        self.preview_label.style().polish(self.preview_label)


class MessageRowWidget(QWidget):
    """
    Wraps a chat bubble with a hover-revealed pencil action button.
    The pencil appears on the opposite side of the bubble (left for outgoing, right for incoming).
    """
    def __init__(self, bubble_frame, is_from_me, msg_data, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.msg_data = msg_data  # dict with db_id, message_id, chat_jid, message_text, is_from_me
        self.is_from_me = is_from_me
        
        self.setMouseTracking(True)
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        
        if is_from_me:
            is_dark = db_manager.get_theme() == "dark"
            btn_bg = "#22222a" if is_dark else "#e2e8f0"
            btn_hover = "#2d2d37" if is_dark else "#cbd5e1"
            btn_fg = "#94a3b8" if is_dark else "#64748b"
            
            self.action_btn = QPushButton("✏️")
            self.action_btn.setFixedSize(28, 28)
            self.action_btn.setCursor(Qt.PointingHandCursor)
            self.action_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_bg};
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    color: {btn_fg};
                }}
                QPushButton:hover {{
                    background-color: {btn_hover};
                }}
            """)
            self.action_btn.setVisible(False)
            self.action_btn.clicked.connect(self._show_menu)
            
            row_layout.addStretch()
            row_layout.addWidget(self.action_btn, 0, Qt.AlignVCenter)
            row_layout.addWidget(bubble_frame)
            bubble_frame.setMaximumWidth(450)
        else:
            self.action_btn = None
            row_layout.addWidget(bubble_frame)
            row_layout.addStretch()
            bubble_frame.setMaximumWidth(450)
    
    def enterEvent(self, event):
        if self.action_btn:
            self.action_btn.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if self.action_btn:
            from PySide6.QtGui import QCursor
            if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
                self.action_btn.setVisible(False)
        super().leaveEvent(event)
    
    def _show_menu(self):
        is_dark = db_manager.get_theme() == "dark"
        menu_bg = "#16161a" if is_dark else "#ffffff"
        menu_fg = "#f9f9fb" if is_dark else "#0f172a"
        menu_border = "#22222a" if is_dark else "#e2e8f0"
        menu_hover = "#22222a" if is_dark else "#f1f5f9"
        danger_color = "#d4544a"
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_fg};
                border: 1px solid {menu_border};
                border-radius: 8px;
                padding: 4px 0px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {menu_hover};
            }}
        """)
        
        edit_action = menu.addAction("✏️  Edit Message")
        delete_action = menu.addAction("🗑️  Delete Message")
        
        # Style the delete action with red color
        delete_action.setData("delete")
        
        action = menu.exec(self.action_btn.mapToGlobal(QPoint(0, self.action_btn.height())))
        
        if action == edit_action:
            self.main_window.edit_chat_message(
                self.msg_data["db_id"],
                self.msg_data["message_id"],
                self.msg_data["chat_jid"],
                self.msg_data["message_text"],
                self.msg_data["is_from_me"]
            )
        elif action == delete_action:
            self.main_window.delete_chat_message(
                self.msg_data["db_id"],
                self.msg_data["message_id"],
                self.msg_data["chat_jid"],
                self.msg_data["is_from_me"]
            )
