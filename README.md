# CV ATS (Applicant Tracking System) - Tubes 3 Stima - DaveBeban

## 📋 Deskripsi Singkat
Sistem ATS untuk mencocokkan dan mencari informasi pelamar kerja berdasarkan CV yang diunggah menggunakan algoritma string matching.

## 🔍 Algoritma yang Diimplementasikan

### Knuth-Morris-Pratt (KMP)
Algoritma pencarian string yang menggunakan preprocessing untuk membangun failure function (border function) untuk menghindari pemeriksaan karakter yang tidak perlu. KMP memiliki kompleksitas waktu O(n + m) di mana n adalah panjang teks dan m adalah panjang pattern.

**Cara Kerja:**
1. Preprocessing: Membangun tabel failure function dari pattern
2. Searching: Menggunakan failure function untuk melompati karakter yang sudah cocok
3. Efisien karena tidak pernah mundur pada teks utama

### Boyer-Moore (BM)
Algoritma pencarian string yang melakukan pencarian dari kanan ke kiri pada pattern. Menggunakan bad character heuristic untuk melompati posisi yang tidak mungkin cocok.

**Cara Kerja:**
1. Preprocessing: Membangun tabel bad character untuk setiap karakter
2. Searching: Mulai dari ujung kanan pattern, jika tidak cocok gunakan bad character rule
3. Efisien untuk pattern panjang dan alphabet besar

### Aho-Corasick
Algoritma pencocokan banyak pola (multi-pattern matching) berbasis struktur automaton (trie + failure link), ideal untuk mendeteksi banyak kata kunci sekaligus dalam satu kali pemindaian teks.

Kompleksitas waktu: O(n + m + z),
dengan:
1. n = panjang teks,
2. m = total panjang semua pattern,
3. z = total hasil kemunculan.

Cara Kerja:
Build Trie: Bangun trie dari semua pattern/kata kunci.
Build Failure Link: Tambahkan failure link ke simpul yang paling panjang yang dapat menjadi fallback saat mismatch.
Searching: Pindai teks satu arah, transisi antar simpul, dan hasilkan kemunculan semua pattern yang cocok.

Kelebihan:
Dapat mencocokkan banyak kata kunci sekaligus.
Cocok untuk aplikasi skala besar seperti filtering konten, pencarian cepat, dan deteksi entitas.

## 🛠️ Requirements

### Sistem Requirements
- **Python**: 3.8 atau lebih tinggi
- **Operating System**: Windows, macOS, atau Linux
- **Database**: MySQL Server 5.7+
- **Memory**: Minimal 512MB RAM
- **Storage**: 100MB ruang kosong

### Python Dependencies
```txt
flet==0.25.1
pdfplumber
mysql-connector-python>=8.0.33
python-dotenv>=1.0.0
regex>=2023.10.3
```

## 🚀 Instalasi dan Setup

### 1. Persiapan Environment
```bash
# Clone repository
git clone https://github.com/d2v6/Tubes3_DaveBeban.git
cd Tubes3_DaveBeban

# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/Scripts/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Master Key
```bash
python keygen.py
```

### 4. Setup env sesuai example

### 5. Setup Database MySQL

```bash
python setup_database.py
```

```bash
cd seeder/
python seeder.py
```

## 🔧 Compile/Build dan Menjalankan Program

### Method 1: Direct Python Execution
```bash
# Pastikan virtual environment aktif
python src/main.py
```

### Method 2: Menggunakan Flet
```bash
# Menjalankan dengan Flet (Recommended)
flet run src/main.py
```

## 📖 Langkah Penggunaan

### 1. Pencarian CV
- Masukkan kata kunci pencarian (dipisah koma)
- Pilih algoritma: KMP atau Boyer-Moore
- Atur jumlah hasil maksimal yang ditampilkan
- Klik "Start Search"

### 2. Lihat Hasil
- CV ditampilkan berdasarkan skor kemiripan
- Klik CV untuk melihat detail lengkap
- Informasi waktu pencarian ditampilkan

## Fitur Bonus: 
1. Enkripsi Data
2. Algoritma Aho-Corasick
3. Video: https://youtu.be/pEbHx77tQPo


## 📁 Struktur Project
```
Tubes3_DaveBeban/
├── src/
│   ├── algorithms/         # Implementasi KMP dan Boyer-Moore
│   ├── database/          # Koneksi dan repository database
│   ├── models/            # Data models
│   ├── ui/               # User interface components
│   ├── utils/            # Utilities dan enkripsi
│   └── main.py           # Entry point aplikasi
├── data/             # Storage CV files
├── requirements.txt      # Dependencies
└── .env                 # Konfigurasi environment
```

## 👥 Author
| NIM      | Nama                          |
|----------|-------------------------------|
| 13523003 | Dave Daniell Yanni            |
| 13523008 | Varel Tiara                   |
| 13523097 | Shanice Feodora Tjahjono      |
