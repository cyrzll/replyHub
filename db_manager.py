import sqlite3
import os
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).resolve().parent
DB_DIR = PROJECT_DIR / "src" / "data" / "chat_data"
DB_FILE = DB_DIR / "chat_data.db"

USER_DB_DIR = PROJECT_DIR / "src" / "data" / "user"
USER_DB_FILE = USER_DB_DIR / "userdata.db"

THEME_DIR = PROJECT_DIR / "src" / "data" / "theme"
THEME_DB = THEME_DIR / "theme.db"

def init_db():
    """Initializes the database directory and the auto_replies table."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # Check if table exists and columns
    cursor.execute("PRAGMA table_info(auto_replies)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if columns:
        if "account_id" not in columns:
            # Table exists but has old schema. Drop it to start fresh with new schema.
            cursor.execute("DROP TABLE auto_replies")
            conn.commit()
            columns = []
        elif "image_path" not in columns:
            cursor.execute("ALTER TABLE auto_replies ADD COLUMN image_path TEXT")
            conn.commit()
            
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            reply TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, keyword)
        )
    """)
    conn.commit()
    conn.close()

def init_user_db():
    """Initializes the user accounts database."""
    USER_DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(USER_DB_FILE))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            push_name TEXT,
            session_name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Account CRUD methods
