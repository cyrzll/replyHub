# ReplyHub - WhatsApp Auto Reply Bot & AI Customer Service

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-green.svg)](https://doc.qt.io/qtforpython-6/)
[![WhatsApp Engine](https://img.shields.io/badge/WhatsApp-Neonize%20(whatsmeow)-brightgreen.svg)](https://github.com/Krypton-Byte/neonize)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)

**ReplyHub** adalah aplikasi desktop modern berbasis GUI (PySide6) yang dirancang untuk mengelola otomatisasi pesan WhatsApp secara multi-akun. Aplikasi ini memungkinkan Anda untuk membuat bot penjawab otomatis (Auto-Reply) berbasis kata kunci konvensional, serta mengintegrasikan kecerdasan buatan dari **Google Gemini API** yang bertindak sebagai agen Customer Service (CS) pintar untuk melayani pelanggan toko online secara dinamis dan real-time.

---

## 🌟 Fitur Utama

1. **Netflix-Style Launcher (Multi-Profile)**
   - Dashboard premium yang memungkinkan pengelolaan beberapa profil WhatsApp/nomor sekaligus.
   - Fitur *Activate All* dan *Deactivate All* untuk mengontrol status koneksi bot secara masal.
   - Peralihan tema terintegrasi (Dark & Light Mode) dengan desain modern berbasis CSS kustom.

2. **Koneksi WhatsApp Instan (QR Code Dinamis)**
   - Tampilan dialog *QR Code* real-time berbasis engine `neonize` (Go whatsmeow) untuk menghubungkan akun melalui pemindaian perangkat bertautan.

3. **Auto-Reply Rules (Aturan Balasan Otomatis)**
   - Pembuatan aturan kustom berdasarkan kata kunci (keyword-matching) yang bersifat *case-insensitive*.
   - Mendukung balasan berupa teks saja atau kombinasi teks dengan lampiran foto (gambar).

4. **Gemini AI Auto-Responder (CS Pintar & Vision Multimodal)**
   - Terintegrasi dengan Google Gemini API (menggunakan model `gemini-2.5-flash` secara default).
   - **Kemampuan Vision**: Bot dapat mengenali dan menganalisis foto yang dikirim oleh pelanggan untuk merespons konteks visual.
   - **Dinamika Riwayat Chat**: Menyimpan dan mengirimkan hingga 10 riwayat percakapan terakhir ke API untuk menjaga konteks percakapan tetap nyambung (conversation memory).

5. **Katalog Produk & Pengiriman Gambar Otomatis**
   - Panel manajemen katalog produk lengkap dengan data nama, harga, stok, deskripsi, kategori, gender, persentase diskon, dan foto produk.
   - **Tag Image Trigger**: Jika pelanggan meminta foto atau detail produk (misal: *"lihat foto kaos"*), Gemini secara otomatis menyertakan tag khusus `{{SEND_IMAGE: <product_id>}}` yang diterjemahkan oleh bot untuk langsung mengirimkan berkas foto produk asli ke WhatsApp pelanggan.
   - **Fallback Image Detection**: Jika AI tidak memicu tag tetapi mendeteksi kata kunci foto/gambar secara semantik, bot akan mendeteksi kecocokan nama produk dari database dan mengirimkan gambarnya secara otomatis.

6. **Chat Workspace Lokal**
   - Halaman obrolan interaktif yang menampilkan daftar percakapan aktif di setiap akun.
   - Riwayat chat terperinci dengan tampilan gelembung percakapan (*chat bubble*) bergaya modern lengkap dengan status waktu.
   - Dukungan CRUD pesan lokal: Anda dapat mengedit teks pesan atau menghapus pesan langsung di database lokal aplikasi.

---

## 📂 Struktur Direktori Proyek

```directory
ReplyHub/
│
├── main.py                 # File utama aplikasi (Entrypoint GUI PySide6)
├── db_manager.py           # Logika inisialisasi & manajemen database SQLite3
├── ReplyHub.spec           # Konfigurasi bundler PyInstaller untuk build executable
├── requirements.txt        # Daftar dependensi modul Python
│
└── src/
    ├── data/               # Direktori penyimpanan data SQLite & file media
    │   ├── chat_data/      # chat_data.db (Auto reply rules)
    │   ├── chat_session/   # Riwayat memori sesi percakapan JSON untuk Gemini AI
    │   ├── media/          # Unduhan media & salinan foto produk terkirim
    │   ├── session/        # File DB kredenisal autentikasi nomor WhatsApp (.db)
    │   ├── theme/          # theme.db (Menyimpan preferensi tema Dark/Light)
    │   └── user/           # userdata.db (Akun, Chat log, Pesan, Katalog Produk)
    │
    ├── hooks/
    │   └── bot_thread.py   # Background thread (QThread) koneksi whatsmeow / Neonize
    │
    ├── lib/
    │   ├── __init__.py
    │   ├── dialogs.py      # Kelas kustom dialog (Tambah Akun, QR, Produk, Chat Baru)
    │   ├── jid_helper.py   # Utilitas parsing JID (WhatsApp ID format)
    │   └── widgets.py      # Widget kustom UI (ProfileCard, ChatItemWidget, MessageRowWidget)
    │
    └── style/
        └── themes.py       # Desain stylesheet CSS untuk Light & Dark Mode
```

---

## 🛠️ Persyaratan Sistem & Dependensi

* **Python 3.8 s/d 3.11** (Sangat disarankan Python 3.10)
* **Go Compiler (1.20+)** (Mungkin dibutuhkan untuk instalasi `neonize` agar dapat membuild library dinamis whatsmeow secara lokal jika platform belum mendukung binary piringan roda).
* Modul python utama yang digunakan:
  - `PySide6` (Qt6 UI Toolkit)
  - `segno` (Pembangkit gambar QR Code)
  - `neonize` (WhatsApp Go-whatsmeow wrapper)
  - `pillow` (Pemrosesan gambar lokal)
  - `protobuf` (Serialisasi data)

---

## 🚀 Instalasi & Menjalankan Aplikasi

Ikuti langkah-langkah di bawah ini untuk menjalankan ReplyHub di komputer lokal Anda:

### 1. Clone Repositori
```bash
git clone https://github.com/username/ReplyHub.git
cd ReplyHub
```

### 2. Buat & Aktifkan Virtual Environment (Opsional tapi disarankan)
**Di macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
**Di Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependensi
Instal semua pustaka yang diperlukan dengan menjalankan perintah:
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi
Jalankan file entrypoint `main.py` menggunakan Python:
```bash
python main.py
```

---

## 💾 Skema Database SQLite

Aplikasi ini menggunakan SQLite dengan tiga file database terpisah yang disimpan di direktori `src/data/`:

### A. `userdata.db` (src/data/user/)
Mengelola informasi profil WhatsApp, data katalog produk, riwayat obrolan, dan pesan chat:
* **`accounts`**: Menyimpan detail profil (ID akun, nama profil, nomor telepon, nama sesi database WhatsApp, status Gemini/Ollama, API Key, instruksi prompt AI, model).
* **`products`**: Menyimpan data katalog (Nama produk, harga, stok, deskripsi, diskon %, kategori, gender, path foto produk).
* **`chats`**: Metadata percakapan teraktif per akun untuk daftar sidebar chat.
* **`messages`**: Log pesan masuk & keluar lengkap (ID pesan, pengirim, teks, waktu, tipe media, path berkas unduhan).

### B. `chat_data.db` (src/data/chat_data/)
Menyimpan aturan auto-reply kustom:
* **`auto_replies`**: Menghubungkan kata kunci (*keyword*) dengan respons teks/gambar untuk masing-masing profil WhatsApp.

### C. `theme.db` (src/data/theme/)
Menyimpan pengaturan antar muka pengguna:
* **`settings`**: Menyimpan preferensi tema (value: `dark` atau `light`).

---

## 🤖 Konfigurasi Gemini AI Customer Service

Untuk mengaktifkan asisten AI pada salah satu profil WhatsApp:
1. Masuk ke profil WhatsApp yang diinginkan melalui Launcher.
2. Navigasikan ke tab **✨ Gemini AI** di sidebar kiri.
3. Centang pilihan **Enable Gemini AI**.
4. Masukkan **Gemini API Key** Anda (Dapatkan dari Google AI Studio).
5. Pilih model yang ingin digunakan (default: `gemini-2.5-flash`).
6. Atur **System Instruction** (Prompt arahan AI).
   * Gunakan tag `{{products}}` di dalam prompt. Aplikasi akan otomatis mengganti tag tersebut menjadi katalog produk terformat dari database lokal Anda saat bot mengirimkan permintaan ke API.

### Template Prompt Rekomendasi
```text
Kamu adalah bot Customer Service (CS) toko online yang ramah dan santai (panggil pelanggan dengan "kak").
Tugas kamu adalah membantu menjawab pertanyaan seputar produk kami, harga, stok, pemesanan, dan pengiriman.

Katalog Produk:
{{products}}
```

---

## 📦 Membangun Aplikasi (Build Standalone Executable)

Anda dapat membundel ReplyHub menjadi file aplikasi executable standalone (.exe di Windows atau App di macOS) menggunakan PyInstaller dan berkas konfigurasi `ReplyHub.spec`:

1. Pastikan `pyinstaller` sudah terinstal:
   ```bash
   pip install pyinstaller
   ```
2. Jalankan kompilasi menggunakan file spesifikasi:
   ```bash
   pyinstaller ReplyHub.spec
   ```
3. Executable hasil build akan tersedia di folder `dist/ReplyHub`.

---

## 🛡️ Lisensi & Kontribusi

Proyek ini dibangun untuk tujuan pembelajaran pemrograman berorientasi objek (PBO) dan otomatisasi. Jika Anda ingin berkontribusi, silakan lakukan fork pada repositori ini dan kirimkan Pull Request (PR) terbaik Anda.
