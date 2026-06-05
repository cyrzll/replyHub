import os
import sys
import io
import time
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QDateTime, QPoint, QTimer
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QGroupBox, QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSplitter, QStackedWidget,
    QDialog, QMenu, QScrollArea, QFrame, QListWidget, QListWidgetItem, QCheckBox, QComboBox, QProgressBar
)
import segno

# Import database manager
import db_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# Constants
PROJECT_DIR = Path(__file__).resolve().parent
SESSION_DIR = PROJECT_DIR / "src" / "data" / "session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
# Load stylesheet themes
from src.style.themes import DARK_STYLESHEET, LIGHT_STYLESHEET

from src.hooks.bot_thread import BotThread
from src.lib.jid_helper import parse_jid
from src.lib.widgets import ProfileCard, AddProfileCard, ChatItemWidget, MessageRowWidget
from src.lib.dialogs import AddAccountDialog, ScanQRDialog, NewChatDialog, EditMessageDialog, ProductDialog

DEFAULT_GEMINI_INSTRUCTION = """Kamu adalah bot Customer Service (CS) toko online yang ramah dan santai (panggil pelanggan dengan "kak").
Tugas kamu adalah membantu menjawab pertanyaan seputar produk kami, harga, stok, pemesanan, pembayaran, pengiriman, dan foto produk.

Sinonim/Sebutan Produk:
- 'Kaos Oversize' sering disebut: kaos, baju, atasan.
- 'celana dalam' sering disebut: celana, cd, bawahan.

Aturan Utama:
1. Hanya gunakan data katalog produk di bawah ini. Jangan mengarang informasi.
2. Ketika pelanggan menanyakan daftar produk atau bertanya "ada produk apa saja", berikan daftar nama produk dan harganya secara ramah.
3. PENTING UNTUK FOTO/GAMBAR: Jika pelanggan meminta foto, gambar, detail, deskripsi, atau ingin melihat produk (contoh: "lihat foto kaos", "fotonya?", "bisa lihat kaos nya?"), kamu WAJIB menuliskan detail produk tersebut secara lengkap, lalu di bagian akhir jawabanmu wajib sertakan tag {{SEND_IMAGE: <id_produk>}} secara persis. Jangan pernah berkata tidak bisa mengirim foto!

Katalog Produk:
{{products}}"""


