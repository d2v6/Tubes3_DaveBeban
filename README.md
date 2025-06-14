
# CV ATS (Applicant Tracking System) - Tubes 3 Stima

## 📋 Deskripsi
Sistem ATS untuk mencocokkan dan mencari informasi pelamar kerja berdasarkan CV yang diunggah. Sistem mengimplementasikan algoritma string matching (KMP, Boyer-Moore, Aho-Corasick) dan Levenshtein Distance untuk pencarian yang akurat.

## 🔐 **FITUR ENKRIPSI BONUS (5 Poin)**

### Implementasi Enkripsi Kustom
Sistem ini mengimplementasikan **enkripsi data profil applicant** tanpa menggunakan pustaka enkripsi bawaan Python (cryptography/hashlib). Fitur enkripsi meliputi:

#### 🛡️ **Algoritma Enkripsi Kustom**
- **Custom AES-like Block Cipher**: Implementasi cipher blok 128-bit dengan substitution boxes (S-boxes) kustom
- **Multiple Security Layers**: 
  - Substitution menggunakan S-box matematika berbasis Galois Field GF(256)
  - Permutation untuk scrambling posisi
  - Diffusion layer untuk penyebaran perubahan
- **Key Derivation**: Implementasi PBKDF2-like dengan 10,000 iterasi
- **CBC Mode**: Cipher Block Chaining untuk keamanan tambahan
- **Salt + IV**: Salt unik dan Initialization Vector untuk setiap enkripsi

#### 🔒 **Data yang Dienkripsi**
- `first_name` - Nama depan pelamar
- `last_name` - Nama belakang pelamar  
- `email` - Alamat email
- `phone_number` - Nomor telepon
- `address` - Alamat lengkap
- `date_of_birth` - Tanggal lahir

#### ⚙️ **Fitur Enkripsi**
- **Transparent Encryption**: Enkripsi/dekripsi otomatis saat akses data
- **Backward Compatibility**: Dapat membaca data lama (plaintext) dan data baru (encrypted)
- **Performance Optimized**: Enkripsi cepat dengan overhead minimal
- **Database Security**: Data tersimpan terenkripsi di database
- **Migration Tool**: Tool untuk mengenkripsi data eksisting

## 🎯 Fitur Utama
- ✅ Ekstraksi teks dari PDF CV
- ✅ Penyimpanan data ke MySQL database
- ✅ **🔐 ENKRIPSI DATA PROFIL (BONUS)**
- ✅ Pencarian dengan algoritma KMP, Boyer-Moore, dan Aho-Corasick
- ✅ Fuzzy matching dengan Levenshtein Distance
- ✅ Ekstraksi informasi CV dengan Regular Expression
- ✅ Interface desktop dengan Flet
- ✅ Tampilan ringkasan dan CV lengkap

## 🛠️ Teknologi
- **Language**: Python 3.8+
- **GUI Framework**: Flet
- **Database**: MySQL
- **PDF Processing**: PyPDF2
- **🔐 Encryption**: Custom AES-like implementation (tanpa library bawaan)
- **String Algorithms**: KMP, Boyer-Moore, Aho-Corasick, Levenshtein

## 📁 Struktur Project
```
Tubes3_DaveBeban/
├── src/
│   ├── algorithms/         # String matching algorithms
│   ├── database/          # Database connection & repository
│   │   ├── encrypted_repository.py  # 🔐 Encrypted database layer
│   ├── models/            # Data models
│   │   ├── encrypted_models.py      # 🔐 Encrypted data models
│   ├── ui/               # User interface components
│   ├── utils/            # Utilities
│   │   ├── encryption.py            # 🔐 Custom encryption system
│   └── main.py           # Entry point
├── data/
│   └── cvs/              # CV storage directory
├── encryption_manager.py  # 🔐 Encryption management CLI
├── requirements.txt      # Dependencies
├── .env                 # Environment variables
└── README.md
```

## 🚀 Instalasi dan Setup

### Method 1: Automatic Setup (Recommended)
```bash
# Windows
setup_encryption.bat

# Linux/Mac
chmod +x setup_encryption.sh
./setup_encryption.sh
```

