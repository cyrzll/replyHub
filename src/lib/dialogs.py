import io
import time
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog, QComboBox, QSpinBox

# Import database manager
import db_manager

# Import BotThread hook
from src.hooks.bot_thread import BotThread

# Setup logging
log = logging.getLogger(__name__)

# Constants
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SESSION_DIR = PROJECT_DIR / "src" / "data" / "session"


class AddAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Link New WhatsApp Account")
        self.setFixedSize(420, 520)
        self.parent = parent
        self.account_id = None
        self.paired_phone = None
        self.paired_whatsapp_name = None
        self.session_name = f"session_{int(time.time())}"
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(15)
        
        # Screen 1: QR Scanning Screen (Active initially)
        self.qr_widget = QWidget()
        qr_layout = QVBoxLayout(self.qr_widget)
        qr_layout.setContentsMargins(0, 0, 0, 0)
        qr_layout.setSpacing(15)
        
        self.qr_title = QLabel("Scan QR Code")
        self.qr_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.qr_title.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_title)
        
        self.qr_desc = QLabel("Scan this QR code with WhatsApp (Linked Devices) to link your account.")
        self.qr_desc.setWordWrap(True)
        self.qr_desc.setAlignment(Qt.AlignCenter)
        self.qr_desc.setStyleSheet("color: #8494a7; font-size: 12px;")
        qr_layout.addWidget(self.qr_desc)
        
        self.qr_label = QLabel("Initializing QR Code...")
        self.qr_label.setFixedSize(260, 260)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setStyleSheet("border: 2px dashed #2d3548; border-radius: 8px; color: #8494a7;")
        qr_layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        
        self.status_label = QLabel("Establishing secure connection...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #d4a03a; font-weight: bold; font-size: 12px;")
        qr_layout.addWidget(self.status_label)
        
        # Cancel button for QR screen
        self.cancel_qr_btn = QPushButton("Batal")
        self.cancel_qr_btn.setObjectName("clearBtn")
        self.cancel_qr_btn.clicked.connect(self.reject)
        qr_layout.addWidget(self.cancel_qr_btn)
        
        self.layout.addWidget(self.qr_widget)
        
        # Screen 2: Name Input & Confirmation Screen (Hidden initially)
        self.name_widget = QWidget()
        name_layout = QVBoxLayout(self.name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(15)
        
        self.name_title = QLabel("Set Profile Name")
        self.name_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.name_title.setAlignment(Qt.AlignCenter)
        name_layout.addWidget(self.name_title)
        
        self.name_desc = QLabel("WhatsApp connection successful! Give this profile a name to identify it in ReplyHub.")
        self.name_desc.setWordWrap(True)
        self.name_desc.setStyleSheet("color: #8494a7; font-size: 12px;")
        name_layout.addWidget(self.name_desc)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. CS Admin")
        self.name_input.setStyleSheet("font-size: 14px; padding: 10px;")
        name_layout.addWidget(self.name_input)
        
        # Confirmation buttons
        buttons_layout = QHBoxLayout()
        self.cancel_name_btn = QPushButton("Batal")
        self.cancel_name_btn.setObjectName("clearBtn")
        self.cancel_name_btn.clicked.connect(self.reject)
        
        self.confirm_btn = QPushButton("Iya Tambahkan")
        self.confirm_btn.setObjectName("secondaryBtn")
        self.confirm_btn.clicked.connect(self.confirm_add)
        
        buttons_layout.addWidget(self.cancel_name_btn)
        buttons_layout.addWidget(self.confirm_btn)
        name_layout.addLayout(buttons_layout)
        
        self.name_widget.setVisible(False)
        self.layout.addWidget(self.name_widget)
        
        # Apply themes styling
        is_dark = db_manager.get_theme() == "dark"
        self.apply_dialog_theme(is_dark)
        
        # Immediately start bot connection thread (using temporary ID -1)
        self.parent.start_bot_for_account(-1, self.session_name)
        
        # Connect signals of the temporary thread to this dialog
        thread = self.parent.bot_threads[-1]
        thread.qr_received.connect(self.on_qr_received)
        thread.connected.connect(self.on_connected)
        thread.disconnected.connect(self.on_disconnected)

    def apply_dialog_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QDialog { background-color: #0f0f13; }
                QLabel { color: #f9f9fb; }
                QLineEdit { background-color: #16161a; border: 1px solid #22222a; border-radius: 6px; padding: 8px; color: #f9f9fb; }
                QPushButton { background-color: #4f46e5; color: #ffffff; border: none; border-radius: 6px; padding: 10px; font-weight: bold; }
                QPushButton:hover { background-color: #4338ca; }
                QPushButton#clearBtn { background-color: #22222a; color: #f9f9fb; border: 1px solid #22222a; border-radius: 6px; }
                QPushButton#clearBtn:hover { background-color: #2d2d37; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f8fafc; }
                QLabel { color: #0f172a; }
                QLineEdit { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; color: #0f172a; }
                QPushButton { background-color: #4f46e5; color: #ffffff; border: none; border-radius: 6px; padding: 10px; font-weight: bold; }
                QPushButton:hover { background-color: #4338ca; }
                QPushButton#clearBtn { background-color: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 6px; }
                QPushButton#clearBtn:hover { background-color: #f1f5f9; }
            """)

    def on_qr_received(self, account_id, qr_data):
        if account_id == -1:
            try:
                import io
                import segno
                qr = segno.make(qr_data)
                out = io.BytesIO()
                qr.save(out, kind='png', scale=5)
                pixmap = QPixmap()
                if pixmap.loadFromData(out.getvalue()):
                    self.qr_label.setPixmap(pixmap.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.qr_label.setStyleSheet("background-color: #ffffff; border: 1px solid #2d3548; border-radius: 8px;")
                    self.status_label.setText("Scan the QR code with WhatsApp Linked Devices to link account.")
                    self.status_label.setStyleSheet("color: #3daa6d; font-weight: bold; font-size: 12px;")
                else:
                    self.status_label.setText("Failed to render QR Code.")
                    self.status_label.setStyleSheet("color: #d4544a; font-weight: bold; font-size: 12px;")
            except Exception as e:
                self.status_label.setText(f"Error rendering QR: {e}")
                self.status_label.setStyleSheet("color: #d4544a; font-weight: bold; font-size: 12px;")

    def on_connected(self, account_id, phone, name):
        if account_id == -1:
            self.paired_phone = phone
            self.paired_whatsapp_name = name or "WhatsApp Account"
            
            # Stop listening to signals from the temporary -1 thread
            thread = self.parent.bot_threads.get(-1)
            if thread:
                try:
                    thread.qr_received.disconnect(self.on_qr_received)
                    thread.connected.disconnect(self.on_connected)
                    thread.disconnected.disconnect(self.on_disconnected)
                except Exception:
                    pass
            
            # Transition to Name setting screen
            self.qr_widget.setVisible(False)
            self.name_widget.setVisible(True)
            self.name_input.setText(self.paired_whatsapp_name)
            self.name_input.setFocus()

    def on_disconnected(self, account_id):
        if account_id == -1:
            self.status_label.setText("Connection disconnected.")
            self.status_label.setStyleSheet("color: #d4544a; font-weight: bold; font-size: 12px;")
            self.reject()

    def confirm_add(self):
        profile_name = self.name_input.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Validation Error", "Profile name cannot be empty.")
            return
            
        # Add profile to database
        self.account_id = db_manager.add_account(self.session_name, profile_name)
        if self.account_id:
            # Update account info (phone and WhatsApp name)
            db_manager.update_account_info(self.account_id, self.paired_phone, self.paired_whatsapp_name)
            
            # Re-key the thread in parent's bot_threads dictionary
            thread = self.parent.bot_threads.pop(-1, None)
            if thread:
                thread.account_id = self.account_id
                self.parent.bot_threads[self.account_id] = thread
                
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save profile to database.")
            self.reject()

    def reject(self):
        # Stop and remove temporary thread
        thread = self.parent.bot_threads.pop(-1, None)
        if thread:
            if thread.isRunning():
                self.parent.stopping_threads.append(thread)
                thread.finished.connect(lambda: self.parent.cleanup_stopped_thread(thread))
                thread.stop(logout=True)
            else:
                thread.deleteLater()
            
        # Delete temporary session file
        session_file = SESSION_DIR / f"{self.session_name}.db"
        if session_file.exists():
            try:
                session_file.unlink()
            except Exception as e:
                log.error(f"Error deleting temp session file: {e}")
                
        super().reject()


class ScanQRDialog(QDialog):
    def __init__(self, account_id, account_name, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.main_window = parent
        self.setWindowTitle(f"Scan QR - {account_name}")
        self.setFixedSize(320, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.title_label = QLabel("Scan QR Code")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.qr_label = QLabel("Generating QR...")
        self.qr_label.setFixedSize(220, 220)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setStyleSheet("border: 2px dashed #2d3548; border-radius: 8px; color: #8494a7;")
        layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        
        self.desc_label = QLabel("Scan this QR code with WhatsApp on your phone to connect.")
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #8494a7; font-size: 11px;")
        layout.addWidget(self.desc_label)
        
        self.cancel_btn = QPushButton("Tutup")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        is_dark = db_manager.get_theme() == "dark"
        self.apply_theme(is_dark)

    def reject(self):
        if self.main_window:
            self.main_window.stop_bot_thread(self.account_id)
        super().reject()
        
    def apply_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QDialog { background-color: #0f0f13; }
                QLabel { color: #f9f9fb; }
                QPushButton { background-color: #22222a; color: #f9f9fb; border: 1px solid #22222a; border-radius: 6px; padding: 8px; font-weight: bold; }
                QPushButton:hover { background-color: #2d2d37; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f8fafc; }
                QLabel { color: #0f172a; }
                QPushButton { background-color: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; font-weight: bold; }
                QPushButton:hover { background-color: #f1f5f9; }
            """)
            
    def update_qr(self, qr_data):
        try:
            import io
            import segno
            qr = segno.make(qr_data)
            out = io.BytesIO()
            qr.save(out, kind='png', scale=4)
            pixmap = QPixmap()
            if pixmap.loadFromData(out.getvalue()):
                self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.qr_label.setStyleSheet("background-color: #ffffff; border: 1px solid #2d3548; border-radius: 8px;")
        except Exception as e:
            log.error(f"Error rendering QR in dialog: {e}")


class NewChatDialog(QDialog):
    """Themed dialog for starting a chat with a new phone number."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Chat")
        self.setFixedSize(360, 210)
        
        is_dark = db_manager.get_theme() == "dark"
        bg = "#16161a" if is_dark else "#ffffff"
        fg = "#f9f9fb" if is_dark else "#0f172a"
        border = "#22222a" if is_dark else "#e2e8f0"
        input_bg = "#0f0f13" if is_dark else "#f8fafc"
        accent = "#4f46e5"
        
        self.setStyleSheet(f"QDialog {{ background-color: {bg}; border-radius: 12px; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("💬 Start New Chat")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet(f"color: {fg}; background: transparent; border: none;")
        layout.addWidget(title)
        
        desc = QLabel("Enter phone number (e.g., 628123456789):")
        desc.setFont(QFont("Arial", 10))
        desc.setStyleSheet(f"color: {'#94a3b8' if is_dark else '#64748b'}; background: transparent; border: none;")
        layout.addWidget(desc)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("628123456789")
        self.phone_input.setFont(QFont("Arial", 11))
        self.phone_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {accent};
            }}
        """)
        layout.addWidget(self.phone_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {'#94a3b8' if is_dark else '#64748b'};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {input_bg};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        
        start_btn = QPushButton("Start")
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4338ca;
            }}
        """)
        start_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)
        
    def get_phone_number(self):
        raw = self.phone_input.text().strip()
        # Clean the input: remove +, space, dashes
        cleaned = "".join(c for c in raw if c.isdigit())
        return cleaned


class EditMessageDialog(QDialog):
    """Themed dialog for editing a message's text content."""
    def __init__(self, current_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Message")
        self.setFixedSize(400, 240)
        
        is_dark = db_manager.get_theme() == "dark"
        bg = "#16161a" if is_dark else "#ffffff"
        fg = "#f9f9fb" if is_dark else "#0f172a"
        border = "#22222a" if is_dark else "#e2e8f0"
        input_bg = "#0f0f13" if is_dark else "#f8fafc"
        accent = "#4f46e5"
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("✏️ Edit Message")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet(f"color: {fg};")
        layout.addWidget(title)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(current_text)
        self.text_edit.setFont(QFont("Arial", 11))
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {input_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #8494a7;
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {input_bg};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3b8ad8;
            }}
        """)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def get_text(self):
        return self.text_edit.toPlainText().strip()


class ProductDialog(QDialog):
    """Themed dialog for adding or editing a product in the catalog."""
    def __init__(self, name="", price="", stock="", description="", image_path="", parent=None, discount=0.0, category="", gender="Unisex"):
        super().__init__(parent)
        self.setWindowTitle("Product Details")
        self.setFixedSize(400, 620)
        
        is_dark = db_manager.get_theme() == "dark"
        bg = "#16161a" if is_dark else "#ffffff"
        fg = "#f9f9fb" if is_dark else "#0f172a"
        border = "#22222a" if is_dark else "#e2e8f0"
        input_bg = "#0f0f13" if is_dark else "#f8fafc"
        accent = "#4f46e5"
        
        self.setStyleSheet(f"QDialog {{ background-color: {bg}; border-radius: 12px; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        title_text = "✏️ Edit Product" if name else "➕ Add Product"
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet(f"color: {fg}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Product Name
        layout.addWidget(QLabel("Product Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(name)
        self.name_input.setPlaceholderText("e.g. Kaos Oversize")
        self.name_input.setStyleSheet(f"background-color: {input_bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; padding: 6px;")
        layout.addWidget(self.name_input)
        
        # Price
        layout.addWidget(QLabel("Price:"))
        self.price_input = QLineEdit()
        self.price_input.setText(price)
        self.price_input.setPlaceholderText("e.g. Rp99.000")
        self.price_input.setStyleSheet(f"background-color: {input_bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; padding: 6px;")
        layout.addWidget(self.price_input)
        
        # Stock
        layout.addWidget(QLabel("Stock:"))
        self.stock_input = QLineEdit()
        self.stock_input.setText(stock)
        self.stock_input.setPlaceholderText("e.g. Hitam M, L; Putih L")
        self.stock_input.setStyleSheet(f"background-color: {input_bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; padding: 6px;")
        layout.addWidget(self.stock_input)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QLineEdit()
        self.desc_input.setText(description)
        self.desc_input.setPlaceholderText("e.g. cotton combed 24s")
        self.desc_input.setStyleSheet(f"background-color: {input_bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; padding: 6px;")
        layout.addWidget(self.desc_input)

        # Style presets for combobox & spinbox
        combo_style = f"""
            QComboBox {{
                background-color: {input_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg};
                color: {fg};
                selection-background-color: {accent};
                selection-color: #ffffff;
                border: 1px solid {border};
            }}
        """
        spin_style = f"""
            QSpinBox {{
                background-color: {input_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px;
            }}
        """

        # Discount (%)
        layout.addWidget(QLabel("Discount (%):"))
        self.discount_input = QSpinBox()
        self.discount_input.setRange(0, 100)
        self.discount_input.setValue(int(discount or 0))
        self.discount_input.setStyleSheet(spin_style)
        layout.addWidget(self.discount_input)
        
        # Category
        layout.addWidget(QLabel("Category:"))
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(["Atasan", "Bawahan", "Outerwear", "Aksesoris", "Lainnya"])
        self.category_input.setStyleSheet(combo_style)
        if category:
            self.category_input.setCurrentText(category)
        else:
            self.category_input.setCurrentIndex(0)
        layout.addWidget(self.category_input)
        
        # Gender
        layout.addWidget(QLabel("Gender:"))
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Unisex", "Pria", "Wanita"])
        self.gender_input.setStyleSheet(combo_style)
        if gender in ["Unisex", "Pria", "Wanita"]:
            self.gender_input.setCurrentText(gender)
        else:
            self.gender_input.setCurrentText("Unisex")
        layout.addWidget(self.gender_input)

        # Image chooser
        layout.addWidget(QLabel("Product Photo (Optional):"))
        image_layout = QHBoxLayout()
        display_label_text = Path(image_path).name if image_path else "No photo selected"
        self.image_path_label = QLabel(display_label_text)
        self.image_path_label.setStyleSheet(f"color: {'#8494a7' if is_dark else '#64748b'}; font-size: 11px;")
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.setStyleSheet(f"background-color: {input_bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; padding: 4px; font-weight: normal; font-size: 11px;")
        self.browse_btn.clicked.connect(self.browse_image)
        
        self.clear_img_btn = QPushButton("Clear")
        self.clear_img_btn.setFixedWidth(60)
        self.clear_img_btn.setStyleSheet(f"background-color: transparent; color: #8494a7; border: 1px solid {border}; border-radius: 6px; padding: 4px; font-weight: normal; font-size: 11px;")
        self.clear_img_btn.clicked.connect(self.clear_image)
        self.clear_img_btn.setVisible(bool(image_path))
        
        image_layout.addWidget(self.image_path_label, 1)
        image_layout.addWidget(self.browse_btn)
        image_layout.addWidget(self.clear_img_btn)
        layout.addLayout(image_layout)
        
        # Image Preview
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(60, 60)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet(f"border: 1px dashed {border}; border-radius: 4px; background: transparent;")
        self.image_preview.setVisible(False)
        layout.addWidget(self.image_preview, 0, Qt.AlignCenter)
        
        self.selected_image_path = image_path
        if image_path:
            self.update_preview(image_path)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {'#94a3b8' if is_dark else '#64748b'};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {input_bg};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4338ca;
            }}
        """)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Product Photo", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_path:
            self.selected_image_path = file_path
            self.image_path_label.setText(Path(file_path).name)
            self.clear_img_btn.setVisible(True)
            self.update_preview(file_path)

    def clear_image(self):
        self.selected_image_path = ""
        self.image_path_label.setText("No photo selected")
        self.clear_img_btn.setVisible(False)
        self.image_preview.setVisible(False)
        self.image_preview.clear()

    def update_preview(self, path):
        if not path or not Path(path).exists():
            self.image_preview.setVisible(False)
            return
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.image_preview.setPixmap(
                pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.image_preview.setVisible(True)
        else:
            self.image_preview.setVisible(False)

    def get_product_data(self):
        return (
            self.name_input.text().strip(),
            self.price_input.text().strip(),
            self.stock_input.text().strip(),
            self.desc_input.text().strip(),
            self.selected_image_path,
            float(self.discount_input.value()),
            self.category_input.currentText().strip(),
            self.gender_input.currentText().strip()
        )
