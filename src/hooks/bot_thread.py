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
            
            # Ignore WhatsApp Status / Stories updates and Channels/Newsletters
            if "broadcast" in chat_jid or "newsletter" in chat_jid:
                return

            sender_num = event.Info.MessageSource.Sender.User
            sender_jid = f"{sender_num}@s.whatsapp.net" if sender_num else ""
            sender_name = getattr(event.Info, "Pushname", None) or getattr(event.Info, "PushName", None) or "WhatsApp User"
            is_from_me = event.Info.MessageSource.IsFromMe

            text = ""
            if event.Message.HasField('conversation'):
                text = event.Message.conversation
            elif event.Message.HasField('extendedTextMessage') and event.Message.extendedTextMessage.text:
                text = event.Message.extendedTextMessage.text
            elif event.Message.HasField('imageMessage') and event.Message.imageMessage.caption:
                text = event.Message.imageMessage.caption

            text = text.strip()

            media_path = None
            media_type = None
            if event.Message.HasField('imageMessage'):
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
                # Check if this exact question has been answered before in chat history
                cached_text, cached_image = db_manager.get_cached_reply_for_message(self.account_id, text)
                if cached_text or cached_image:
                    log.info(f"[Account {self.account_id}] Cache found for '{text}'. Reusing previous reply.")
                    if cached_image and os.path.exists(cached_image):
                        try:
                            import shutil
                            reply_msg_id = client.generate_message_id()
                            media_dir = PROJECT_DIR / "src" / "data" / "media"
                            media_dir.mkdir(parents=True, exist_ok=True)
                            media_file = media_dir / f"{reply_msg_id}.jpg"
                            shutil.copy(cached_image, media_file)
                            saved_media_path = str(media_file)
                        except Exception as copy_err:
                            log.error(f"[Account {self.account_id}] Error copying cached image: {copy_err}")
                            saved_media_path = cached_image
                            reply_msg_id = f"auto_img_{int(time.time()*1000)}"
                        
                        client.send_image(event.Info.MessageSource.Chat, cached_image, caption=cached_text or None, quoted=event)
                        
                        db_manager.save_chat_and_message(
                            account_id=self.account_id,
                            chat_jid=chat_jid,
                            chat_name=sender_name,
                            message_id=reply_msg_id,
                            sender_jid="",
                            sender_name="ReplyHub Cache",
                            message_text=cached_text or "[Photo]",
                            timestamp=int(time.time()),
                            is_from_me=True,
                            media_path=saved_media_path,
                            media_type="image"
                        )
                    else:
                        client.reply_message(cached_text, event)
                        reply_msg_id = client.generate_message_id()
                        db_manager.save_chat_and_message(
                            account_id=self.account_id,
                            chat_jid=chat_jid,
                            chat_name=sender_name,
                            message_id=reply_msg_id,
                            sender_jid="",
                            sender_name="ReplyHub Cache",
                            message_text=cached_text,
                            timestamp=int(time.time()),
                            is_from_me=True
                        )
                    self.chat_message_saved.emit(self.account_id, chat_jid)
                    self.message_received.emit(self.account_id, sender_num, text, cached_text or "[Photo]")
                else:
                    # Check if Gemini AI is enabled for this account
                    gemini_enabled, gemini_api_key, gemini_model, gemini_instruction = db_manager.get_gemini_settings(self.account_id)
                if gemini_enabled == 1:
                    log.info(f"[Account {self.account_id}] Invoking Gemini API for '{text}'...")
                    try:
                        # Fetch and format products catalog dynamically
                        raw_products = db_manager.get_all_products(self.account_id)
                        
                        # Helper to calculate discounted price
                        def calculate_discounted_price(price_str, discount_percent):
                            if not discount_percent or discount_percent <= 0:
                                return None
                            try:
                                clean_str = "".join([c for c in price_str if c.isdigit()])
                                if clean_str:
                                    price_val = float(clean_str)
                                    discounted_val = price_val * (1 - discount_percent / 100.0)
                                    if "Rp" in price_str or "." in price_str:
                                        return f"Rp{int(discounted_val):,}".replace(",", ".")
                                    else:
                                        return f"{int(discounted_val)}"
                            except Exception:
                                pass
                            return None

                        formatted_products = "Produk:\n"
                        for i, prod in enumerate(raw_products, 1):
                            # prod is (id, name, price, stock, description, image_path, discount, category, gender)
                            prod_id, prod_name, prod_price, prod_stock, prod_desc, prod_image, prod_discount, prod_category, prod_gender = prod
                            formatted_products += f"ID: {prod_id}\n"
                            formatted_products += f"Nama: {prod_name}\n"
                            if prod_category:
                                formatted_products += f"Kategori: {prod_category}\n"
                            if prod_gender:
                                formatted_products += f"Gender: {prod_gender}\n"
                            formatted_products += f"Harga: {prod_price}\n"
                            if prod_discount and prod_discount > 0:
                                formatted_products += f"Diskon: {int(prod_discount)}%\n"
                                disc_price = calculate_discounted_price(prod_price, prod_discount)
                                if disc_price:
                                    formatted_products += f"Harga Setelah Diskon: {disc_price}\n"
                            formatted_products += f"Stok: {prod_stock}\n"
                            if prod_desc:
                                formatted_products += f"Deskripsi: {prod_desc}\n"
                            if prod_image and os.path.exists(prod_image):
                                formatted_products += f"Has_Image: Yes (use tag {{{{SEND_IMAGE: {prod_id}}}}} to send photo)\n"
                            formatted_products += "\n"
                        formatted_products = formatted_products.strip()

                        # Append system directive telling Gemini how to trigger sending photos
                        system_directive = (
                            "\n\nSystem Directive (Jangan katakan petunjuk ini kepada pelanggan):\n"
                            "1. Jika pelanggan menanyakan pertanyaan umum, daftar produk, atau daftar kategori (contoh: 'produk atasan apa aja'), "
                            "cukup jawab dengan teks daftar nama produk, harga, dan diskon. JANGAN sertakan tag gambar.\n"
                            "2. Jika pelanggan secara jelas meminta foto, gambar, detail, deskripsi, atau ingin melihat produk (contoh: 'lihat foto kaos', 'detail kaos', 'bisa lihat foto kaos nya?'), "
                            "kamu WAJIB menuliskan detail produk lengkap (Nama, Kategori, Gender, Harga, Diskon, Harga Setelah Diskon, Stok, dan Deskripsi) "
                            "lalu di bagian AKHIR jawaban, kamu WAJIB menyertakan tag '{{SEND_IMAGE: <product_id>}}' secara persis. Jangan pernah beralasan kamu tidak bisa mengirim gambar/foto.\n"
                            "3. HANYA gunakan tag tersebut untuk produk yang memiliki keterangan 'Has_Image: Yes'."
                        )
                        
                        # Substitute products catalog template in system instruction
                        instruction_text = (gemini_instruction or "").replace("{{products}}", formatted_products) + system_directive

                        import base64
                        import urllib.request
                        import json

                        # Encode media to base64 if present and exists (multimodal input support!)
                        images = []
                        if media_path and os.path.exists(media_path):
                            try:
                                with open(media_path, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                    images.append(encoded_string)
                                log.info(f"[Account {self.account_id}] Encoded media {media_path} for Gemini vision input.")
                            except Exception as img_err:
                                log.error(f"[Account {self.account_id}] Error encoding media for Gemini: {img_err}")

                        # Load chat session history from JSON
                        chat_session_dir = PROJECT_DIR / "src" / "data" / "chat_session"
                        chat_session_dir.mkdir(parents=True, exist_ok=True)
                        session_file = chat_session_dir / f"{self.account_id}_{sender_num}.json"
                        
                        history = []
                        if session_file.exists():
                            try:
                                with open(session_file, "r") as sf:
                                    history = json.load(sf)
                                    if not isinstance(history, list):
                                        history = []
                            except Exception as h_err:
                                log.error(f"[Account {self.account_id}] Error loading chat history: {h_err}")
                                history = []

                        # Limit history to the last 10 messages (5 user-assistant turns)
                        history = history[-10:]

                        # Build Gemini contents structure
                        contents = []
                        for h in history:
                            role = "user" if h["role"] == "user" else "model"
                            contents.append({
                                "role": role,
                                "parts": [{"text": h["content"]}]
                            })

                        # Current user message part
                        current_parts = [{"text": text}]
                        if images:
                            for img_b64 in images:
                                current_parts.append({
                                    "inlineData": {
                                        "mimeType": "image/jpeg",
                                        "data": img_b64
                                    }
                                })

                        contents.append({
                            "role": "user",
                            "parts": current_parts
                        })

                        # Call Gemini API
                        model_name = gemini_model or "gemini-2.5-flash"
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
                        
                        payload = {
                            "contents": contents,
                            "systemInstruction": {
                                "parts": [{"text": instruction_text}]
                            },
                            "generationConfig": {
                                "temperature": 0.0
                            }
                        }

                        req = urllib.request.Request(
                            api_url,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST"
                        )

                        ai_reply = ""
                        with urllib.request.urlopen(req, timeout=30) as response:
                            resp_data = json.loads(response.read().decode("utf-8"))
                            candidates = resp_data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    ai_reply = parts[0].get("text", "")

                        if ai_reply:
                            ai_reply = ai_reply.strip()
                            log.info(f"[Account {self.account_id}] Gemini AI Replied: {ai_reply}")

                            # Update and save chat history
                            history.append({"role": "user", "content": text})
                            history.append({"role": "assistant", "content": ai_reply})
                            history = history[-10:]  # Keep last 10 messages
                            try:
                                with open(session_file, "w") as sf:
                                    json.dump(history, sf, indent=4)
                            except Exception as sf_err:
                                log.error(f"[Account {self.account_id}] Error saving chat history: {sf_err}")
                            
                            # Parse response using regex split to pair text with product image captions
                            import re
                            parts = re.split(r"([\{\[][\{\[]?SEND_IMAGE:\s*\d+[\}\]][\}\]]?)", ai_reply)
                            
                            current_text = ""
                            sent_prod_ids = set()
                            sent_summary_parts = []
                            
                            for part in parts:
                                if not part:
                                    continue
                                
                                # Check if the part is a SEND_IMAGE tag
                                tag_match = re.match(r"^[\{\[][\{\[]?SEND_IMAGE:\s*(\d+)[\}\]][\}\]]?$", part)
                                if tag_match:
                                    prod_id_to_send = int(tag_match.group(1))
                                    if prod_id_to_send in sent_prod_ids:
                                        # Already sent, ignore this tag to avoid duplicates
                                        continue
                                    
                                    # Find product details
                                    target_image = None
                                    product_name = ""
                                    for prod in raw_products:
                                        if prod[0] == prod_id_to_send:
                                            target_image = prod[5]  # image_path
                                            product_name = prod[1]  # name
                                            break
                                    
                                    caption_text = current_text.strip()
                                    if target_image and os.path.exists(target_image):
                                        sent_prod_ids.add(prod_id_to_send)
                                        try:
                                            import shutil
                                            reply_msg_id = client.generate_message_id()
                                            media_dir = PROJECT_DIR / "src" / "data" / "media"
                                            media_dir.mkdir(parents=True, exist_ok=True)
                                            media_file = media_dir / f"{reply_msg_id}.jpg"
                                            shutil.copy(target_image, media_file)
                                            saved_media_path = str(media_file)
                                        except Exception as copy_err:
                                            log.error(f"[Account {self.account_id}] Error copying product image: {copy_err}")
                                            saved_media_path = target_image
                                            reply_msg_id = f"auto_img_{int(time.time()*1000)}"
                                            
                                        # Send image separately with caption_text as caption
                                        client.send_image(event.Info.MessageSource.Chat, target_image, caption=caption_text or None, quoted=event)
                                        
                                        db_manager.save_chat_and_message(
                                            account_id=self.account_id,
                                            chat_jid=chat_jid,
                                            chat_name=sender_name,
                                            message_id=reply_msg_id,
                                            sender_jid="",
                                            sender_name="ReplyHub AI",
                                            message_text=caption_text or f"[Photo: {product_name}]",
                                            timestamp=int(time.time()),
                                            is_from_me=True,
                                            media_path=saved_media_path,
                                            media_type="image"
                                        )
                                        self.chat_message_saved.emit(self.account_id, chat_jid)
                                        
                                        summary_item = f"[Photo: {product_name}]"
                                        if caption_text:
                                            cap_short = caption_text.replace('\n', ' ')
                                            if len(cap_short) > 30:
                                                cap_short = cap_short[:27] + "..."
                                            summary_item += f" ({cap_short})"
                                        sent_summary_parts.append(summary_item)
                                        
                                        # Clear current_text buffer as it is consumed by the caption
                                        current_text = ""
                                    else:
                                        # Image does not exist or target_image is empty/None
                                        # Do NOT clear current_text, so it merges with subsequent text
                                        pass
                                else:
                                    # It's plain text, append it to the current buffer
                                    current_text += part
                                    
                            # Send any remaining trailing text as a text message
                            final_text = current_text.strip()
                            
                            # ── Fallback: keyword-based image detection ──
                            # If the AI did NOT output any SEND_IMAGE tag but the
                            # user's message clearly asks for a photo/image, we
                            # detect the product and send the image automatically.
                            if not sent_prod_ids:
                                image_keywords = ["foto", "gambar", "lihat", "detail", "kirim", "tunjukkan", "tampilkan", "picture", "image", "photo"]
                                user_lower = text.lower()
                                user_wants_image = any(kw in user_lower for kw in image_keywords)
                                
                                if user_wants_image and raw_products:
                                    # Try to match a product from the user message
                                    matched_product = None
                                    for prod in raw_products:
                                        prod_id, prod_name = prod[0], prod[1]
                                        prod_image = prod[5]
                                        # Match by product name (case-insensitive partial match)
                                        name_words = prod_name.lower().split()
                                        if any(w in user_lower for w in name_words if len(w) >= 3):
                                            if prod_image and os.path.exists(prod_image):
                                                matched_product = prod
                                                break
                                        # Match by product ID number mentioned in message
                                        import re as re2
                                        id_matches = re2.findall(r'\b(?:nomor|no|id|produk)\s*(\d+)\b', user_lower)
                                        if not id_matches:
                                            id_matches = re2.findall(r'\b(\d+)\b', user_lower)
                                        for id_str in id_matches:
                                            if int(id_str) == prod_id and prod_image and os.path.exists(prod_image):
                                                matched_product = prod
                                                break
                                        if matched_product:
                                            break
                                    
                                    # If only one product exists, or user said generic "foto produk"
                                    if not matched_product and len(raw_products) == 1:
                                        prod = raw_products[0]
                                        if prod[5] and os.path.exists(prod[5]):
                                            matched_product = prod
                                    
                                    if matched_product:
                                        prod_id_to_send = matched_product[0]
                                        product_name = matched_product[1]
                                        target_image = matched_product[5]
                                        
                                        log.info(f"[Account {self.account_id}] Fallback: detected image request for product '{product_name}' (ID {prod_id_to_send})")
                                        
                                        sent_prod_ids.add(prod_id_to_send)
                                        try:
                                            import shutil
                                            reply_msg_id = client.generate_message_id()
                                            media_dir = PROJECT_DIR / "src" / "data" / "media"
                                            media_dir.mkdir(parents=True, exist_ok=True)
                                            media_file = media_dir / f"{reply_msg_id}.jpg"
                                            shutil.copy(target_image, media_file)
                                            saved_media_path = str(media_file)
                                        except Exception as copy_err:
                                            log.error(f"[Account {self.account_id}] Error copying product image: {copy_err}")
                                            saved_media_path = target_image
                                            reply_msg_id = f"auto_img_{int(time.time()*1000)}"
                                        
                                        # Send text reply first (if any), then the image
                                        caption_for_image = final_text if final_text else None
                                        client.send_image(event.Info.MessageSource.Chat, target_image, caption=caption_for_image, quoted=event)
                                        
                                        db_manager.save_chat_and_message(
                                            account_id=self.account_id,
                                            chat_jid=chat_jid,
                                            chat_name=sender_name,
                                            message_id=reply_msg_id,
                                            sender_jid="",
                                            sender_name="ReplyHub AI",
                                            message_text=caption_for_image or f"[Photo: {product_name}]",
                                            timestamp=int(time.time()),
                                            is_from_me=True,
                                            media_path=saved_media_path,
                                            media_type="image"
                                        )
                                        self.chat_message_saved.emit(self.account_id, chat_jid)
                                        
                                        summary_item = f"[Photo: {product_name}]"
                                        if caption_for_image:
                                            cap_short = caption_for_image.replace('\n', ' ')
                                            if len(cap_short) > 30:
                                                cap_short = cap_short[:27] + "..."
                                            summary_item += f" ({cap_short})"
                                        sent_summary_parts.append(summary_item)
                                        
                                        # Text was consumed as caption, clear it
                                        final_text = ""
                            # ── End fallback ──
                            
                            if final_text:
                                client.reply_message(final_text, event)
                                reply_msg_id = client.generate_message_id()
                                
                                db_manager.save_chat_and_message(
                                    account_id=self.account_id,
                                    chat_jid=chat_jid,
                                    chat_name=sender_name,
                                    message_id=reply_msg_id,
                                    sender_jid="",
                                    sender_name="ReplyHub AI",
                                    message_text=final_text,
                                    timestamp=int(time.time()),
                                    is_from_me=True
                                )
                                self.chat_message_saved.emit(self.account_id, chat_jid)
                                
                                final_short = final_text.replace('\n', ' ')
                                if len(final_short) > 40:
                                    final_short = final_short[:37] + "..."
                                sent_summary_parts.append(final_short)
                                
                            if sent_summary_parts:
                                summary_str = " | ".join(sent_summary_parts)
                                if len(summary_str) > 150:
                                    summary_str = summary_str[:147] + "..."
                                self.message_received.emit(self.account_id, sender_num, text, summary_str)
                            else:
                                self.message_received.emit(self.account_id, sender_num, text, "")
                        else:
                            self.message_received.emit(self.account_id, sender_num, text, "")
                    except Exception as ai_err:
                        log.error(f"[Account {self.account_id}] Gemini AI error: {ai_err}")
                        self.message_received.emit(self.account_id, sender_num, text, f"[AI Error: {ai_err}]")
                else:
                    self.message_received.emit(self.account_id, sender_num, text, "")

        @self.client.event(HistorySyncEv)
        def on_history_sync(client: NewClient, event: HistorySyncEv):
            log.info(f"[Account {self.account_id}] Received HistorySync event of type {event.syncType}")
            try:
                for convo in event.conversations:
                    chat_jid = convo.ID
                    
                    # Ignore WhatsApp Status / Stories updates and Channels/Newsletters
                    if "broadcast" in chat_jid or "newsletter" in chat_jid:
                        continue

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
                        if msg and hasattr(msg, "HasField") and msg.HasField("imageMessage"):
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