### Method 2: Manual Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd Tubes3_DaveBeban
```

#### 2. Setup Virtual Environment
```bash
# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
# Windows:
venv\Scripts\activate
# Git Bash:
source venv/Scripts/activate
# Linux/Mac:
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Setup Database
1. Install MySQL Server
2. Buat database baru:
```sql
CREATE DATABASE cv_ats;
```

3. Copy `.env.example` ke `.env` dan sesuaikan konfigurasi:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cv_ats

# Encryption Settings
ENCRYPTION_MASTER_KEY=CV_ATS_SECURE_MASTER_KEY_2024_STIMA_ITB
ENCRYPTION_ENABLED=true
BACKWARD_COMPATIBILITY=true
```

#### 5. Setup Database Schema
```bash
# Akan dibuat otomatis saat pertama kali menjalankan aplikasi
python seed_database.py
```

## 🔐 **MANAJEMEN ENKRIPSI**

### Menggunakan Encryption Manager CLI
```bash
# Test sistem enkripsi
python encryption_manager.py --test

# Lihat status enkripsi
python encryption_manager.py --status

# Aktifkan enkripsi untuk data baru
python encryption_manager.py --enable

# Nonaktifkan enkripsi (mode demo)
python encryption_manager.py --disable

# Migrasi data eksisting ke format terenkripsi
python encryption_manager.py --migrate

# Buat data demo terenkripsi
python encryption_manager.py --demo

# Benchmark performa enkripsi
python encryption_manager.py --benchmark
```

### Cara Kerja Enkripsi

#### 1. **Enkripsi Transparan**
```python
# Data otomatis terenkripsi saat disimpan
profile = ApplicantProfile(
    first_name="John",
    last_name="Doe", 
    email="john.doe@example.com"
)
# Disimpan terenkripsi di database

# Data otomatis terdekripsi saat diambil
retrieved_profile = repo.get_profile(id)
print(retrieved_profile.first_name)  # "John" (sudah terdekripsi)
```

#### 2. **Backward Compatibility**
```bash
# Sistem dapat membaca data lama (plaintext) dan baru (encrypted)
# Migration tool tersedia untuk mengenkripsi data eksisting
python encryption_manager.py --migrate
```

#### 3. **Keamanan Data**
- Data sensitif tersimpan dalam format base64 terenkripsi
- Setiap field menggunakan salt dan IV unik
- Key derivation dengan 10,000 iterasi untuk keamanan tinggi
- Tidak ada kunci enkripsi yang tersimpan dalam kode

## 🎮 Cara Menjalankan

### Method 1: Menggunakan Flet
```bash
# Pastikan virtual environment aktif
flet run src/main.py
```

### Method 2: Menggunakan Python
```bash
python src/main.py
```

## 📊 Penggunaan

### 1. Upload CV
- Klik "Select PDF Files" untuk memilih file CV
- Sistem akan otomatis mengekstrak teks dan informasi
- **Data profil akan terenkripsi otomatis jika enkripsi aktif**

### 2. Pencarian CV
- Masukkan kata kunci (dipisah koma)
- Pilih algoritma pencarian (KMP/Boyer-Moore/Aho-Corasick)
- Atur jumlah hasil maksimal
- Klik "Start Search"
- **Sistem akan otomatis mendekripsi data untuk pencarian**

### 3. Lihat Hasil
- CV akan ditampilkan berdasarkan skor kemiripan
- Klik CV untuk melihat detail lengkap
- Informasi waktu pencarian ditampilkan
- **Data profil ditampilkan dalam bentuk terdekripsi**

## 🔧 Konfigurasi

### Environment Variables (.env)
```env
# Database
DB_HOST=localhost      # MySQL host
DB_USER=root          # MySQL username
DB_PASSWORD=          # MySQL password
DB_NAME=cv_ats        # Database name

