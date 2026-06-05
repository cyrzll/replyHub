# Design System & UI Documentation - ReplyHub

Dokumentasi ini menjelaskan filosofi desain, palet warna, tipografi, komponen antarmuka, serta mekanisme interaktif yang diterapkan pada **ReplyHub** setelah migrasi dari gaya Neo-Brutalist ke sistem **Modern Premium UI / SaaS Dashboard**.

---

## 🌟 1. Filosofi Desain

ReplyHub kini mengadopsi pendekatan **SaaS-style Dashboard** yang berfokus pada kenyamanan mata, estetika premium, kejelasan informasi, dan interaksi yang halus (*smooth*).

* **Sudut Melengkung (Rounded Corners):** Menghilangkan semua sudut siku kaku (`0px`). Sebagai gantinya, sudut luar jendela dan panel utama menggunakan kelengkungan `12px` (Medium-Large), sedangkan tombol, kolom input, dan item list menggunakan `8px` (Medium) untuk memberikan kesan ramah dan modern.
* **Garis Batas Halus (Soft Thin Borders):** Ketebalan garis tepi diturunkan menjadi `1px` solid, menggunakan warna kontras rendah seperti abu-abu netral (`#e2e8f0` / `#cbd5e1`) untuk membagi area layar tanpa membuat visual terasa sesak.
* **Warna Aksen Semantik (Semantic Accents):** Menggunakan warna bernilai semantik tinggi untuk menandakan fungsionalitas:
  - Biru Indigo (`#2563eb`): Aksen fokus, input aktif, dan link.
  - Slate Dark (`#0f172a`): Highlight utama, tombol sekunder, dan status terpilih.
  - Hijau/Kuning/Merah: Untuk indikasi dinamis status WhatsApp (Connected, Connecting, Disconnected).
* **Efek Interaktif & Hover:** Transisi perpindahan halaman dan perubahan status hover pada tombol didesain secara halus menggunakan perubahan latar belakang pastel yang redup.

---

## 🎨 2. Palet Warna (Color System)

Palet warna utama berbasis pada skema **Grayscale Premium / Slate** dengan aksen fungsional yang tajam namun lembut di mata.

### Light Mode (Default & Utama)

| Kategori | Nilai Hex | Penggunaan Utama |
| :--- | :--- | :--- |
| **Primary Background** | `#ffffff` | Halaman kerja utama, kartu, panel aktif |
| **Secondary Background**| `#f8fafc` | Latar belakang sidebar kiri, header obrolan, input area |
| **Surface Hover** | `#f1f5f9` | Hover menu, baris obrolan aktif, tombol hover |
| **Primary Text** | `#0f172a` | Judul, nama kontak, pesan keluar, tombol utama |
| **Secondary Text/Muted**| `#64748b` | Subtitle, preview pesan terakhir, waktu, detail JID |
| **Border Neutral** | `#e2e8f0` | Pembatas antar-panel, pembatas atas/bawah |
| **Border Input** | `#cbd5e1` | Garis tepi default untuk text field, spinbox, dan combobox |
| **Accent Primary** | `#2563eb` | Status aktif/fokus input, tombol aksi utama |
| **Destructive/Danger** | `#ef4444` | Tombol hapus, peringatan, status disconnect |

### Dark Mode (Fallback / Kompatibilitas)

Untuk kompatibilitas, skema gelap menggunakan gradasi zinc/gray:
- **Background**: `#1e1e24`
- **Surface**: `#27272a`
- **Border**: `#3f3f46`
- **Text**: `#ffffff`

---

## ✍️ 3. Tipografi

Sistem tipografi dirancang untuk menjaga keterbacaan tinggi di berbagai resolusi layar.

* **Font Utama (Interface & Obrolan):** `'Poppins', 'Segoe UI', Helvetica, sans-serif`
  - Memberikan nuansa antarmuka modern, bersih, dengan kerning proporsional.