def add_account(session_name, push_name=None):
    """Adds a new account with a unique session name and optional custom name."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (session_name, push_name) VALUES (?, ?)", (session_name, push_name))
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return account_id
    except Exception as e:
        print(f"Error adding account: {e}")
        return None

def update_account_info(account_id, phone_number, push_name):
    """Updates account's phone number and optionally push name once bot connects."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        
        # Check if current push_name is empty or default
        cursor.execute("SELECT push_name FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        current_name = row[0].strip() if (row and row[0]) else ""
        
        if not current_name or current_name in ("New Account", "Linked Account", "WhatsApp Account"):
            # Overwrite only if empty or default name
            cursor.execute(
                "UPDATE accounts SET phone_number = ?, push_name = ? WHERE id = ?",
                (phone_number, push_name or "Linked Account", account_id)
            )
        else:
            # Preserve current custom profile name
            cursor.execute(
                "UPDATE accounts SET phone_number = ? WHERE id = ?",
                (phone_number, account_id)
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating account info: {e}")
        return False

def get_all_accounts():
    """Retrieves all accounts."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone_number, push_name, session_name, created_at FROM accounts ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error getting accounts: {e}")
        return []

def delete_account(account_id):
    """Deletes an account, its rules, and its session file."""
    try:
        # First get the session name to delete the session file
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("SELECT session_name FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        
        if row:
            session_name = row[0]
            # Delete session DB file
            session_file = PROJECT_DIR / "src" / "data" / "session" / f"{session_name}.db"
            if session_file.exists():
                try:
                    session_file.unlink()
                except Exception as ex:
                    print(f"Error deleting session file: {ex}")
            
            # Delete rules associated with this account
            conn_rules = sqlite3.connect(str(DB_FILE))
            cursor_rules = conn_rules.cursor()
            cursor_rules.execute("DELETE FROM auto_replies WHERE account_id = ?", (account_id,))
            conn_rules.commit()
            conn_rules.close()
            
            # Delete account record
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting account: {e}")
        return False

# Rule CRUD methods
def get_all_replies(account_id):
    """Retrieves all auto-reply records for a specific account."""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute("SELECT id, keyword, reply, image_path, created_at FROM auto_replies WHERE account_id = ? ORDER BY id DESC", (account_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_reply(account_id, keyword, reply, image_path=None):
    """Adds a new auto-reply for an account. Returns (success, message)."""
    keyword = keyword.strip()
    reply = reply.strip()
    if not keyword:
        return False, "Keyword cannot be empty."
    if not reply and not image_path:
        return False, "Reply text or image must be specified."

    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO auto_replies (account_id, keyword, reply, image_path) VALUES (?, ?, ?, ?)", (account_id, keyword, reply, image_path))
        conn.commit()
        conn.close()
        return True, "Successfully added!"
    except sqlite3.IntegrityError:
        return False, f"Keyword '{keyword}' already exists for this account!"
    except Exception as e:
        return False, str(e)

def update_reply(account_id, reply_id, keyword, reply, image_path=None):
    """Updates an existing auto-reply. Returns (success, message)."""
    keyword = keyword.strip()
    reply = reply.strip()
    if not keyword:
        return False, "Keyword cannot be empty."
    if not reply and not image_path:
        return False, "Reply text or image must be specified."

    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        cursor.execute("UPDATE auto_replies SET keyword = ?, reply = ?, image_path = ? WHERE id = ? AND account_id = ?", (keyword, reply, image_path, reply_id, account_id))
        conn.commit()
        conn.close()
        return True, "Successfully updated!"
    except sqlite3.IntegrityError:
        return False, f"Keyword '{keyword}' already exists for this account!"
    except Exception as e:
        return False, str(e)

def delete_reply(reply_id):
    """Deletes an auto-reply record by ID."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auto_replies WHERE id = ?", (rule_id := reply_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting record: {e}")
        return False

def get_reply_for_message(account_id, message_text):
    """Checks if the message text matches any keyword (case-insensitive) for this account and returns (reply, image_path)."""
    if not message_text:
        return None, None
    
    clean_text = message_text.strip().lower()
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute("SELECT reply, image_path FROM auto_replies WHERE account_id = ? AND LOWER(keyword) = ?", (account_id, clean_text))
    row = cursor.fetchone()
    conn.close()
    return (row[0], row[1]) if row else (None, None)

# Theme database configurations
def init_theme_db():
    """Initializes the theme database directory and table."""
    THEME_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(THEME_DB))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    # Set default theme to 'dark' if it doesn't exist
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'dark')")
    conn.commit()
    conn.close()

def get_theme() -> str:
    """Retrieves the current saved theme from the database."""
    conn = sqlite3.connect(str(THEME_DB))
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'theme'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "dark"

def set_theme(theme_name: str):
    """Saves the theme selection to the database."""
    conn = sqlite3.connect(str(THEME_DB))
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', ?)", (theme_name,))
    conn.commit()
    conn.close()

def update_profile_name(account_id, new_name):
    """Updates the custom profile name (push_name) for an account."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET push_name = ? WHERE id = ?", (new_name, account_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating profile name: {e}")
        return False

def init_chat_store():
    """Initializes chats and messages tables in the userdata.db database."""
    USER_DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(USER_DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            chat_jid TEXT NOT NULL,
            chat_name TEXT,
            unread_count INTEGER DEFAULT 0,
            last_message TEXT,
            last_message_time TIMESTAMP,
            UNIQUE(account_id, chat_jid)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            chat_jid TEXT NOT NULL,
            message_id TEXT NOT NULL,
            sender_jid TEXT NOT NULL,
            sender_name TEXT,
            message_text TEXT,
            timestamp TIMESTAMP,
            is_from_me BOOLEAN,
            media_path TEXT,
            media_type TEXT,
            UNIQUE(account_id, chat_jid, message_id)
        )
    """)
    
    # Run migration to convert existing millisecond timestamps to seconds
    try:
        cursor.execute("UPDATE messages SET timestamp = timestamp / 1000 WHERE timestamp > 9999999999")
        cursor.execute("UPDATE chats SET last_message_time = last_message_time / 1000 WHERE last_message_time > 9999999999")
    except Exception as ex:
        print(f"Error running database migration: {ex}")
        
    conn.commit()
    conn.close()

