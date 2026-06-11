import os
import shutil
from pathlib import Path
import sqlite3

# Import db_manager
try:
    import db_manager
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import db_manager

def reset_and_initialize():
    print("Mulai inisialisasi database sesuai DATABASE.md...")
    
    # Path database files
    db_paths = [
        db_manager.DB_FILE,
        db_manager.USER_DB_FILE,
        db_manager.THEME_DB
    ]
    
    # Hapus file database jika ada untuk memulai ulang secara bersih
    for db_path in db_paths:
        if db_path.exists():
            try:
                print(f"Menghapus database lama: {db_path.name}...")
                db_path.unlink()
            except Exception as e:
                print(f"Gagal menghapus {db_path.name}: {e}")
        else:
            # Buat direktori jika belum ada
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
    # Panggil fungsi inisialisasi dari db_manager
    print("Membuat tabel dan skema database baru...")
    db_manager.init_db()
    db_manager.init_user_db()
    db_manager.init_theme_db()
    db_manager.init_chat_store()
    
    print("\nVerifikasi database yang berhasil dibuat:")
    for db_path in db_paths:
        if db_path.exists():
            print(f"[OK] {db_path.name} berhasil dibuat di {db_path.relative_to(Path.cwd())}")
            # Tampilkan tabel di dalamnya
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
            print(f"     Tabel: {', '.join(tables)}")
            conn.close()
        else:
            print(f"[FAIL] {db_path.name} gagal dibuat.")

if __name__ == "__main__":
    reset_and_initialize()
