import os
import sys
import time
import logging
import shutil
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal

# Import database manager
import db_manager

# Setup logging
log = logging.getLogger(__name__)

# Constants
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SESSION_DIR = PROJECT_DIR / "src" / "data" / "session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)


class BotThread(QThread):
    """Background thread running the WhatsApp bot connection for a specific account."""
    qr_received = Signal(int, bytes)          # account_id, qr_data
    connected = Signal(int, str, str)         # account_id, phone, name
    disconnected = Signal(int)                # account_id
    message_received = Signal(int, str, str, str)  # account_id, sender, text, reply
    chat_message_saved = Signal(int, str)     # account_id, chat_jid

    def __init__(self, account_id: int, session_name: str, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.session_name = session_name
        self.client = None
        self._is_running = True

    def run(self):
        from neonize.client import NewClient
        from neonize.events import MessageEv, ConnectedEv, HistorySyncEv

        db_path = str(SESSION_DIR / f"{self.session_name}.db")
        log.info(f"[Account {self.account_id}] Initializing client at {db_path}...")
        self.client = NewClient(db_path)

        @self.client.event(ConnectedEv)
        def on_connected(client: NewClient, event: ConnectedEv):
            phone = ""
            name = ""
            if client.me:
                phone = getattr(client.me.JID, "User", "")
                name = getattr(client.me, "PushName", "")
            # Update account info in the database
            db_manager.update_account_info(self.account_id, phone, name)
            self.connected.emit(self.account_id, phone, name)

        @self.client.qr
        def handle_qr(client: NewClient, qr_data: bytes):
            self.qr_received.emit(self.account_id, qr_data)

        @self.client.event(MessageEv)
        def on_message(client: NewClient, event: MessageEv):
            from neonize.utils.jid import Jid2String
            import time

            chat_jid = Jid2String(event.Info.MessageSource.Chat)
            sender_num = event.Info.MessageSource.Sender.User
            sender_jid = f"{sender_num}@s.whatsapp.net" if sender_num else ""
            sender_name = getattr(event.Info, "Pushname", None) or getattr(event.Info, "PushName", None) or "WhatsApp User"
            is_from_me = event.Info.MessageSource.IsFromMe

            text = ""
            if event.Message.conversation:
                text = event.Message.conversation
            elif event.Message.extendedTextMessage and event.Message.extendedTextMessage.text:
                text = event.Message.extendedTextMessage.text
            elif event.Message.imageMessage and event.Message.imageMessage.caption:
                text = event.Message.imageMessage.caption

            text = text.strip()

            media_path = None
            media_type = None
            if event.Message.imageMessage:
                media_type = "image"
                try:
                    media_dir = PROJECT_DIR / "src" / "data" / "media"
                    media_dir.mkdir(parents=True, exist_ok=True)
                    media_file = media_dir / f"{event.Info.ID}.jpg"
                    log.info(f"[Account {self.account_id}] Downloading image: {event.Info.ID}")
                    self.client.download_any(event.Message, str(media_file))
                    media_path = str(media_file)
                except Exception as media_err:
                    log.error(f"[Account {self.account_id}] Error downloading image: {media_err}")

            if media_type == "image" and not text:
                text = "[Photo]"

            timestamp = getattr(event.Info, "Timestamp", 0) or int(time.time())

            # Save incoming or outgoing message to database
            db_manager.save_chat_and_message(
                account_id=self.account_id,
                chat_jid=chat_jid,
                chat_name=sender_name if not is_from_me else None,
                message_id=event.Info.ID,
                sender_jid=sender_jid,
                sender_name=sender_name,
                message_text=text,
                timestamp=timestamp,
                is_from_me=is_from_me,
                media_path=media_path,
                media_type=media_type
            )
            
            # Emit chat message saved signal
            self.chat_message_saved.emit(self.account_id, chat_jid)

            # Auto-reply handling (only for incoming messages)
            if is_from_me:
                return

            if not text:
                return

            # Check database for auto-reply matched to this specific account_id
            reply_text, reply_image = db_manager.get_reply_for_message(self.account_id, text)
            
            if reply_text or reply_image:
                log.info(f"[Account {self.account_id}] Trigger found for '{text}'. Replying with text='{reply_text}', image='{reply_image}' to {sender_num}.")
                
                if reply_image and os.path.exists(reply_image):
                    # Copy the auto-reply image to media folder so it can be previewed in Chat Workspace!
                    try:
                        import shutil
                        reply_msg_id = client.generate_message_id()
                        media_dir = PROJECT_DIR / "src" / "data" / "media"
                        media_dir.mkdir(parents=True, exist_ok=True)
                        media_file = media_dir / f"{reply_msg_id}.jpg"
                        shutil.copy(reply_image, media_file)
                        saved_media_path = str(media_file)
                    except Exception as copy_err:
                        log.error(f"[Account {self.account_id}] Error copying auto-reply image: {copy_err}")
                        saved_media_path = reply_image
                        reply_msg_id = f"auto_img_{int(time.time()*1000)}"
                        
                    client.send_image(event.Info.MessageSource.Chat, reply_image, caption=reply_text or None, quoted=event)
                    
                    db_manager.save_chat_and_message(
                        account_id=self.account_id,
                        chat_jid=chat_jid,
                        chat_name=sender_name,
                        message_id=reply_msg_id,
                        sender_jid="",
                        sender_name="ReplyHub Bot",
                        message_text=reply_text or "[Photo]",
                        timestamp=int(time.time()),
                        is_from_me=True,
                        media_path=saved_media_path,
                        media_type="image"
                    )
                else:
                    client.reply_message(reply_text, event)
                    reply_msg_id = client.generate_message_id()
                    db_manager.save_chat_and_message(
                        account_id=self.account_id,
                        chat_jid=chat_jid,
                        chat_name=sender_name,
                        message_id=reply_msg_id,
                        sender_jid="",
                        sender_name="ReplyHub Bot",
                        message_text=reply_text,
                        timestamp=int(time.time()),
                        is_from_me=True
                    )
                self.chat_message_saved.emit(self.account_id, chat_jid)
                self.message_received.emit(self.account_id, sender_num, text, reply_text or "[Photo]")
            else:
                self.message_received.emit(self.account_id, sender_num, text, "")

        @self.client.event(HistorySyncEv)
        def on_history_sync(client: NewClient, event: HistorySyncEv):
            log.info(f"[Account {self.account_id}] Received HistorySync event of type {event.syncType}")
            try:
                for convo in event.conversations:
                    chat_jid = convo.ID
                    chat_name = convo.newJID or convo.oldJID or None
                    
                    for history_msg in convo.messages:
                        web_msg = history_msg.message
                        if not web_msg:
                            continue
                            
                        msg_id = web_msg.key.ID
                        is_from_me = web_msg.key.fromMe
                        
                        sender_num = web_msg.key.participant or ""
                        if not is_from_me:
                            sender_jid = web_msg.key.participant or chat_jid
                        else:
                            sender_jid = ""
                            
                        sender_name = getattr(web_msg, "pushName", None) or "WhatsApp User"
                        
                        text = ""
                        msg = web_msg.message
                        if hasattr(msg, "conversation") and msg.conversation:
                            text = msg.conversation
                        elif hasattr(msg, "extendedTextMessage") and msg.extendedTextMessage and msg.extendedTextMessage.text:
                            text = msg.extendedTextMessage.text
                        elif hasattr(msg, "imageMessage") and msg.imageMessage:
                            if msg.imageMessage.caption:
                                text = msg.imageMessage.caption
                                
                        text = text.strip()
                        
                        media_type = None
                        media_path = None
                        if hasattr(msg, "imageMessage") and msg.imageMessage:
                            media_type = "image"
                            if not text:
                                text = "[Photo]"
                                
                        timestamp = getattr(web_msg, "messageTimestamp", 0) or int(time.time())
                        
                        db_manager.save_chat_and_message(
                            account_id=self.account_id,
                            chat_jid=chat_jid,
                            chat_name=chat_name,
                            message_id=msg_id,
                            sender_jid=sender_jid,
                            sender_name=sender_name,
                            message_text=text,
                            timestamp=timestamp,
                            is_from_me=is_from_me,
                            media_path=media_path,
                            media_type=media_type
                        )
                self.chat_message_saved.emit(self.account_id, "")
            except Exception as e:
                log.error(f"[Account {self.account_id}] Error in history sync handler: {e}")

        try:
            self.client.connect()
        except Exception as e:
            log.error(f"[Account {self.account_id}] Connection error: {e}")
        finally:
            self.disconnected.emit(self.account_id)

    def stop(self, logout=False):
        """Disconnect and stop the running thread. Set logout=True to unlink WhatsApp."""
        self._is_running = False
        if self.client:
            import threading
            # Run disconnect in a daemon thread to avoid blocking the main GUI thread on network close
            t = threading.Thread(
                target=self._safe_disconnect,
                args=(logout,),
                daemon=True
            )
            t.start()
        self.quit()
        self.wait(500)  # Wait at most 500ms for thread to exit, preventing GUI hang

    def _safe_disconnect(self, logout=False):
        try:
            if self.client:
                if logout:
                    try:
                        log.info(f"[Account {self.account_id}] Logging out client...")
                        self.client.logout()
                    except Exception as logout_err:
                        log.error(f"[Account {self.account_id}] Error logging out client: {logout_err}")
                self.client.disconnect()
        except Exception as e:
            log.error(f"[Account {self.account_id}] Error disconnecting client: {e}")