# 🔐 Encryption Settings
ENCRYPTION_MASTER_KEY=CV_ATS_SECURE_MASTER_KEY_2024_STIMA_ITB
ENCRYPTION_ENABLED=true
BACKWARD_COMPATIBILITY=true
```

### Struktur Database
- `ApplicantProfile`: Data profil pelamar (**fields sensitif terenkripsi**)
- `ApplicationDetail`: Detail aplikasi dan path CV
- CV files disimpan di folder `data/cvs/`

### Database Schema (Encrypted Fields)
```sql
CREATE TABLE ApplicantProfile (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name TEXT,        -- 🔐 ENCRYPTED
    last_name TEXT,         -- 🔐 ENCRYPTED  
    email TEXT,             -- 🔐 ENCRYPTED
    phone_number TEXT,      -- 🔐 ENCRYPTED
    address TEXT,           -- 🔐 ENCRYPTED
    date_of_birth TEXT,     -- 🔐 ENCRYPTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

### Test Enkripsi
```bash
# Test lengkap sistem enkripsi
python encryption_manager.py --test

# Test performa enkripsi
python encryption_manager.py --benchmark
```

### Test Algoritma
```bash
python -c "
from src.algorithms.string_matcher import StringMatcher
matcher = StringMatcher()
# Test KMP
print(matcher.kmp_search('hello world', 'world'))
# Test Boyer-Moore  
print(matcher.boyer_moore_search('hello world', 'world'))
"
```

### Test Database Connection
```bash
python -c "
from src.database.connection import DatabaseConnection
db = DatabaseConnection()
print('Connected:', db.connect())
"
```

### Test Encrypted Database
```bash
python -c "
from src.database.encrypted_repository import EncryptedCVRepository
repo = EncryptedCVRepository()
repo.test_encryption_functionality()
"
```

## 📋 Checklist Spesifikasi

### ✅ Implementasi Algoritma
- [x] Knuth-Morris-Pratt (KMP)
- [x] Boyer-Moore
- [x] Aho-Corasick (Bonus)
- [x] Levenshtein Distance
- [x] Regular Expression untuk ekstraksi

### ✅ Fitur Utama
- [x] Ekstraksi PDF ke teks
- [x] Penyimpanan ke MySQL
- [x] Pencarian exact matching
- [x] Fuzzy matching
- [x] Tampilan ringkasan CV
- [x] Pemilihan algoritma
- [x] Pengaturan jumlah hasil
- [x] Tampilan waktu pencarian

### ✅ Interface
- [x] GUI desktop (Flet)
- [x] Input kata kunci
- [x] Pemilihan algoritma
- [x] Hasil pencarian terurut
- [x] Detail CV

### 🔐 **BONUS: Enkripsi Data (5 Poin)**
- [x] **Custom encryption algorithm** (tanpa library bawaan)
- [x] **Field-level encryption** untuk data sensitif
- [x] **Transparent encryption/decryption**
- [x] **Backward compatibility** dengan data lama
- [x] **Key derivation** dan salt-based security
- [x] **Migration tools** untuk data eksisting
- [x] **Performance optimization**
- [x] **Multiple security layers** (substitution, permutation, diffusion)

## 🐛 Troubleshooting

### Error: "flet: command not found"
```bash
pip install flet
# atau
python -m pip install flet
```

### Error: MySQL Connection
1. Pastikan MySQL server berjalan
2. Periksa kredensial di `.env`
3. Pastikan database `cv_ats` sudah dibuat

### Error: PDF parsing
1. Pastikan file PDF tidak terproteksi
2. Install ulang PyPDF2: `pip install --upgrade PyPDF2`

### Error: Encryption
1. Periksa `ENCRYPTION_MASTER_KEY` di `.env`
2. Test dengan: `python encryption_manager.py --test`
3. Untuk reset: `python encryption_manager.py --disable`

## 🔐 Keamanan Enkripsi

### Algoritma yang Diimplementasikan
1. **Custom Block Cipher**: AES-like dengan 128-bit blocks
2. **S-box Generation**: Matematika berbasis Galois Field GF(256)
3. **Key Derivation**: PBKDF2-like dengan 10,000 iterasi
4. **CBC Mode**: Cipher Block Chaining untuk keamanan
5. **Salt + IV**: Randomness untuk setiap enkripsi

### Tingkat Keamanan
- **256-bit keys** dari master key
- **10,000 iterations** untuk key derivation
- **Unique salt** untuk setiap data
- **Initialization vectors** untuk CBC mode
- **No hardcoded keys** dalam source code

### Compliance
- Data sensitif tidak tersimpan dalam plaintext
- Enkripsi transparent untuk aplikasi
- Backward compatibility untuk demo data
- Migration path untuk data eksisting

## 👥 Tim Pengembang
- **Dave & Beban Team**
- Tugas Besar 3 - Strategi Algoritma
- Institut Teknologi Bandung

## 📝 Lisensi
Project ini dibuat untuk keperluan akademik ITB.
