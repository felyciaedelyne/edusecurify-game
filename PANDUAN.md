# Langkah cepat (versi game baru)

1. Ekstrak zip ini, buka foldernya di VS Code (File > Open Folder).
2. Terminal > New Terminal, lalu jalankan:
```
python -m pip install -r requirements.txt
python server.py
```
3. Buka http://localhost:5000 di browser. Layar loading muncul sebentar, lalu ikuti arahan maskot Bima.
4. Cek cepat: jawab soal pertama, ketuk ikon maskot (hint harus menampilkan persentase), lalu lihat tanda bahaya di bawah umpan balik.
5. Di HP (WiFi sama): `http://IP-LAPTOP:5000` (cek IP dengan `ipconfig`), izinkan Python di Private network.
6. Deploy: push folder ke GitHub, lalu render.com > New > Blueprint (langkah lengkap di bagian "Deploy" bawah).

Model di zip ini sudah dilatih ulang dengan scikit-learn 1.9.1 (sesuai requirements.txt) dan data uji 36 soal.
Jika muncul error saat memuat model: `python train_medsos.py`.

## Yang baru di game
- Kombo (+2 poin per jawaban benar beruntun, maks +10), pangkat (Satpam Magang sampai Legenda Siber), 12 lencana.
- Setelah menjawab, game menjelaskan tanda bahaya (domain murah, tautan pendek, OTP, batas waktu, dst.) atau tanda aman.
- Profil lucu: tiap akun di game punya avatar hewan, dan pemain mendapat nama + bio acak (mis. "Kucing Anti-Klik") yang bisa diacak ulang dengan 🎲 di tab Task. Profil hanya disimpan di perangkat, tidak dikirim ke server. Avatar akun diatur di `AVATARS` pada `public/data.js`.
- Efek suara (tombol 🔊), konfeti, dialog bergaya mesin ketik, tampilan kartu dan navigasi baru.
- Soal Endless bertambah 14 (total 26 soal tambahan). File `fx.js` berisi semua efek ini.
- Log jawaban punya dua kolom baru: `combo` dan `bonus`. Poin per sesi sedikit lebih tinggi dari versi lama karena bonus kombo.

---

# Panduan EduSecurity (model gaya media sosial)

## Isi folder
- `public/`            : game (index.html, style.css, data.js, game.js, ml-hook.js)
- `server.py`          : melayani game + `/predict` (model) + `/log` (catat jawaban) + `/export`
- `model_medsos.joblib`: model SIAP PAKAI (sudah dilatih), tidak perlu Data_Prep.ipynb lagi untuk menjalankan game
- `fitur.py`           : normalisasi teks + ciri tautan (dipakai training dan server)
- `buat_dataset.py`    : pembuat dataset gaya medsos + data uji dari soal game
- `train_medsos.py`, `Train_Medsos.ipynb` : melatih ulang + evaluasi (notebook ini untuk laporan)
- `data/dataset_medsos.csv`, `data/game_items.csv`
- `requirements.txt`, `render.yaml` : untuk deploy

## Menjalankan di laptop (Windows, VS Code)
1. File > Open Folder > pilih folder ini.
2. Terminal > New Terminal:
```
python -m pip install -r requirements.txt
python server.py
```
3. Buka http://localhost:5000 . Ketuk ikon maskot: persentase hint berasal dari model baru.
4. HP di WiFi yang sama: buka `http://IP-LAPTOP:5000` (cek IP dengan `ipconfig`).
   Saat Windows bertanya, izinkan Python di Private network.

Kalau muncul error saat memuat `model_medsos.joblib` (biasanya beda versi scikit-learn),
latih ulang di komputer yang sama: `python train_medsos.py`.

## Deploy untuk 40 HP (Render, gratis)
1. Taruh seluruh folder di repo GitHub (termasuk `model_medsos.joblib` dan `data/`).
2. render.com > New > Blueprint > pilih repo. Tunggu build, bagikan link/QR.
3. Server gratis "tidur" saat idle: buka linknya sendiri 5 menit sebelum sesi.
4. Data jawaban bisa hilang saat restart: unduh segera lewat
   `https://NAMA-APP.onrender.com/export?token=ADMIN_TOKEN` (token ada di Render > Environment).

## Melatih ulang / menambah data
- Tambah template di `buat_dataset.py` (daftar `P` untuk phishing, `N` untuk normal), lalu:
```
python buat_dataset.py
python train_medsos.py
```
- Lebih baik lagi: tambahkan contoh NYATA (postingan/DM yang kamu labeli sendiri) ke `data/dataset_medsos.csv`
  dengan kolom `teks,label,kategori,jenis,grup` (grup = nama unik per contoh asli).
- Jika kamu mengubah soal di `public/data.js`, jalankan `python buat_dataset.py` lagi agar data uji ikut diperbarui
  dan contoh latih yang mirip soal baru disaring.

## Hal yang perlu ditulis jujur di laporan
- Dataset dibuat dari template + variasi acak dengan domain rekaan, bukan hasil scraping akun nyata.
- 22 soal game dipakai sebagai data uji (tidak ikut dilatih), jadi angkanya kasar. Angka yang lebih realistis
  adalah GroupKFold per template (sekitar 0,89 akurasi).
- Titik lemah: pesan penipuan tanpa tautan (misalnya minta transfer) hanya mengandalkan kata-kata, jadi
  lebih rentan salah. Model memberi persentase perkiraan, bukan kepastian.
- Tab Tweet menyimpan teks ke server; ingatkan anak jangan menulis data pribadi asli.
