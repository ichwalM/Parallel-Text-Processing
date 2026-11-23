# Statistik Pengujian & Evaluasi Kinerja (Kelompok 7)

Folder ini memuat seluruh data statistik empiris, visualisasi performa, dan metrik hasil pengujian pemrosesan teks berskala besar (**Word Count Skala Besar**) pada korpus digital **PG-19 Project Gutenberg** (~11 GB / 28.752 file `.txt`) yang diuji pada arsitektur **Intel® Core™ i7-14700HX** (20 Core / 28 Thread, 16 GB DDR5).

---

## 1. Daftar Berkas & Struktur Folder

```text
statistic/
├── generate_statistics.py       # Skrip otomatisasi pengolahan data & grafik
├── benchmark_metrics.json       # Rekapitulasi lengkap metrik dalam format JSON
├── benchmark_metrics.csv        # Rekapitulasi metrik eksekusi, speedup, efisiensi (CSV)
├── dataset_statistics.json      # Profil statistik ukuran dataset PG-19
├── dataset_distribution.csv     # Bins distribusi ukuran file buku (histogram)
├── top_words.csv                # Top frekuensi kata kunci korpus penuh (Top 50)
├── speedup_comparison.png       # Grafik Speedup: Linear vs Amdahl vs OpenMP vs MPI
├── execution_time_breakdown.png # Grafik Breakdown waktu: Komputasi vs Agregasi
├── efficiency_curve.png         # Grafik Kurva Efisiensi Paralel (%)
├── dataset_distribution.png     # Grafik Distribusi ukuran buku (Membuktikan Masalah P2)
├── top_words_bar.png            # Grafik Barchart Top Kata Kunci Korpus
└── README.md                    # Dokumentasi ini
```

---

## 2. Ringkasan Temuan Kunci

### A. Dataset PG-19 (Bukti Rumusan Masalah P2)
* **Total File:** 28.752 file buku teks (`.txt`)
* **Total Ukuran Data:** 10,93 GB (11.737.206.770 byte)
* **Variansi Ekstrem:** Ukuran minimum 100 byte, ukuran maksimum 28,93 MB, rasio selisih mencapai **289.000×**.
* **Standar Deviasi:** 438,57 KB dengan nilai rata-rata 398,65 KB ($CV = 1,10$). Hal ini membuktikan bahwa pembagian statis mutlak menimbulkan *load imbalance*, sehingga penjadwalan dinamis OpenMP (`schedule(dynamic, 4)`) dan partisi siklik terdesentralisasi MPI sangat esensial.

### B. Hasil Skala Penuh (Full 11 GB PG-19)
* **Total Kata:** 880.026.908 kata
* **Kosakata Unik:** 2.576.276 kata unik
* **Serial (1 Core):** 167,22 detik (~2,78 menit)
* **OpenMP (4 Threads):** 56,65 detik (**Speedup 2,95×**, Efisiensi 73,8%)
* **OpenMP (16 Threads):** 24,59 detik (**Speedup 6,80×**, Efisiensi 42,5%)

### C. Visualisasi Performa
1. **Speedup Comparison (`speedup_comparison.png`):** Memperlihatkan deviasi percepatan aktual terhadap garis linear ideal dan batas teoretis Hukum Amdahl ($f=96,5\%$).
2. **Breakdown Waktu (`execution_time_breakdown.png`):** Menggambarkan bagaimana fase komputasi paralel menurun drastis, sedangkan fase agregasi hash map dan komunikasi MPI meningkat proporsional terhadap penambahan worker ($O(P)$ communication overhead).
3. **Efisiensi Paralel (`efficiency_curve.png`):** Menunjukkan penurunan efisiensi pada thread tinggi akibat saturasi bus memori DDR5 dan persaingan L3 cache.

---

## 3. Cara Menjalankan Ulang Skrip

Untuk meregenerasi seluruh data CSV, JSON, dan grafik visualisasi:

```bash
# Pastikan dependensi terpasang
pip install matplotlib pandas numpy

# Eksekusi skrip
python3 statistic/generate_statistics.py
```