def save_chat_and_message(account_id, chat_jid, chat_name, message_id, sender_jid, sender_name, message_text, timestamp, is_from_me, media_path=None, media_type=None):
    """Saves a message to message logs and updates the active conversation list metadata."""
    try:
        # Normalize timestamp from milliseconds to seconds if necessary
        if timestamp and timestamp > 9999999999:
            timestamp = timestamp // 1000
            
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        
        # 1. Insert message
        cursor.execute("""
            INSERT OR IGNORE INTO messages 
            (account_id, chat_jid, message_id, sender_jid, sender_name, message_text, timestamp, is_from_me, media_path, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (account_id, chat_jid, message_id, sender_jid, sender_name, message_text, timestamp, is_from_me, media_path, media_type))
        
        # 2. Update last message preview or create conversation record
        cursor.execute("""
            INSERT INTO chats (account_id, chat_jid, chat_name, last_message, last_message_time)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(account_id, chat_jid) DO UPDATE SET
                chat_name = COALESCE(excluded.chat_name, chat_name),
                last_message = excluded.last_message,
                last_message_time = excluded.last_message_time
        """, (account_id, chat_jid, chat_name, message_text, timestamp))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving chat and message: {e}")
        return False

def get_chats_for_account(account_id):
    """Retrieves all active chats for a user account, ordered by latest activity."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, chat_jid, chat_name, unread_count, last_message, last_message_time
            FROM chats
            WHERE account_id = ?
            ORDER BY last_message_time DESC
        """, (account_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error getting chats: {e}")
        return []

def get_messages_for_chat(account_id, chat_jid):
    """Retrieves the full message history for a specific chat conversation."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, message_id, sender_jid, sender_name, message_text, timestamp, is_from_me, media_path, media_type
            FROM messages
            WHERE account_id = ? AND chat_jid = ?
            ORDER BY timestamp ASC
        """, (account_id, chat_jid))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []


def delete_message(account_id, chat_jid, message_id):
    """Deletes a message locally and updates the last message metadata in chats."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM messages 
            WHERE account_id = ? AND chat_jid = ? AND message_id = ?
        """, (account_id, chat_jid, message_id))
        
        # Get remaining latest message
        cursor.execute("""
            SELECT message_text, timestamp 
            FROM messages 
            WHERE account_id = ? AND chat_jid = ? 
            ORDER BY timestamp DESC, id DESC LIMIT 1
        """, (account_id, chat_jid))
        row = cursor.fetchone()
        
        if row:
            last_text, last_time = row
        else:
            last_text, last_time = "", 0
            
        cursor.execute("""
            UPDATE chats 
            SET last_message = ?, last_message_time = ?
            WHERE account_id = ? AND chat_jid = ?
        """, (last_text, last_time, account_id, chat_jid))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting message: {e}")
        return False


def edit_message(account_id, chat_jid, message_id, new_text):
    """Updates a message locally and updates the last message metadata if necessary."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE messages 
            SET message_text = ? 
            WHERE account_id = ? AND chat_jid = ? AND message_id = ?
        """, (new_text, account_id, chat_jid, message_id))
        
        # Check if it was the latest message
        cursor.execute("""
            SELECT message_id 
            FROM messages 
            WHERE account_id = ? AND chat_jid = ? 
            ORDER BY timestamp DESC, id DESC LIMIT 1
        """, (account_id, chat_jid))
        row = cursor.fetchone()
        
        if row and row[0] == message_id:
            cursor.execute("""
                UPDATE chats 
                SET last_message = ? 
                WHERE account_id = ? AND chat_jid = ?
            """, (new_text, account_id, chat_jid))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error editing message: {e}")
        return False


def create_empty_chat(account_id, chat_jid, chat_name):
    """Creates a new empty chat record in the database if it doesn't exist."""
    try:
        conn = sqlite3.connect(str(USER_DB_FILE))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO chats (account_id, chat_jid, chat_name, last_message, last_message_time)
            VALUES (?, ?, ?, ?, ?)
        """, (account_id, chat_jid, chat_name, "", 0))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating empty chat: {e}")
        return False