* **Font Teknis (Status & Waktu):** `'Courier New', Courier, monospace`
  - Digunakan khusus untuk JID WhatsApp (`JID`), penunjuk waktu (*timestamp*), serta log konsol aktivitas bot di tab monitor.

---

## 🧩 4. Spesifikasi Komponen & Widget

### A. Netflix-Style Launcher Cards (Profil Akun)
- **Struktur**: Box ukuran `160x200 px` dengan sudut melengkung `12px` dan border tipis `1px solid #e2e8f0`.
- **Avatar**: Berbentuk lingkaran sempurna (`border-radius: 35px` dari dimensi `70x70 px`) menggunakan warna latar abu-abu muda (`#f1f5f9`) dan teks inisial gelap (`#0f172a`).
- **Overlay Buttons**: Tombol rename (✏️) dan toggle bot (▶️/⏹️) berbentuk bulat kecil (`border-radius: 12px` dari dimensi `24x24 px`) yang menyatu halus saat melayang di atas kartu.

### B. Chat List Workspace (Sidebar Kiri)
- **Floating Row**: List item tidak lagi saling menempel rapat. Setiap baris obrolan memiliki margin samping, tinggi yang pas, dan kelengkungan `8px` sehingga terlihat seperti baris kartu melayang yang teratur.
- **Inversi Otomatis saat Terpilih (Selected State)**:
  - Ketika kontak dipilih, list item berubah warna latar menjadi hitam slate (`#0f172a`).
  - Teks nama kontak, preview pesan, dan waktu otomatis berubah warna menjadi putih (`#ffffff`).
  - Avatar kontak berinversi secara visual menjadi berlatar putih dengan teks hitam.

### C. Chat Bubble (Ruang Pesan)
- **Pesan Keluar (Sent - Me)**: Latar belakang gelap (`#0f172a`), teks putih (`#ffffff`), tanpa garis batas, dengan sudut melengkung `12px` dan sudut lancip di bagian bawah-kanan (`border-bottom-right-radius: 2px`).
- **Pesan Masuk (Received - Others)**: Latar belakang abu-abu sangat muda (`#f1f5f9`), teks hitam (`#0f172a`), tanpa garis batas, dengan sudut melengkung `12px` dan sudut lancip di bagian bawah-kiri (`border-bottom-left-radius: 2px`).

### D. Status Indicator Pill (Badge Koneksi)
Digunakan sebagai indikator visual status bot dengan gaya capsule badge modern (`border-radius: 10px`, tanpa border, teks tebal `11px`):
- **CONNECTED**: Latar `#dcfce7` (Hijau Muda), teks `#166534` (Hijau Tua).
- **CONNECTING...**: Latar `#fef9c3` (Kuning Muda), teks `#854d0e` (Cokelat Tua).
- **DISCONNECTED**: Latar `#fee2e2` (Merah Muda), teks `#991b1b` (Merah Tua).
- **NO ACTIVE SELECTION**: Latar `#f1f5f9` (Abu-abu), teks `#64748b` (Abu-abu Tua).

---

## ⚡ 5. Mekanisme Qt Stylesheet Pembaruan Dinamis

Karena PySide6/Qt tidak meneruskan selektor CSS `:selected` dari parent `QListWidget::item` ke widget kustom (seperti `ChatItemWidget`) secara default, ReplyHub menerapkan metode pembaruan dinamis:

1. **Sinkronisasi Sinyal**: Event `currentItemChanged` dipantau di `main.py`.
2. **Propagasi Property**: Status aktif dikirimkan ke widget kustom melalui method `setSelected(self, selected)`.
3. **Dynamic CSS Matching**: Method tersebut menyetel property dynamic Qt `selected="true"` atau `selected="false"` ke seluruh label anak (Name, Time, Preview, Avatar).
4. **Style Repainting**: Perintah `polish()` dan `unpolish()` dieksekusi seketika pada komponen untuk memaksa mesin Qt me-render ulang visual stylesheet tanpa perlu merestart aplikasi atau merusak status memori GUI.