class MainWindow(QMainWindow):
    chat_message_saved_signal = Signal(int, str) # Emits account_id, chat_jid

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReplyHub - WhatsApp Auto Reply Bot")
        self.resize(1100, 700)
        
        # State variables
        self.bot_threads = {}        # Key: account_id (int), Value: BotThread
        self.stopping_threads = []   # List of BotThread objects currently shutting down
        self.account_logs = {}       # Key: account_id (int), Value: List of HTML logs
        self.selected_account_id = None
        self.current_editing_rule_id = None
        self.selected_chat_jid = None # Active chat JID reference

        # Connect signals
        self.chat_message_saved_signal.connect(self.on_chat_message_saved)

        # Main Central Stack Widget
        self.app_stack = QStackedWidget()
        self.setCentralWidget(self.app_stack)
        
        # 1. Setup Netflix-Style Launcher Widget
        self.setup_launcher_widget()
        
        # 2. Setup Main Workspace Widget
        self.setup_workspace_widget()
        
        # Load theme & profiles launcher
        self.load_launcher_profiles()
        self.apply_theme(db_manager.get_theme())
        
        # Set default stack page (Launcher Screen)
        self.app_stack.setCurrentIndex(0)

        # Auto-start previously connected bots
        self.auto_start_active_accounts()

    def get_sender_color(self, sender_name, is_dark):
        if not sender_name or sender_name == "WhatsApp User":
            return "#3daa6d" if is_dark else "#2d8f5c"
        
        if is_dark:
            colors = [
                "#4a9eed",  # Sky Blue
                "#d4a03a",  # Amber
                "#3daa6d",  # Green
                "#9b7ad8",  # Lavender
                "#d4544a",  # Coral
                "#5aafb8",  # Teal
                "#c9884a",  # Bronze
                "#7a9ed4",  # Soft Blue
            ]
        else:
            colors = [
                "#2b7de9",  # Blue
                "#c2912a",  # Amber
                "#2d8f5c",  # Green
                "#7b5cb0",  # Purple
                "#c0392b",  # Red
                "#1a8a94",  # Teal
                "#a87032",  # Brown
                "#4a78b5",  # Steel Blue
            ]
            
        val = sum(ord(c) for c in sender_name)
        return colors[val % len(colors)]

    def setup_launcher_widget(self):
        self.launcher_widget = QWidget()
        launcher_layout = QVBoxLayout(self.launcher_widget)
        launcher_layout.setContentsMargins(40, 40, 40, 40)
        
        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(10)
        
        self.launcher_title = QLabel("ReplyHub")
        self.launcher_title.setFont(QFont("Arial", 36, QFont.Bold))
        self.launcher_title.setAlignment(Qt.AlignCenter)
        
        self.launcher_subtitle = QLabel("Choose a profile to manage auto-reply bot")
        self.launcher_subtitle.setFont(QFont("Arial", 14))
        self.launcher_subtitle.setStyleSheet("color: #8494a7;")
        self.launcher_subtitle.setAlignment(Qt.AlignCenter)
        
        center_layout.addWidget(self.launcher_title)
        center_layout.addWidget(self.launcher_subtitle)
        center_layout.addSpacing(10)
        
        # Bulk Activate Buttons Layout
        bulk_layout = QHBoxLayout()
        bulk_layout.setAlignment(Qt.AlignCenter)
        bulk_layout.setSpacing(15)
        
        self.activate_all_btn = QPushButton("⚡ Activate All Bots")
        self.activate_all_btn.setObjectName("secondaryBtn")
        self.activate_all_btn.setFixedSize(160, 40)
        self.activate_all_btn.setToolTip("Start connection for all linked accounts")
        self.activate_all_btn.clicked.connect(self.activate_all_bots)
        
        self.deactivate_all_btn = QPushButton("🔌 Deactivate All Bots")
        self.deactivate_all_btn.setObjectName("clearBtn")
        self.deactivate_all_btn.setFixedSize(160, 40)
        self.deactivate_all_btn.setToolTip("Stop connection for all running bots")
        self.deactivate_all_btn.clicked.connect(self.deactivate_all_bots)
        
        bulk_layout.addWidget(self.activate_all_btn)
        bulk_layout.addWidget(self.deactivate_all_btn)
        center_layout.addLayout(bulk_layout)
        
        center_layout.addSpacing(30)
        
        # Scroll Area for Profile Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setFixedHeight(230)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.profiles_layout = QHBoxLayout(scroll_content)
        self.profiles_layout.setAlignment(Qt.AlignCenter)
        self.profiles_layout.setSpacing(25)
        
        scroll.setWidget(scroll_content)
        center_layout.addWidget(scroll)
        
        center_layout.addSpacing(30)
        
        launcher_layout.addStretch()
        launcher_layout.addWidget(center_widget)
        launcher_layout.addStretch()
        
        self.app_stack.addWidget(self.launcher_widget)

    def load_launcher_profiles(self):
        # Clear existing layout
        while self.profiles_layout.count():
            child = self.profiles_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            acc_id, phone, name, session_name, _ = acc
            thread = self.bot_threads.get(acc_id)
            is_connected = (thread is not None and thread.isRunning() and thread.client and thread.client.connected)
            
            card = ProfileCard(acc_id, name or "New Account", phone, session_name, is_connected)
            card.clicked.connect(self.select_profile_and_enter_workspace)
            card.rename_clicked.connect(self.rename_profile_dialog)
            card.toggle_bot_clicked.connect(self.toggle_bot_for_account_from_launcher)
            self.profiles_layout.addWidget(card)
            
        # Add "+" Profile Card
        add_card = AddProfileCard()
        add_card.clicked.connect(self.add_new_account_via_dialog)
        self.profiles_layout.addWidget(add_card)

    def toggle_bot_for_account_from_launcher(self, account_id):
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            if acc[0] == account_id:
                session_name = acc[3]
                self.toggle_bot_for_account(account_id, session_name)
                break

    def activate_all_bots(self):
        accounts = db_manager.get_all_accounts()
        activated_count = 0
        for acc in accounts:
            acc_id, phone, name, session_name, _ = acc
            if phone:  # only auto-start already linked/authenticated accounts
                thread = self.bot_threads.get(acc_id)
                if not thread or not thread.isRunning():
                    self.start_bot_for_account(acc_id, session_name)
                    activated_count += 1
        if activated_count > 0:
            self.load_launcher_profiles()
            self.update_active_profile_widget()
            self.update_page_visibility()

    def deactivate_all_bots(self):
        deactivated_count = 0
        for acc_id in list(self.bot_threads.keys()):
            self.stop_bot_thread(acc_id)
            deactivated_count += 1
        if deactivated_count > 0:
            self.load_launcher_profiles()
            self.update_active_profile_widget()
            self.update_page_visibility()

    def setup_workspace_widget(self):
        self.workspace_widget = QWidget()
        layout = QHBoxLayout(self.workspace_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left Sidebar Panel
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 25)
        sidebar_layout.setSpacing(10)

        # Logo / Branding
        self.logo_label = QLabel("ReplyHub")
        self.logo_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.logo_label.setStyleSheet("padding-bottom: 12px; border-bottom: 1px solid #2d3548;")
        sidebar_layout.addWidget(self.logo_label)

        # Status indicator pill
        self.status_pill = QLabel()
        self.status_pill.setAlignment(Qt.AlignCenter)
        self.status_pill.setToolTip("Currently selected account status indicator")
        sidebar_layout.addWidget(self.status_pill)

        # Navigation Menu Buttons
        self.menu_status_btn = QPushButton("🤖 Bot Status & Logs")
        self.menu_status_btn.clicked.connect(lambda: self.switch_page(0))
        self.menu_status_btn.setToolTip("Check connection status, QR code, and real-time logs")
        
        self.menu_chat_btn = QPushButton("💬 Chat Workspace")
        self.menu_chat_btn.clicked.connect(lambda: self.switch_page(1))
        self.menu_chat_btn.setToolTip("View all WhatsApp chats, send messages, and view attachments")
        
        self.menu_rules_btn = QPushButton("📝 Auto-Reply Rules")
        self.menu_rules_btn.clicked.connect(lambda: self.switch_page(2))
        self.menu_rules_btn.setToolTip("Create and edit auto-reply rules for the active account")

        self.menu_gemini_btn = QPushButton("✨ Gemini AI")
        self.menu_gemini_btn.clicked.connect(lambda: self.switch_page(3))
        self.menu_gemini_btn.setToolTip("Configure Gemini AI Auto-Responder settings")

        self.menu_products_btn = QPushButton("🛍️ Manage Products")
        self.menu_products_btn.clicked.connect(lambda: self.switch_page(4))
        self.menu_products_btn.setToolTip("Manage product catalog, categories, gender, and discounts")

        sidebar_layout.addWidget(self.menu_status_btn)
        sidebar_layout.addWidget(self.menu_chat_btn)
        sidebar_layout.addWidget(self.menu_rules_btn)
        sidebar_layout.addWidget(self.menu_gemini_btn)
        sidebar_layout.addWidget(self.menu_products_btn)
        sidebar_layout.addStretch()

        # Active Profile switcher widget
        self.profile_btn = QPushButton()
        self.profile_btn.setObjectName("profileSwitcherBtn")
        self.profile_btn.setFixedHeight(55)
        self.profile_btn.setToolTip("Click to switch account, delete account or link a new one")
        
        profile_layout = QHBoxLayout(self.profile_btn)
        profile_layout.setContentsMargins(10, 5, 10, 5)
        profile_layout.setSpacing(8)
        
        self.profile_status_dot = QLabel("●")
        self.profile_status_dot.setStyleSheet("color: #8494a7; font-size: 14px;")
        self.profile_status_dot.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        info_widget = QWidget()
        info_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(1)
        
        self.profile_name_label = QLabel("No Account")
        self.profile_name_label.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.profile_phone_label = QLabel("Click to select")
        self.profile_phone_label.setFont(QFont("Arial", 9))
        
        info_layout.addWidget(self.profile_name_label)
        info_layout.addWidget(self.profile_phone_label)
        
        chevron = QLabel("▼")
        chevron.setStyleSheet("color: #8494a7; font-size: 10px;")
        chevron.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        profile_layout.addWidget(self.profile_status_dot)
        profile_layout.addWidget(info_widget, 1)
        profile_layout.addWidget(chevron)
        
        self.profile_btn.clicked.connect(self.show_account_switcher_menu)
        sidebar_layout.addWidget(self.profile_btn)
        sidebar_layout.addSpacing(5)

        sidebar_layout.addSpacing(5)

        layout.addWidget(self.sidebar)

        # Right Stacked Content area
        self.workspace_stack = QStackedWidget()
        layout.addWidget(self.workspace_stack)

        # Setup Stack Pages
        self.setup_bot_control_page()
        self.setup_chat_page()
        self.setup_rules_page()
        self.setup_gemini_page()
        self.setup_products_page()

        self.app_stack.addWidget(self.workspace_widget)

    def select_profile_and_enter_workspace(self, account_id):
        self.selected_account_id = account_id
        self.selected_chat_jid = None # Reset selected chat workspace selection
        
        # Hide conversation area until a contact is clicked
        if hasattr(self, "chat_convo_widget"):
            self.chat_convo_widget.setVisible(False)
        if hasattr(self, "chat_placeholder_right"):
            self.chat_placeholder_right.setVisible(True)
            
        self.update_active_profile_widget()
        self.update_page_visibility()
        self.update_log_console_view()
        self.load_rules_into_table()
        
        # Switch app stack to Workspace
        self.app_stack.setCurrentIndex(1)
        self.switch_page(0)

    def add_new_account_via_dialog(self):
        dialog = AddAccountDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_launcher_profiles()
            if dialog.account_id:
                self.select_profile_and_enter_workspace(dialog.account_id)

    def rename_profile_dialog(self, account_id, current_name):
        from PySide6.QtWidgets import QInputDialog
        
        is_dark = db_manager.get_theme() == "dark"
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rename Profile")
        dialog.setLabelText(f"Enter new name for '{current_name}':")
        dialog.setTextValue(current_name)
        
        if is_dark:
            dialog.setStyleSheet("""
                QInputDialog { background-color: #1e1e24; border: 1px solid #3f3f46; border-radius: 12px; }
                QLabel { color: #ffffff; font-size: 13px; font-family: 'Poppins'; }
                QLineEdit { background-color: #27272a; border: 1px solid #3f3f46; border-radius: 8px; padding: 6px; color: #ffffff; }
                QPushButton { background-color: #ffffff; color: #000000; border: none; border-radius: 8px; padding: 6px 12px; font-weight: bold; }
                QPushButton:hover { background-color: #e2e8f0; }
            """)
        else:
            dialog.setStyleSheet("""
                QInputDialog { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; }
                QLabel { color: #0f172a; font-size: 13px; font-family: 'Poppins'; }
                QLineEdit { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px; color: #0f172a; }
                QPushButton { background-color: #0f172a; color: #ffffff; border: none; border-radius: 8px; padding: 6px 12px; font-weight: bold; }
                QPushButton:hover { background-color: #1e293b; }
            """)
            
        if dialog.exec() == QInputDialog.Accepted:
            new_name = dialog.textValue().strip()
            if new_name:
                db_manager.update_profile_name(account_id, new_name)
                self.load_launcher_profiles()
                self.update_active_profile_widget()
                self.update_page_visibility()

    def go_to_launcher(self):
        self.selected_account_id = None
        self.load_launcher_profiles()
        self.app_stack.setCurrentIndex(0)

    def show_account_switcher_menu(self):
        menu = QMenu(self)
        is_dark = db_manager.get_theme() == "dark"
        if is_dark:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #16161a;
                    border: 1px solid #22222a;
                    border-radius: 6px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 24px;
                    border-radius: 4px;
                    color: #f9f9fb;
                }
                QMenu::item:selected {
                    background-color: #22222a;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #22222a;
                    margin: 4px 0px;
                }
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 24px;
                    border-radius: 4px;
                    color: #0f172a;
                }
                QMenu::item:selected {
                    background-color: #f1f5f9;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #e2e8f0;
                    margin: 4px 0px;
                }
            """)

        header_action = menu.addAction("Switch Account:")
        header_action.setEnabled(False)

        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            acc_id, phone, name, session_name, _ = acc
            display_name = name or "New Account"
            if phone:
                display_name += f" ({phone})"
            
            thread = self.bot_threads.get(acc_id)
            status_indicator = "● " if (thread and thread.isRunning() and thread.client and thread.client.connected) else "○ "
            
            action_text = f"{status_indicator}{display_name}"
            if acc_id == self.selected_account_id:
                action_text = f"✓ {action_text} (Current)"
                
            act = menu.addAction(action_text)
            if acc_id == self.selected_account_id:
                act.setEnabled(False)
            else:
                act.triggered.connect(lambda _, a_id=acc_id: self.select_profile_and_enter_workspace(a_id))

        menu.addSeparator()

        if self.selected_account_id is not None:
            # Find active session name
            session_name = None
            for acc in accounts:
                if acc[0] == self.selected_account_id:
                    session_name = acc[3]
                    break
            
            thread = self.bot_threads.get(self.selected_account_id)
            is_running = (thread is not None and thread.isRunning())
            
            if is_running:
                toggle_act = menu.addAction("🔌 Stop Active Bot")
            else:
                toggle_act = menu.addAction("🤖 Start Active Bot")
            
            if session_name:
                toggle_act.triggered.connect(lambda _, a_id=self.selected_account_id, s_name=session_name: self.toggle_bot_for_account(a_id, s_name))
        
        menu.addSeparator()

        add_act = menu.addAction("➕ Link New Account...")
        add_act.triggered.connect(self.add_new_account_via_dialog)

        launcher_act = menu.addAction("🚪 Show Launcher Screen")
        launcher_act.triggered.connect(self.go_to_launcher)

        if self.selected_account_id is not None:
            del_act = menu.addAction("🗑️ Delete Current Account...")
            del_act.triggered.connect(lambda: self.delete_account_record(self.selected_account_id))

        button_pos = self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomLeft())
        menu.exec(button_pos - QPoint(0, menu.sizeHint().height() + 5))

    def auto_start_active_accounts(self):
        """Finds all accounts that have successfully linked before and connects them."""
        for acc in db_manager.get_all_accounts():
            acc_id, phone, name, session_name, _ = acc
            if phone:  # A linked account will have a phone number saved
                self.start_bot_for_account(acc_id, session_name)

    def switch_page(self, index):
        """Switches the right-hand stacked widget page and highlights the active menu."""
        self.workspace_stack.setCurrentIndex(index)
        
        # Reset object names
        self.menu_status_btn.setObjectName("")
        self.menu_chat_btn.setObjectName("")
        self.menu_rules_btn.setObjectName("")
        self.menu_gemini_btn.setObjectName("")
        self.menu_products_btn.setObjectName("")
        
        # Set active name
        if index == 0:
            self.menu_status_btn.setObjectName("activeMenu")
        elif index == 1:
            self.menu_chat_btn.setObjectName("activeMenu")
        elif index == 2:
            self.menu_rules_btn.setObjectName("activeMenu")
        elif index == 3:
            self.menu_gemini_btn.setObjectName("activeMenu")
        elif index == 4:
            self.menu_products_btn.setObjectName("activeMenu")
            
        # Re-apply stylesheet to force refresh menu button styling
        self.setStyleSheet(self.styleSheet())
        
        # Update visibility and views
        self.update_page_visibility()

    def update_page_visibility(self):
        """Hides page controls if no account is selected, showing launcher screen instead."""
        has_selection = (self.selected_account_id is not None)
        
        if not has_selection:
            self.go_to_launcher()
            return
            
        # Status/Log Page Placeholder Toggle
        self.control_placeholder.setVisible(False)
        self.control_main_widget.setVisible(True)
        
        # Chat Page Placeholder Toggle
        if hasattr(self, "chat_placeholder") and hasattr(self, "chat_main_widget"):
            self.chat_placeholder.setVisible(False)
            self.chat_main_widget.setVisible(True)
            self.load_chats_list()
        
        # Rules Page Placeholder Toggle
        self.rules_placeholder.setVisible(False)
        self.rules_main_widget.setVisible(True)
        
        # Gemini Page Placeholder Toggle
        if hasattr(self, "gemini_placeholder") and hasattr(self, "gemini_main_widget"):
            self.gemini_placeholder.setVisible(False)
            self.gemini_main_widget.setVisible(True)
            self.load_gemini_settings()
            
        # Products Page Placeholder Toggle
        if hasattr(self, "products_placeholder") and hasattr(self, "products_main_widget"):
            self.products_placeholder.setVisible(False)
            self.products_main_widget.setVisible(True)
            self.load_products_into_table()
        
        # Update titles with selected account name
        display_name = self.get_selected_account_display_name()
        self.log_group.setTitle(f"Live Activity Log ({display_name})")
        self.rules_group.setTitle(f"Rules for {display_name}")
        if hasattr(self, "gemini_group"):
            self.gemini_group.setTitle(f"Gemini AI Settings for {display_name}")
        if hasattr(self, "products_group"):
            self.products_group.setTitle(f"Products for {display_name}")
        
        # Reload rules list & logs
        self.load_rules_into_table()
        self.update_log_console_view()
        self.update_active_profile_widget()

        # Update logs tab status controls
        thread = self.bot_threads.get(self.selected_account_id)
        if thread and thread.isRunning():
            if thread.client and thread.client.connected:
                self.tab_status_label.setText("Status: Connected")
                self.tab_status_label.setStyleSheet("color: #3daa6d;")
                self.tab_toggle_btn.setText("Stop Bot")
                self.tab_toggle_btn.setObjectName("stopBtn")
            else:
                self.tab_status_label.setText("Status: Connecting...")
                self.tab_status_label.setStyleSheet("color: #d4a03a;")
                self.tab_toggle_btn.setText("Stop Bot")
                self.tab_toggle_btn.setObjectName("stopBtn")
        else:
            self.tab_status_label.setText("Status: Disconnected")
            self.tab_status_label.setStyleSheet("color: #d4544a;")
            self.tab_toggle_btn.setText("Start Bot")
            self.tab_toggle_btn.setObjectName("secondaryBtn")
            
        self.tab_toggle_btn.style().unpolish(self.tab_toggle_btn)
        self.tab_toggle_btn.style().polish(self.tab_toggle_btn)

    def get_selected_account_display_name(self) -> str:
        """Helper to get a display name for the currently selected account."""
        if self.selected_account_id is None:
            return "No Account Selected"
        for acc in db_manager.get_all_accounts():
            if acc[0] == self.selected_account_id:
                name = acc[2] or "New Account"
                phone = acc[1] or "Not Linked"
                return f"{name} ({phone})"
        return "Unknown Account"

    def toggle_bot_for_account(self, account_id, session_name):
        """Starts or stops the bot background thread for the specified account."""
        thread = self.bot_threads.get(account_id)
        if thread and thread.isRunning():
            self.log_activity(account_id, "🔄 Disconnecting account bot...")
            self.stop_bot_thread(account_id)
        else:
            self.start_bot_for_account(account_id, session_name)
            self.log_activity(account_id, "🔄 Starting account bot connection...")
        
        if self.app_stack.currentIndex() == 0:
            self.load_launcher_profiles()
        self.update_active_profile_widget()
        self.update_page_visibility()

    def delete_account_record(self, account_id):
        """Deletes the account entry, its rules, its session file, and stops thread."""
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete WhatsApp Account ID {account_id}? "
            "This will delete its session credentials and all its auto-reply rules.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            # Stop thread if running and clean up references
            self.stop_bot_thread(account_id, logout=True)
                
            # Remove logs
            if account_id in self.account_logs:
                del self.account_logs[account_id]

            # Delete from DB
            db_manager.delete_account(account_id)
            
            if self.selected_account_id == account_id:
                self.selected_account_id = None
                
            if self.app_stack.currentIndex() == 0:
                self.load_launcher_profiles()
            self.update_active_profile_widget()
            self.update_page_visibility()

    def update_active_profile_widget(self):
        """Updates the active account display in the sidebar footer."""
        if self.selected_account_id is None:
            self.profile_name_label.setText("No Account")
            self.profile_phone_label.setText("Click to select")
            self.profile_status_dot.setStyleSheet("color: #8494a7; font-size: 14px;")
            return

        for acc in db_manager.get_all_accounts():
            if acc[0] == self.selected_account_id:
                name = acc[2] or "New Account"
                phone = acc[1] or "Not Linked"
                self.profile_name_label.setText(name)
                self.profile_phone_label.setText(phone)
                
                thread = self.bot_threads.get(self.selected_account_id)
                if thread and thread.isRunning():
                    if thread.client and thread.client.connected:
                        self.profile_status_dot.setStyleSheet("color: #3daa6d; font-size: 14px;") # green
                    else:
                        self.profile_status_dot.setStyleSheet("color: #d4a03a; font-size: 14px;") # amber
                else:
                    self.profile_status_dot.setStyleSheet("color: #d4544a; font-size: 14px;") # red
                break


    # ==========================================
    # PAGE 2: BOT CONTROL & LOGS VIEW
    # ==========================================
    def setup_bot_control_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder: shown when no account is selected
        self.control_placeholder = QLabel("Select or add a WhatsApp account from the Accounts page first.")
        self.control_placeholder.setAlignment(Qt.AlignCenter)
        self.control_placeholder.setStyleSheet("font-size: 15px; font-weight: bold; font-family: 'Poppins';")
        layout.addWidget(self.control_placeholder)

        # Main active widget
        self.control_main_widget = QWidget()
        control_layout = QVBoxLayout(self.control_main_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_group = QGroupBox("Live Activity Log")
        log_layout = QVBoxLayout(self.log_group)

        # Status header layout on log page
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        self.tab_status_label = QLabel("Status: Disconnected")
        self.tab_status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.tab_status_label.setStyleSheet("color: #d4544a;")
        
        self.tab_toggle_btn = QPushButton("Start Bot")
        self.tab_toggle_btn.setFixedSize(120, 36)
        self.tab_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.tab_toggle_btn.setToolTip("Start or stop the bot for the selected account")
        self.tab_toggle_btn.clicked.connect(self.toggle_bot_from_tab)
        
        header_layout.addWidget(self.tab_status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.tab_toggle_btn)
        log_layout.addLayout(header_layout)

        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setFont(QFont("Courier New", 11))
        self.log_console.setToolTip("Live feed of incoming/outgoing messages and bot activities")
        log_layout.addWidget(self.log_console)

        control_layout.addWidget(self.log_group)
        layout.addWidget(self.control_main_widget)
        self.workspace_stack.addWidget(page)

    def toggle_bot_from_tab(self):
        if self.selected_account_id is None:
            return
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            if acc[0] == self.selected_account_id:
                session_name = acc[3]
                self.toggle_bot_for_account(self.selected_account_id, session_name)
                break

    def start_bot_for_account(self, account_id, session_name):
        """Creates and launches the BotThread for a specific account."""
        if account_id in self.bot_threads and self.bot_threads[account_id].isRunning():
            return
            
        thread = BotThread(account_id, session_name, self)
        thread.qr_received.connect(self.on_qr_received)
        thread.connected.connect(self.on_bot_connected)
        thread.disconnected.connect(self.on_bot_disconnected)
        thread.message_received.connect(self.on_message_received)
        thread.chat_message_saved.connect(self.chat_message_saved_signal)
        
        self.bot_threads[account_id] = thread
        thread.start()

    def stop_bot_thread(self, account_id, logout=False):
        """Safely stops a bot connection thread and preserves Python references to prevent GC crashes."""
        thread = self.bot_threads.pop(account_id, None)
        if thread:
            if thread.isRunning():
                self.stopping_threads.append(thread)
                thread.finished.connect(lambda: self.cleanup_stopped_thread(thread))
                thread.stop(logout)
            else:
                thread.deleteLater()

    def cleanup_stopped_thread(self, thread):
        """Removes a thread from the stopping queue and releases Python references after it fully exits."""
        if thread in self.stopping_threads:
            self.stopping_threads.remove(thread)
        thread.deleteLater()

    def update_log_console_view(self):
        """Refreshes the console log text edit for the selected account."""
        self.log_console.clear()
        if self.selected_account_id is None:
            return
        acc_logs = self.account_logs.get(self.selected_account_id, [])
        for log_msg in acc_logs:
            self.log_console.appendHtml(log_msg)

    # ==========================================
    # PAGE 2: CHAT WORKSPACE VIEW
    # ==========================================
    def setup_chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder: shown when no account is selected
        self.chat_placeholder = QLabel("Select or add a WhatsApp account from the Accounts page first.")
        self.chat_placeholder.setAlignment(Qt.AlignCenter)
        self.chat_placeholder.setStyleSheet("font-size: 15px; font-weight: bold; font-family: 'Poppins';")
        layout.addWidget(self.chat_placeholder)

        # Main active widget
        self.chat_main_widget = QWidget()
        chat_layout = QHBoxLayout(self.chat_main_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(15)

        # Left Panel: Chats List
        left_widget = QFrame()
        left_widget.setObjectName("chatLeftPanel")
        left_widget.setAttribute(Qt.WA_StyledBackground, True)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        chats_header_layout = QHBoxLayout()
        chats_header_layout.setContentsMargins(0, 0, 0, 0)
        
        chats_title = QLabel("Conversations")
        chats_title.setFont(QFont("Arial", 16, QFont.Bold))
        chats_title.setStyleSheet("background: transparent;")
        chats_header_layout.addWidget(chats_title)
        
        self.new_chat_btn = QPushButton("💬 New Chat")
        self.new_chat_btn.setObjectName("secondaryBtn")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.setStyleSheet("padding: 6px 12px; font-size: 11px; font-weight: bold;")
        self.new_chat_btn.clicked.connect(self.start_new_chat)
        chats_header_layout.addWidget(self.new_chat_btn)
        
        left_layout.addLayout(chats_header_layout)

        self.chat_list_widget = QListWidget()
        self.chat_list_widget.setObjectName("chatList")
        self.chat_list_widget.setSpacing(2)
        self.chat_list_widget.currentItemChanged.connect(self.on_current_chat_changed)
        left_layout.addWidget(self.chat_list_widget)

        chat_layout.addWidget(left_widget)

        # Right Panel: Active Chat Room
        self.right_chat_container = QWidget()
        right_layout = QVBoxLayout(self.right_chat_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Right Panel Placeholder (Rounded Card Container)
        self.chat_placeholder_right = QFrame()
        self.chat_placeholder_right.setObjectName("chatRightPlaceholder")
        self.chat_placeholder_right.setAttribute(Qt.WA_StyledBackground, True)
        placeholder_layout = QVBoxLayout(self.chat_placeholder_right)
        
        lbl = QLabel("Select a conversation from the left to start messaging.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #8494a7; font-size: 14px; background: transparent;")
        placeholder_layout.addWidget(lbl)
        
        right_layout.addWidget(self.chat_placeholder_right, 1)

        # Right Panel Active Convo Widget (Rounded Card Container)
        self.chat_convo_widget = QFrame()
        self.chat_convo_widget.setObjectName("chatRightPanel")
        self.chat_convo_widget.setAttribute(Qt.WA_StyledBackground, True)
        convo_layout = QVBoxLayout(self.chat_convo_widget)
        convo_layout.setContentsMargins(0, 0, 0, 0)
        convo_layout.setSpacing(0)

        # Chat Header
        self.chat_header = QWidget()
        self.chat_header.setObjectName("chatHeader")
        header_vlayout = QVBoxLayout(self.chat_header)
        header_vlayout.setContentsMargins(15, 10, 15, 10)
        header_vlayout.setSpacing(3)

        self.chat_header_name = QLabel("Chat Name")
        self.chat_header_name.setObjectName("chatHeaderName")
        self.chat_header_name.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.chat_header_jid = QLabel("JID")
        self.chat_header_jid.setObjectName("chatHeaderJid")
        self.chat_header_jid.setFont(QFont("Arial", 9))

        header_vlayout.addWidget(self.chat_header_name)
        header_vlayout.addWidget(self.chat_header_jid)
        convo_layout.addWidget(self.chat_header)

        # Message Scroll Area
        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.chat_scroll_content = QWidget()
        self.chat_scroll_content.setStyleSheet("background-color: transparent;")
        self.chat_messages_layout = QVBoxLayout(self.chat_scroll_content)
        self.chat_messages_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_messages_layout.setSpacing(10)
        self.chat_messages_layout.setAlignment(Qt.AlignTop)

        self.chat_scroll_area.setWidget(self.chat_scroll_content)
        convo_layout.addWidget(self.chat_scroll_area, 1)

        # Input Area
        self.chat_input_area = QWidget()
        self.chat_input_area.setObjectName("chatInputArea")
        input_layout = QHBoxLayout(self.chat_input_area)
        input_layout.setContentsMargins(15, 10, 15, 10)
        input_layout.setSpacing(10)

        self.chat_attach_btn = QPushButton("📎")
        self.chat_attach_btn.setObjectName("chatAttachBtn")
        self.chat_attach_btn.setFixedSize(36, 36)
        self.chat_attach_btn.setCursor(Qt.PointingHandCursor)
        self.chat_attach_btn.setToolTip("Attach Image")
        self.chat_attach_btn.clicked.connect(self.select_chat_image)
        input_layout.addWidget(self.chat_attach_btn)

        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("chatInput")
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input, 1)

        self.chat_send_btn = QPushButton("Send ➔")
        self.chat_send_btn.setObjectName("chatSendBtn")
        self.chat_send_btn.setFixedWidth(90)
        self.chat_send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_send_btn)

        # Attachment Preview Area
        self.chat_attachment_preview = QWidget()
        self.chat_attachment_preview.setObjectName("chatAttachmentPreview")
        preview_layout = QHBoxLayout(self.chat_attachment_preview)
        preview_layout.setContentsMargins(15, 8, 15, 8)
        preview_layout.setSpacing(12)
        
        self.chat_preview_thumb = QLabel()
        self.chat_preview_thumb.setFixedSize(50, 50)
        self.chat_preview_thumb.setStyleSheet("border-radius: 4px; border: 1px solid #2d3548;")
        self.chat_preview_thumb.setScaledContents(True)
        preview_layout.addWidget(self.chat_preview_thumb)
        
        preview_text_widget = QWidget()
        preview_text_layout = QVBoxLayout(preview_text_widget)
        preview_text_layout.setContentsMargins(0, 0, 0, 0)
        preview_text_layout.setSpacing(2)
        
        self.chat_preview_filename = QLabel("filename.jpg")
        self.chat_preview_filename.setFont(QFont("Arial", 11, QFont.Bold))
        
        chat_preview_desc = QLabel("Image attached (will be sent with message)")
        chat_preview_desc.setFont(QFont("Arial", 9))
        chat_preview_desc.setStyleSheet("color: #8494a7;")
        
        preview_text_layout.addWidget(self.chat_preview_filename)
        preview_text_layout.addWidget(chat_preview_desc)
        preview_layout.addWidget(preview_text_widget, 1)
        
        self.chat_clear_attach_btn = QPushButton("✕")
        self.chat_clear_attach_btn.setFixedSize(24, 24)
        self.chat_clear_attach_btn.setCursor(Qt.PointingHandCursor)
        self.chat_clear_attach_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8494a7;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #d4544a;
            }
        """)
        self.chat_clear_attach_btn.clicked.connect(self.clear_chat_attachment)
        preview_layout.addWidget(self.chat_clear_attach_btn)
        
        self.chat_attachment_preview.setVisible(False)
        self.selected_chat_image_path = None

        convo_layout.addWidget(self.chat_attachment_preview)
        convo_layout.addWidget(self.chat_input_area)

        right_layout.addWidget(self.chat_convo_widget, 1)
        self.chat_convo_widget.setVisible(False)

        chat_layout.addWidget(self.right_chat_container, 1)

        self.chat_main_widget.setVisible(False)
        layout.addWidget(self.chat_main_widget)
        
        self.workspace_stack.addWidget(page)

    def start_new_chat(self):
        if self.selected_account_id is None:
            QMessageBox.warning(self, "No Account Selected", "Please select a connected WhatsApp account first.")
            return
            
        dialog = NewChatDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
            
        phone = dialog.get_phone_number()
        if not phone:
            QMessageBox.warning(self, "Invalid Phone Number", "Please enter a valid phone number.")
            return
            
        chat_jid = f"{phone}@s.whatsapp.net"
        
        # Create empty chat in SQLite
        db_manager.create_empty_chat(self.selected_account_id, chat_jid, phone)
        
        self.selected_chat_jid = chat_jid
        self.load_chats_list()
        
        # Select the newly created chat item in the list
        for i in range(self.chat_list_widget.count()):
            item = self.chat_list_widget.item(i)
            if item.data(Qt.UserRole) == chat_jid:
                self.chat_list_widget.setCurrentItem(item)
                self.on_chat_selected(item)
                break

    def load_chats_list(self):
        if self.selected_account_id is None:
            return
            
        prev_selected_jid = self.selected_chat_jid
        
        self.chat_list_widget.blockSignals(True)
        self.chat_list_widget.clear()
        chats = db_manager.get_chats_for_account(self.selected_account_id)
        
        selected_item = None
        for chat_row in chats:
            # id, chat_jid, chat_name, unread_count, last_message, last_message_time
            _, chat_jid, chat_name, _, last_message, last_message_time = chat_row
            
            display_name = chat_name or chat_jid
            if "@" in display_name and not chat_name:
                display_name = display_name.split("@")[0]
                
            is_group = "@g.us" in chat_jid or "-" in chat_jid
            
            item = QListWidgetItem(self.chat_list_widget)
            item.setData(Qt.UserRole, chat_jid)
            item.setData(Qt.UserRole + 1, display_name)
            
            widget = ChatItemWidget(display_name, last_message, last_message_time, is_group)
            item.setSizeHint(widget.sizeHint())
            self.chat_list_widget.addItem(item)
            self.chat_list_widget.setItemWidget(item, widget)
            
            if prev_selected_jid and prev_selected_jid == chat_jid:
                selected_item = item
                
        if selected_item:
            self.chat_list_widget.setCurrentItem(selected_item)
            
        self.chat_list_widget.blockSignals(False)
        
        if selected_item:
            self.on_chat_selected(selected_item)

    def on_current_chat_changed(self, current, previous):
        # Update selection state on all items
        for i in range(self.chat_list_widget.count()):
            item = self.chat_list_widget.item(i)
            widget = self.chat_list_widget.itemWidget(item)
            if widget and hasattr(widget, "setSelected"):
                widget.setSelected(item == current)
                
        if current:
            self.on_chat_selected(current)

    def on_chat_selected(self, item):
        if not item:
            return
        chat_jid = item.data(Qt.UserRole)
        chat_name = item.data(Qt.UserRole + 1)
        
        self.selected_chat_jid = chat_jid
        
        # Make sure styling is updated for selected item
        for i in range(self.chat_list_widget.count()):
            curr_item = self.chat_list_widget.item(i)
            widget = self.chat_list_widget.itemWidget(curr_item)
            if widget and hasattr(widget, "setSelected"):
                widget.setSelected(curr_item == item)
                
        self.chat_placeholder_right.setVisible(False)
        self.chat_convo_widget.setVisible(True)
        
        self.chat_header_name.setText(chat_name)
        self.chat_header_jid.setText(chat_jid)
        
        self.load_messages_for_selected_chat(chat_jid)

    def load_messages_for_selected_chat(self, chat_jid):
        if self.selected_account_id is None:
            return
            
        while self.chat_messages_layout.count():
            child = self.chat_messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        messages = db_manager.get_messages_for_chat(self.selected_account_id, chat_jid)
        
        for msg in messages:
            # id, message_id, sender_jid, sender_name, message_text, timestamp, is_from_me, media_path, media_type
            db_id, message_id, _, sender_name, message_text, timestamp, is_from_me, media_path, media_type = msg
            
            bubble_frame = QFrame()
            bubble_frame.setObjectName("myBubble" if is_from_me else "otherBubble")
            bubble_frame.setAttribute(Qt.WA_StyledBackground, True)
            
            bubble_layout = QVBoxLayout(bubble_frame)
            bubble_layout.setContentsMargins(12, 8, 12, 8)
            bubble_layout.setSpacing(5)
            
            is_dark = db_manager.get_theme() == "dark"
            if is_from_me:
                bg_color = "#2563eb" if is_dark else "#0f172a"
                text_color = "#ffffff"
                bubble_frame.setStyleSheet(f"""
                    background-color: {bg_color};
                    color: {text_color};
                    border: none;
                    border-radius: 12px;
                    border-bottom-right-radius: 2px;
                """)
            else:
                bg_color = "#27272a" if is_dark else "#f1f5f9"
                text_color = "#ffffff" if is_dark else "#0f172a"
                bubble_frame.setStyleSheet(f"""
                    background-color: {bg_color};
                    color: {text_color};
                    border: none;
                    border-radius: 12px;
                    border-bottom-left-radius: 2px;
                """)
            
            if not is_from_me and sender_name and sender_name != "WhatsApp User":
                sender_label = QLabel(sender_name)
                sender_label.setFont(QFont("Arial", 9, QFont.Bold))
                sender_color = self.get_sender_color(sender_name, is_dark)
                sender_label.setStyleSheet(f"color: {sender_color}; background: transparent; border: none;")
                bubble_layout.addWidget(sender_label)
                
            if media_type == "image" and media_path and os.path.exists(media_path):
                img_label = QLabel()
                pixmap = QPixmap(media_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaledToWidth(250, Qt.SmoothTransformation)
                    img_label.setPixmap(scaled_pixmap)
                    border_color = "#3f3f46" if is_dark else "#e2e8f0"
                    img_label.setStyleSheet(f"border-radius: 8px; background: transparent; border: 1px solid {border_color};")
                    bubble_layout.addWidget(img_label)
                    
            if message_text and message_text != "[Photo]":
                text_label = QLabel(message_text)
                text_label.setWordWrap(True)
                text_label.setFont(QFont("Arial", 11))
                text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                msg_color = "#ffffff" if is_from_me else ("#ffffff" if is_dark else "#0f172a")
                text_label.setStyleSheet(f"background: transparent; color: {msg_color}; border: none;")
                bubble_layout.addWidget(text_label)
                
            time_str = ""
            if timestamp:
                try:
                    dt = QDateTime.fromSecsSinceEpoch(int(timestamp))
                    time_str = dt.toString("HH:mm")
                except Exception:
                    time_str = str(timestamp)
                    
            time_label = QLabel(time_str)
            time_label.setAlignment(Qt.AlignRight)
            time_label.setFont(QFont("Courier New", 9))
            time_color = "#000000" if (is_from_me and is_dark) else ("#ffffff" if (is_from_me or is_dark) else "#000000")
            time_label.setStyleSheet(f"background: transparent; color: {time_color}; border: none;")
            bubble_layout.addWidget(time_label)
            
            msg_data = {
                "db_id": db_id,
                "message_id": message_id,
                "chat_jid": chat_jid,
                "message_text": message_text or "",
                "is_from_me": is_from_me
            }
            row_widget = MessageRowWidget(bubble_frame, is_from_me, msg_data, self)
            self.chat_messages_layout.addWidget(row_widget)
            
        QTimer.singleShot(50, self.scroll_chat_to_bottom)

    def scroll_chat_to_bottom(self):
        scrollbar = self.chat_scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def delete_chat_message(self, db_id, message_id, chat_jid, is_from_me):
        """Delete a message locally and attempt to revoke it on WhatsApp."""
        confirm = QMessageBox.question(
            self, "Delete Message",
            "Are you sure you want to delete this message?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # Delete from local DB
        db_manager.delete_message(self.selected_account_id, chat_jid, message_id)

        # Attempt to revoke on WhatsApp (only for outgoing messages)
        if is_from_me:
            thread = self.bot_threads.get(self.selected_account_id)
            if thread and thread.isRunning() and thread.client:
                import threading
                def revoke_worker():
                    try:
                        to_jid = parse_jid(chat_jid)
                        my_jid = thread.client.me.JID if (thread.client and thread.client.me) else parse_jid("")
                        thread.client.revoke_message(to_jid, my_jid, message_id)
                        log.info(f"Revoked message {message_id} on WhatsApp")
                    except Exception as e:
                        log.error(f"Error revoking message on WhatsApp: {e}")
                threading.Thread(target=revoke_worker, daemon=True).start()

        # Reload UI
        self.load_chats_list()
        if self.selected_chat_jid == chat_jid:
            self.load_messages_for_selected_chat(chat_jid)

    def edit_chat_message(self, db_id, message_id, chat_jid, current_text, is_from_me):
        """Edit a message locally and attempt to edit it on WhatsApp."""
        dialog = EditMessageDialog(current_text, self)
        if dialog.exec() != QDialog.Accepted:
            return

        new_text = dialog.get_text()
        if not new_text or new_text == current_text:
            return

        # Update local DB
        db_manager.edit_message(self.selected_account_id, chat_jid, message_id, new_text)

        # Attempt to edit on WhatsApp (only for outgoing messages)
        if is_from_me:
            thread = self.bot_threads.get(self.selected_account_id)
            if thread and thread.isRunning() and thread.client:
                import threading
                def edit_worker():
                    try:
                        from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message
                        to_jid = parse_jid(chat_jid)
                        wa_msg = Message(conversation=new_text)
                        thread.client.edit_message(to_jid, message_id, wa_msg)
                        log.info(f"Edited message {message_id} on WhatsApp")
                    except Exception as e:
                        log.error(f"Error editing message on WhatsApp: {e}")
                threading.Thread(target=edit_worker, daemon=True).start()

        # Reload UI
        self.load_chats_list()
        if self.selected_chat_jid == chat_jid:
            self.load_messages_for_selected_chat(chat_jid)

    def select_chat_image(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach Image to Message", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_path:
            self.selected_chat_image_path = file_path
            file_name = os.path.basename(file_path)
            self.chat_preview_filename.setText(file_name)
            
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.chat_preview_thumb.setPixmap(pixmap)
                self.chat_attachment_preview.setVisible(True)
                
    def clear_chat_attachment(self):
        self.selected_chat_image_path = None
        self.chat_preview_thumb.clear()
        self.chat_attachment_preview.setVisible(False)

    def select_rule_image(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image for Auto-Reply", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_path:
            self.set_rule_image(file_path)

    def set_rule_image(self, file_path):
        self.rule_image_path = file_path
        file_name = os.path.basename(file_path)
        self.rule_image_path_label.setText(file_name)
        self.rule_image_path_label.setToolTip(file_path)
        
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.rule_image_preview.setPixmap(scaled)
            self.rule_image_preview.setVisible(True)
            self.rule_image_clear_btn.setVisible(True)
        else:
            self.rule_image_preview.clear()
            self.rule_image_preview.setVisible(False)
            self.rule_image_clear_btn.setVisible(False)

    def clear_rule_image(self):
        self.rule_image_path = None
        self.rule_image_path_label.setText("No image selected")
        self.rule_image_path_label.setToolTip("")
        self.rule_image_preview.clear()
        self.rule_image_preview.setVisible(False)
        self.rule_image_clear_btn.setVisible(False)

    def send_chat_message(self):
        if self.selected_account_id is None:
            return
            
        thread = self.bot_threads.get(self.selected_account_id)
        if not thread or not thread.isRunning() or not thread.client or not thread.client.connected:
            QMessageBox.warning(self, "Connection Error", "Cannot send message. The bot for this account is not connected.")
            return
            
        text = self.chat_input.text().strip()
        image_path = getattr(self, "selected_chat_image_path", None)
        
        if not text and not image_path:
            return
            
        chat_jid_str = self.selected_chat_jid
        if not chat_jid_str:
            return
            
        self.chat_input.clear()
        self.clear_chat_attachment()
        
        # Send asynchronously via threading
        import threading
        def send_worker():
            try:
                to_jid = parse_jid(chat_jid_str)
                if image_path:
                    # Copy image to media folder so it displays locally
                    try:
                        import shutil
                        media_dir = PROJECT_DIR / "src" / "data" / "media"
                        media_dir.mkdir(parents=True, exist_ok=True)
                        reply_msg_id = thread.client.generate_message_id()
                        media_file = media_dir / f"{reply_msg_id}.jpg"
                        shutil.copy(image_path, media_file)
                        saved_media_path = str(media_file)
                    except Exception as copy_err:
                        log.error(f"Error copying sent image: {copy_err}")
                        saved_media_path = image_path
                        reply_msg_id = f"manual_img_{int(time.time()*1000)}"
                        
                    response = thread.client.send_image(to_jid, image_path, caption=text or None)
                    msg_id = response.ID if response else reply_msg_id
                    
                    db_manager.save_chat_and_message(
                        account_id=self.selected_account_id,
                        chat_jid=chat_jid_str,
                        chat_name=None,
                        message_id=msg_id,
                        sender_jid="",
                        sender_name="You",
                        message_text=text or "[Photo]",
                        timestamp=int(time.time()),
                        is_from_me=True,
                        media_path=saved_media_path,
                        media_type="image"
                    )
                else:
                    response = thread.client.send_message(to_jid, text)
                    msg_id = response.ID if response else f"manual_{int(time.time()*1000)}"
                    
                    db_manager.save_chat_and_message(
                        account_id=self.selected_account_id,
                        chat_jid=chat_jid_str,
                        chat_name=None,
                        message_id=msg_id,
                        sender_jid="",
                        sender_name="You",
                        message_text=text,
                        timestamp=int(time.time()),
                        is_from_me=True
                    )
                self.chat_message_saved_signal.emit(self.selected_account_id, chat_jid_str)
            except Exception as e:
                log.error(f"Error sending message: {e}")
                self.chat_message_saved_signal.emit(self.selected_account_id, chat_jid_str)
                
        threading.Thread(target=send_worker, daemon=True).start()

    def on_chat_message_saved(self, account_id, chat_jid):
        if account_id == self.selected_account_id:
            self.load_chats_list()
            if self.selected_chat_jid == chat_jid:
                self.load_messages_for_selected_chat(chat_jid)

    # ==========================================
    # PAGE 3: AUTO-REPLY RULES VIEW
    # ==========================================
    def setup_rules_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder: shown when no account is selected
        self.rules_placeholder = QLabel("Select or add a WhatsApp account from the Accounts page first.")
        self.rules_placeholder.setAlignment(Qt.AlignCenter)
        self.rules_placeholder.setStyleSheet("font-size: 15px; font-weight: bold; font-family: 'Poppins';")
        layout.addWidget(self.rules_placeholder)

        # Main active widget
        self.rules_main_widget = QWidget()
        rules_layout = QHBoxLayout(self.rules_main_widget)
        rules_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        rules_layout.addWidget(splitter)

        # Left Panel: Rule Form
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)

        self.rules_group = QGroupBox("Create Auto-Reply Rule")
        form_layout = QVBoxLayout(self.rules_group)

        form_layout.addWidget(QLabel("If received keyword (case-insensitive):"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("e.g. hai")
        self.keyword_input.setToolTip("Type the exact keyword to match in incoming messages (case-insensitive)")
        form_layout.addWidget(self.keyword_input)

        form_layout.addWidget(QLabel("Send this auto-reply message (Optional if Image attached):"))
        self.reply_input = QTextEdit()
        self.reply_input.setPlaceholderText("e.g. Halo juga!")
        self.reply_input.setToolTip("Type the response message to send when the keyword matches")
        form_layout.addWidget(self.reply_input)

        form_layout.addWidget(QLabel("Attach Image (Optional):"))
        image_select_layout = QHBoxLayout()
        self.rule_image_path_label = QLabel("No image selected")
        self.rule_image_path_label.setStyleSheet("color: #8494a7; font-size: 11px;")
        
        self.rule_image_select_btn = QPushButton("Browse...")
        self.rule_image_select_btn.setFixedWidth(80)
        self.rule_image_select_btn.clicked.connect(self.select_rule_image)
        
        self.rule_image_clear_btn = QPushButton("Clear")
        self.rule_image_clear_btn.setFixedWidth(60)
        self.rule_image_clear_btn.clicked.connect(self.clear_rule_image)
        self.rule_image_clear_btn.setVisible(False)
        
        image_select_layout.addWidget(self.rule_image_path_label, 1)
        image_select_layout.addWidget(self.rule_image_select_btn)
        image_select_layout.addWidget(self.rule_image_clear_btn)
        form_layout.addLayout(image_select_layout)
        
        self.rule_image_preview = QLabel()
        self.rule_image_preview.setFixedSize(100, 100)
        self.rule_image_preview.setAlignment(Qt.AlignCenter)
        self.rule_image_preview.setStyleSheet("border: 1px dashed #2d3548; border-radius: 4px; background: transparent;")
        self.rule_image_preview.setVisible(False)
        form_layout.addWidget(self.rule_image_preview, 0, Qt.AlignCenter)
        self.rule_image_path = None

        form_buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save Rule")
        self.save_btn.setObjectName("secondaryBtn")
        self.save_btn.setToolTip("Save new rule or update existing selection")
        self.save_btn.clicked.connect(self.save_rule)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setToolTip("Clear text fields and reset editor status")
        self.clear_btn.clicked.connect(self.clear_form)

        form_buttons.addWidget(self.save_btn)
        form_buttons.addWidget(self.clear_btn)
        form_layout.addLayout(form_buttons)

        left_layout.addWidget(self.rules_group)
        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # Right Panel: Rule List Table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        table_group = QGroupBox("Active Auto-Reply Rules")
        table_layout = QVBoxLayout(table_group)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["ID", "Keyword", "Reply Content", "Actions"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.verticalHeader().setDefaultSectionSize(40)
        self.rules_table.setEditTriggers(QTableWidget.NoEditTriggers)

        table_layout.addWidget(self.rules_table)
        right_layout.addWidget(table_group)
        splitter.addWidget(right_widget)

        splitter.setSizes([350, 650])
        layout.addWidget(self.rules_main_widget)
        self.workspace_stack.addWidget(page)

    # ==========================================
    # PAGE 4: GEMINI AI CONFIGURATION VIEW
    # ==========================================
    def setup_gemini_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder: shown when no account is selected
        self.gemini_placeholder = QLabel("Select or add a WhatsApp account from the Accounts page first.")
        self.gemini_placeholder.setAlignment(Qt.AlignCenter)
        self.gemini_placeholder.setStyleSheet("font-size: 15px; font-weight: bold; font-family: 'Poppins';")
        layout.addWidget(self.gemini_placeholder)

        # Main active widget
        self.gemini_main_widget = QWidget()
        gemini_layout = QVBoxLayout(self.gemini_main_widget)
        gemini_layout.setContentsMargins(0, 0, 0, 0)

        self.gemini_group = QGroupBox("Gemini AI Settings")
        form_layout = QVBoxLayout(self.gemini_group)
        form_layout.setSpacing(12)

        # Toggle Switch using CheckBox
        self.gemini_enabled_check = QCheckBox("Enable Gemini AI Auto-Responder")
        self.gemini_enabled_check.setFont(QFont("Arial", 12, QFont.Bold))
        self.gemini_enabled_check.setToolTip("Toggle to activate or deactivate Gemini AI automatic replies.")
        form_layout.addWidget(self.gemini_enabled_check)

        form_layout.addWidget(QLabel("Gemini API Key:"))
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_api_key_input.setPlaceholderText("AIzaSy...")
        self.gemini_api_key_input.setToolTip("Enter your Google Gemini API Key. You can get it from Google AI Studio.")
        form_layout.addWidget(self.gemini_api_key_input)
        
        form_layout.addWidget(QLabel("Gemini Model:"))
        self.gemini_model_input = QComboBox()
        self.gemini_model_input.setEditable(True)
        self.gemini_model_input.addItems([
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-3.5-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ])
        self.gemini_model_input.setToolTip("Select or type the Gemini model (default: gemini-2.5-flash).")
        form_layout.addWidget(self.gemini_model_input)

        form_layout.addWidget(QLabel("AI System Instructions (Prompt):"))
        self.gemini_instruction_input = QTextEdit()
        self.gemini_instruction_input.setPlaceholderText("Tell the Gemini AI how to behave and what data to use...")
        self.gemini_instruction_input.setToolTip("Define the personality, response constraints, and knowledge bases for the bot. Use {{products}} tag where you want the dynamic products catalog injected.")
        form_layout.addWidget(self.gemini_instruction_input)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.gemini_save_btn = QPushButton("Save AI Settings")
        self.gemini_save_btn.setObjectName("secondaryBtn")
        self.gemini_save_btn.setFixedWidth(160)
        self.gemini_save_btn.clicked.connect(self.save_gemini_settings)
        
        self.gemini_reset_btn = QPushButton("Reset to Default Prompt")
        self.gemini_reset_btn.setObjectName("clearBtn")
        self.gemini_reset_btn.setFixedWidth(180)
        self.gemini_reset_btn.clicked.connect(self.reset_gemini_instruction_to_default)

        btn_layout.addWidget(self.gemini_save_btn)
        btn_layout.addWidget(self.gemini_reset_btn)
        btn_layout.addStretch()
        form_layout.addLayout(btn_layout)

        gemini_layout.addWidget(self.gemini_group)
        self.gemini_main_widget.setVisible(False)
        layout.addWidget(self.gemini_main_widget)
        self.workspace_stack.addWidget(page)

    # ==========================================
    # PAGE 5: PRODUCTS CATALOG MANAGEMENT VIEW
    # ==========================================
    def setup_products_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder: shown when no account is selected
        self.products_placeholder = QLabel("Select or add a WhatsApp account from the Accounts page first.")
        self.products_placeholder.setAlignment(Qt.AlignCenter)
        self.products_placeholder.setStyleSheet("font-size: 15px; font-weight: bold; font-family: 'Poppins';")
        layout.addWidget(self.products_placeholder)

        # Main active widget
        self.products_main_widget = QWidget()
        prod_main_layout = QVBoxLayout(self.products_main_widget)
        prod_main_layout.setContentsMargins(0, 0, 0, 0)

        self.products_group = QGroupBox("Dynamic Product Catalog")
        prod_layout = QVBoxLayout(self.products_group)
        prod_layout.setSpacing(12)

        # Filter and Search Bar
        filter_bar_layout = QHBoxLayout()
        filter_bar_layout.setSpacing(10)

        # Search Input
        self.prod_search_input = QLineEdit()
        self.prod_search_input.setPlaceholderText("🔎 Search products by name or description...")
        self.prod_search_input.textChanged.connect(self.filter_products)
        self.prod_search_input.setFixedWidth(280)
        filter_bar_layout.addWidget(self.prod_search_input)

        # Category Filter
        filter_bar_layout.addWidget(QLabel("Category:"))
        self.prod_category_filter = QComboBox()
        self.prod_category_filter.addItem("All Categories")
        self.prod_category_filter.addItems(["Atasan", "Bawahan", "Outerwear", "Aksesoris", "Lainnya"])
        self.prod_category_filter.currentTextChanged.connect(self.filter_products)
        self.prod_category_filter.setFixedWidth(140)
        filter_bar_layout.addWidget(self.prod_category_filter)

        # Gender Filter
        filter_bar_layout.addWidget(QLabel("Gender:"))
        self.prod_gender_filter = QComboBox()
        self.prod_gender_filter.addItem("All Genders")
        self.prod_gender_filter.addItems(["Unisex", "Pria", "Wanita"])
        self.prod_gender_filter.currentTextChanged.connect(self.filter_products)
        self.prod_gender_filter.setFixedWidth(120)
        filter_bar_layout.addWidget(self.prod_gender_filter)

        filter_bar_layout.addStretch()

        # Add Product Button
        self.add_product_btn = QPushButton("➕ Add Product")
        self.add_product_btn.setObjectName("secondaryBtn")
        self.add_product_btn.setFixedSize(130, 36)
        self.add_product_btn.clicked.connect(self.on_add_product_clicked)
        filter_bar_layout.addWidget(self.add_product_btn)

        prod_layout.addLayout(filter_bar_layout)

        # Products Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Product Name", "Category", "Gender", "Price", "Discount", "Stock", "Actions"
        ])
        
        # Header Resizing
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)      # Product Name
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)      # Category
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)      # Gender
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)      # Price
        self.products_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Interactive)      # Discount
        self.products_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)          # Stock
        self.products_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents) # Actions

        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(40)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)

        prod_layout.addWidget(self.products_table)
        prod_main_layout.addWidget(self.products_group)
        layout.addWidget(self.products_main_widget)
        self.workspace_stack.addWidget(page)

    def load_gemini_settings(self):
        if self.selected_account_id is None:
            return
        enabled, api_key, model, instruction = db_manager.get_gemini_settings(self.selected_account_id)
        self.gemini_enabled_check.setChecked(enabled == 1)
        self.gemini_api_key_input.setText(api_key or "")
        
        # Set Gemini Model
        idx = self.gemini_model_input.findText(model or "gemini-2.5-flash")
        if idx >= 0:
            self.gemini_model_input.setCurrentIndex(idx)
        else:
            self.gemini_model_input.setEditText(model or "gemini-2.5-flash")
            
        # Check if instructions exist, if not, load default
        if not instruction:
            instruction = DEFAULT_GEMINI_INSTRUCTION
            
        self.gemini_instruction_input.setText(instruction)

    def save_gemini_settings(self):
        if self.selected_account_id is None:
            return
        enabled = self.gemini_enabled_check.isChecked()
        api_key = self.gemini_api_key_input.text().strip()
        model = self.gemini_model_input.currentText().strip() or "gemini-2.5-flash"
        instruction = self.gemini_instruction_input.toPlainText().strip()
        
        db_manager.update_gemini_settings(self.selected_account_id, enabled, api_key, model, instruction)
        QMessageBox.information(self, "Success", "Gemini settings updated successfully!")

    def reset_gemini_instruction_to_default(self):
        confirm = QMessageBox.question(
            self, "Reset Prompt",
            "Are you sure you want to reset the system instructions to the default CS bot template?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.gemini_instruction_input.setText(DEFAULT_GEMINI_INSTRUCTION)

    def filter_products(self):
        self.load_products_into_table()

    def load_products_into_table(self):
        if self.selected_account_id is None:
            return
            
        products = db_manager.get_all_products(self.selected_account_id)
        self.products_table.setRowCount(0)
        
        # Get filter values
        search_query = ""
        category_filter = "All Categories"
        gender_filter = "All Genders"
        
        if hasattr(self, "prod_search_input"):
            search_query = self.prod_search_input.text().strip().lower()
        if hasattr(self, "prod_category_filter"):
            category_filter = self.prod_category_filter.currentText()
        if hasattr(self, "prod_gender_filter"):
            gender_filter = self.prod_gender_filter.currentText()
            
        filtered_products = []
        for prod in products:
            # prod: (id, name, price, stock, description, image_path, discount, category, gender)
            prod_id, name, price, stock, description, image_path, discount, category, gender = prod
            
            # Check category filter
            if category_filter != "All Categories":
                if (category or "").strip() != category_filter:
                    continue
                    
            # Check gender filter
            if gender_filter != "All Genders":
                if (gender or "Unisex").strip() != gender_filter:
                    continue
                    
            # Check search query
            if search_query:
                name_match = search_query in name.lower()
                desc_match = search_query in (description or "").lower()
                if not name_match and not desc_match:
                    continue
                    
            filtered_products.append(prod)
            
        for row_idx, (prod_id, name, price, stock, description, image_path, discount, category, gender) in enumerate(filtered_products):
            self.products_table.insertRow(row_idx)
            self.products_table.setItem(row_idx, 0, QTableWidgetItem(str(prod_id)))
            
            display_name = f"📷 {name}" if image_path else name
            self.products_table.setItem(row_idx, 1, QTableWidgetItem(display_name))
            self.products_table.setItem(row_idx, 2, QTableWidgetItem(category or ""))
            self.products_table.setItem(row_idx, 3, QTableWidgetItem(gender or "Unisex"))
            self.products_table.setItem(row_idx, 4, QTableWidgetItem(price))
            
            # Format discount
            disc_text = f"{int(discount)}%" if discount > 0 else "-"
            self.products_table.setItem(row_idx, 5, QTableWidgetItem(disc_text))
            
            self.products_table.setItem(row_idx, 6, QTableWidgetItem(stock))
            
            # Actions Column (Edit/Delete Buttons)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit this product details")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff; 
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    padding: 4px 10px; 
                    border-radius: 6px; 
                    font-weight: bold; 
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f8fafc;
                    border-color: #94a3b8;
                }
            """)
            edit_btn.clicked.connect(
                lambda _, p_id=prod_id, n=name, p=price, s=stock, d=description, img=image_path, disc=discount, cat=category, gen=gender: 
                self.on_edit_product_clicked(p_id, n, p, s, d, img, disc, cat, gen)
            )
 
            del_btn = QPushButton("Delete")
            del_btn.setToolTip("Delete this product permanently")
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444; 
                    border: none;
                    color: #ffffff;
                    padding: 4px 10px; 
                    border-radius: 6px; 
                    font-weight: bold; 
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
            del_btn.clicked.connect(lambda _, p_id=prod_id: self.on_delete_product_clicked(p_id))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(del_btn)
            self.products_table.setCellWidget(row_idx, 7, actions_widget)

    def on_add_product_clicked(self):
        if self.selected_account_id is None:
            return
            
        dialog = ProductDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            name, price, stock, desc, img, discount, category, gender = dialog.get_product_data()
            if not name or not price or not stock:
                QMessageBox.warning(self, "Validation Error", "Product Name, Price, and Stock are required.")
                return
                
            db_manager.add_product(self.selected_account_id, name, price, stock, desc, img, discount, category, gender)
            self.load_products_into_table()

    def on_edit_product_clicked(self, product_id, name, price, stock, description, image_path="", discount=0.0, category="", gender="Unisex"):
        dialog = ProductDialog(name, price, stock, description, image_path, self, discount, category, gender)
        if dialog.exec() == QDialog.Accepted:
            new_name, new_price, new_stock, new_desc, new_img, new_disc, new_cat, new_gen = dialog.get_product_data()
            if not new_name or not new_price or not new_stock:
                QMessageBox.warning(self, "Validation Error", "Product Name, Price, and Stock are required.")
                return
                
            db_manager.update_product(product_id, new_name, new_price, new_stock, new_desc, new_img, new_disc, new_cat, new_gen)
            self.load_products_into_table()

    def on_delete_product_clicked(self, product_id):
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this product from the catalog?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            db_manager.delete_product(product_id)
            self.load_products_into_table()

    # ==========================================
    # BOT CALLBACK SIGNALS
    # ==========================================
    def on_bot_connected(self, account_id: int, phone: str, name: str):
        self.log_activity(account_id, f"⚡ Connected successfully as {name} ({phone})")
        if self.app_stack.currentIndex() == 0:
            self.load_launcher_profiles()
        else:
            self.update_active_profile_widget()
        
        if self.selected_account_id == account_id:
            self.update_page_visibility()
            
        # Close ScanQRDialog if open for this account
        if hasattr(self, "qr_dialogs"):
            dialog = self.qr_dialogs.pop(account_id, None)
            if dialog:
                dialog.accept()

    def on_bot_disconnected(self, account_id: int):
        self.log_activity(account_id, "❌ Bot disconnected.")
        thread = self.bot_threads.pop(account_id, None)
        if thread:
            thread.deleteLater()
            
        if self.app_stack.currentIndex() == 0:
            self.load_launcher_profiles()
        else:
            self.update_active_profile_widget()
        
        if self.selected_account_id == account_id:
            self.update_page_visibility()

    def on_qr_received(self, account_id: int, qr_data: bytes):
        if account_id == -1:
            return  # AddAccountDialog handles this
            
        # For existing accounts, open a popup QR dialog
        account_name = "WhatsApp Account"
        for acc in db_manager.get_all_accounts():
            if acc[0] == account_id:
                account_name = acc[2] or "WhatsApp Account"
                break
                
        if not hasattr(self, "qr_dialogs"):
            self.qr_dialogs = {}
            
        dialog = self.qr_dialogs.get(account_id)
        if not dialog or not dialog.isVisible():
            dialog = ScanQRDialog(account_id, account_name, self)
            self.qr_dialogs[account_id] = dialog
            dialog.show()
            
        dialog.update_qr(qr_data)
        self.log_activity(account_id, "🔄 New login QR Code rendered. Please scan the QR code using your WhatsApp app.")

    def on_message_received(self, account_id: int, sender: str, text: str, reply: str):
        if reply:
            self.log_activity(
                account_id,
                f"<span style='color: #8494a7;'>Received from {sender}:</span> '{text}' &rarr; "
                f"<span style='font-weight: bold;'>Replied:</span> '{reply}'", 
                is_html=True
            )
        else:
            self.log_activity(
                account_id,
                f"<span style='color: #8494a7;'>Received from {sender}:</span> '{text}' "
                f"<span style='color: #8494a7; font-style: italic;'>(No matching rules)</span>",
                is_html=True
            )

    # Logging helper
    def log_activity(self, account_id: int, text: str, is_html=False):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        prefix = f"<span style='color: #8494a7;'>[{timestamp}]</span>"
        log_msg = f"{prefix} {text}"
        
        if account_id not in self.account_logs:
            self.account_logs[account_id] = []
        self.account_logs[account_id].append(log_msg)
        
        if self.selected_account_id == account_id:
            self.log_console.appendHtml(log_msg)

    # ==========================================
    # CRUD OPERATIONS
    # ==========================================
    def load_rules_into_table(self):
        if self.selected_account_id is None:
            return
            
        rules = db_manager.get_all_replies(self.selected_account_id)
        self.rules_table.setRowCount(0)
        
        for row_idx, (rule_id, keyword, reply, image_path, _) in enumerate(rules):
            self.rules_table.insertRow(row_idx)
            self.rules_table.setItem(row_idx, 0, QTableWidgetItem(str(rule_id)))
            self.rules_table.setItem(row_idx, 1, QTableWidgetItem(keyword))
            display_text = f"[📷 Image] {reply}" if image_path else reply
            self.rules_table.setItem(row_idx, 2, QTableWidgetItem(display_text))

            # Action Column (Edit/Delete Buttons)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit this auto-reply rule")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff; 
                    color: #000000;
                    border: 2px solid #000000;
                    padding: 4px 10px; 
                    border-radius: 0px; 
                    font-weight: bold; 
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                }
            """)
            edit_btn.clicked.connect(lambda _, r_id=rule_id, kw=keyword, rep=reply, img=image_path: self.load_rule_for_edit(r_id, kw, rep, img))

            del_btn = QPushButton("Delete")
            del_btn.setToolTip("Delete this auto-reply rule permanently")
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e12b30; 
                    border: 2px solid #000000;
                    color: #ffffff;
                    padding: 4px 10px; 
                    border-radius: 0px; 
                    font-weight: bold; 
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #ffffff;
                    color: #e12b30;
                }
            """)
            del_btn.clicked.connect(lambda _, r_id=rule_id: self.delete_rule(r_id))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(del_btn)
            self.rules_table.setCellWidget(row_idx, 3, actions_widget)

    def load_rule_for_edit(self, rule_id, keyword, reply, image_path=None):
        self.current_editing_rule_id = rule_id
        self.keyword_input.setText(keyword)
        self.reply_input.setText(reply)
        if image_path and os.path.exists(image_path):
            self.set_rule_image(image_path)
        else:
            self.clear_rule_image()
        self.rules_group.setTitle(f"Edit Auto-Reply Rule (ID: {rule_id})")
        self.save_btn.setText("Update Rule")

    def save_rule(self):
        if self.selected_account_id is None:
            return
            
        keyword = self.keyword_input.text().strip()
        reply = self.reply_input.toPlainText().strip()
        image_path = getattr(self, "rule_image_path", None)

        if not keyword:
            QMessageBox.warning(self, "Validation Error", "Keyword cannot be empty.")
            return
        if not reply and not image_path:
            QMessageBox.warning(self, "Validation Error", "You must provide either reply text or attach an image.")
            return

        if self.current_editing_rule_id is not None:
            # Update mode
            success, msg = db_manager.update_reply(self.selected_account_id, self.current_editing_rule_id, keyword, reply, image_path)
            if success:
                img_log = f" (Image: {os.path.basename(image_path)})" if image_path else ""
                self.log_activity(self.selected_account_id, f"✏️ Updated rule ID {self.current_editing_rule_id}: '{keyword}' &rarr; '{reply}'{img_log}")
                self.clear_form()
                self.load_rules_into_table()
            else:
                QMessageBox.critical(self, "Database Error", msg)
        else:
            # Insert mode
            success, msg = db_manager.add_reply(self.selected_account_id, keyword, reply, image_path)
            if success:
                img_log = f" (Image: {os.path.basename(image_path)})" if image_path else ""
                self.log_activity(self.selected_account_id, f"➕ Added new rule: '{keyword}' &rarr; '{reply}'{img_log}")
                self.clear_form()
                self.load_rules_into_table()
            else:
                QMessageBox.critical(self, "Database Error", msg)

    def delete_rule(self, rule_id):
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete auto-reply rule ID {rule_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if db_manager.delete_reply(rule_id):
                if self.selected_account_id is not None:
                    self.log_activity(self.selected_account_id, f"🗑️ Deleted rule ID {rule_id}")
                if self.current_editing_rule_id == rule_id:
                    self.clear_form()
                self.load_rules_into_table()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to delete rule.")

    def clear_form(self):
        self.current_editing_rule_id = None
        self.keyword_input.clear()
        self.reply_input.clear()
        self.clear_rule_image()
        self.rules_group.setTitle("Create Auto-Reply Rule")
        self.save_btn.setText("Save Rule")

    # ==========================================
    # THEME AND STYLING MANAGEMENT
    # ==========================================
    def apply_theme(self, theme_name):
        """Applies stylesheet and colors according to selected theme."""
        self.setStyleSheet(LIGHT_STYLESHEET)
        self.logo_label.setStyleSheet("color: #000000; padding-bottom: 12px; border-bottom: 2px solid #000000; font-family: 'Poppins'; font-weight: 700; text-transform: uppercase;")
        self.launcher_title.setStyleSheet("color: #000000; font-family: 'Poppins'; font-weight: 700; text-transform: uppercase;")
        self.profile_name_label.setStyleSheet("color: #000000; background: transparent; border: none; font-weight: 700;")
        self.profile_phone_label.setStyleSheet("color: #000000; background: transparent; border: none; font-family: 'Courier New';")
            
        self.update_status_pill()
        self.update_active_profile_widget()
        
        # Update theme for all loaded profile cards in launcher
        for i in range(self.profiles_layout.count()):
            item = self.profiles_layout.itemAt(i)
            if item and item.widget():
                if hasattr(item.widget(), "apply_card_theme"):
                    item.widget().apply_card_theme(False)
                    
        self.load_rules_into_table()

    def toggle_theme(self):
        """Toggles the current theme (No-op since dark mode is removed)."""
        pass

    def stop_bot_for_account(self, account_id):
        """Stops the bot background thread for the specified account."""
        self.log_activity(account_id, "❌ Bot connection stopped.")
        self.stop_bot_thread(account_id)
        self.update_active_profile_widget()
        self.update_page_visibility()

    def update_status_pill(self):
        """Applies monochromatic formatting to the status indicator pill."""
        is_dark = db_manager.get_theme() == "dark"
        if self.selected_account_id is None:
            self.status_pill.setText("NO ACTIVE SELECTION")
            bg_color = "#27272a" if is_dark else "#f1f5f9"
            text_color = "#a1a1aa" if is_dark else "#64748b"
            self.status_pill.setStyleSheet(f"""
                background-color: {bg_color};
                color: {text_color};
                padding: 4px 12px;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 11px;
                font-family: 'Poppins';
            """)
            return
            
        thread = self.bot_threads.get(self.selected_account_id)
        
        if thread and thread.isRunning():
            if thread.client and thread.client.connected:
                self.status_pill.setText("CONNECTED")
                bg_color = "#064e3b" if is_dark else "#dcfce7"
                text_color = "#34d399" if is_dark else "#166534"
                self.status_pill.setStyleSheet(f"""
                    background-color: {bg_color}; 
                    color: {text_color}; 
                    padding: 4px 12px; 
                    border: none;
                    border-radius: 10px; 
                    font-weight: bold;
                    font-size: 11px;
                    font-family: 'Poppins';
                """)
            else:
                self.status_pill.setText("CONNECTING...")
                bg_color = "#78350f" if is_dark else "#fef9c3"
                text_color = "#fbbf24" if is_dark else "#854d0e"
                self.status_pill.setStyleSheet(f"""
                    background-color: {bg_color}; 
                    color: {text_color}; 
                    padding: 4px 12px; 
                    border: none;
                    border-radius: 10px; 
                    font-weight: bold;
                    font-size: 11px;
                    font-family: 'Poppins';
                """)
        else:
            self.status_pill.setText("DISCONNECTED")
            bg_color = "#7f1d1d" if is_dark else "#fee2e2"
            text_color = "#f87171" if is_dark else "#991b1b"
            self.status_pill.setStyleSheet(f"""
                background-color: {bg_color}; 
                color: {text_color}; 
                padding: 4px 12px; 
                border: none;
                border-radius: 10px; 
                font-weight: bold;
                font-size: 11px;
                font-family: 'Poppins';
            """)


    # Cleanup running threads
    def closeEvent(self, event):
        for acc_id in list(self.bot_threads.keys()):
            self.stop_bot_thread(acc_id)
            
        # Wait up to 2 seconds for all active/stopping threads to exit cleanly
        for thread in list(self.stopping_threads):
            thread.wait(2000)
            
        event.accept()
        # Hard exit to prevent lingering connection threads from causing SIGABRT crashes
        os._exit(0)


if __name__ == "__main__":
    # Initialize auto-reply, user, theme, and chat history databases
    db_manager.init_db()
    db_manager.init_user_db()
    db_manager.init_theme_db()
    db_manager.init_chat_store()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())