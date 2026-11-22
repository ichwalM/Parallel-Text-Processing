# Parallel Text Processing — Word Count Skala Besar (Kelompok 7)

Proyek UAS Mata Kuliah **Komputasi Paralel** (Kelas A3) — Fakultas Ilmu Komputer, Universitas Muslim Indonesia (UMI).  
Proyek ini mengimplementasikan dan membandingkan performa penghitungan frekuensi kata (*word count*) pada korpus teks berskala besar menggunakan pendekatan **Serial**, **Shared-Memory (OpenMP)**, dan **Distributed-Memory (MPI)**.

## Anggota Tim (Kelompok 7)

- **Ichwal**
- **Ikhsan Qowiyyun**
- **Fachrul Rezky**
- **Fathur Rahmansyah**

---

## Rumusan Masalah

Pemrosesan korpus buku teks berskala besar (28.752 file `.txt` / 11 GB) memunculkan empat permasalahan utama yang diuji dalam proyek ini:

1. **P1 · Eksekusi Serial (*Bottleneck* 1 Core):** Pemindaian dan penghitungan frekuensi kata pada korpus 11 GB secara sekuensial berjalan lambat karena hanya memanfaatkan satu *core* CPU.
2. **P2 · *Scheduling* (Beban Tidak Merata):** Ukuran antar buku pada 28.752 file sangat beragam (dari karya pendek hingga novel tebal), sehingga pembagian kerja statis berpotensi membuat sebagian *thread/process* menganggur.
3. **P3 · Sinkronisasi (Agregasi *Hash Map*):** Penggabungan tabel frekuensi kata (*hash map*) lokal dari banyak *worker* ke struktur global rawan *race condition* dan menimbulkan *overhead* sinkronisasi/komunikasi.
4. **P4 · Skalabilitas (*Speedup* Non-Linear):** Penambahan jumlah *thread/process* tidak selalu menghasilkan percepatan linear akibat bagian serial (Hukum Amdahl), akses memori/*cache*, dan biaya agregasi.

---

## Dataset

Proyek ini menggunakan seluruh korpus teks dari **The PG-19 Language Modeling Benchmark Dataset** (bersumber dari buku domain publik Project Gutenberg) dengan menggabungkan seluruh folder `train`, `test`, dan `validation`:

- **Sumber Dataset (Kaggle):** [The PG-19 Language Modeling Benchmark Dataset — Bojan Tunguz](https://www.kaggle.com/datasets/tunguz/the-pg19-language-modeling-benchmark-dataset)
- **Total File Teks:** 28.752 file `.txt` (`train`: 28.602, `test`: 100, `validation`: 50)
- **Ukuran:** ~4 GB (arsip `.zip`) / ~11 GB (setelah diekstrak)

> **Catatan:** Folder `Dataset/` tidak disertakan di dalam repository GitHub ini (diabaikan melalui `.gitignore`) karena ukurannya yang besar.

### Cara Menyiapkan Dataset

1. Unduh file `archive.zip` dari tautan Kaggle di atas:  
   `https://www.kaggle.com/datasets/tunguz/the-pg19-language-modeling-benchmark-dataset`
2. Simpan `archive.zip` ke dalam folder `Dataset/` di root proyek.
3. Ekstrak arsip ke folder `Dataset/pg19/`:

```bash
mkdir -p Dataset/pg19
unzip -q Dataset/archive.zip -d Dataset/pg19
```

4. Verifikasi jumlah file `.txt` yang terekstrak:

```bash
du -sh Dataset/pg19
find Dataset/pg19 -type f -name "*.txt" | wc -l
```

---

## Struktur Proyek

```text
Komputasi-Pararel-2026/
├── src/
│   ├── serial.cpp          # Implementasi serial (baseline 1 core)
│   ├── openmp.cpp          # Implementasi paralel shared-memory (OpenMP)
│   └── mpi_wordcount.cpp   # Implementasi paralel distributed-memory (MPI)
├── build/                  # Binary hasil kompilasi (diabaikan git)
├── Dataset/
│   └── pg19/               # Korpus buku PG-19 (diabaikan git)
├── .gitignore
└── README.md
```

---

## Prasyarat & Lingkungan Pengujian

### Dependensi Software
- Compiler C++ dengan dukungan **C++17** dan **OpenMP** (`g++`)
- Library **OpenMPI** (`mpic++`, `mpirun`)

Instalasi pada Ubuntu/Debian/WSL:

```bash
sudo apt update
sudo apt install -y build-essential openmpi-bin libopenmpi-dev unzip
```

### Spesifikasi Perangkat Uji
- **CPU:** Intel Core i7-14700HX (20 Core: 8 P-Core + 12 E-Core, 28 Thread)
- **RAM:** 16 GB
- **OS:** Linux

---

## Cara Kompilasi & Menjalankan Program

Buat folder `build/` terlebih dahulu dari direktori utama proyek:

```bash
mkdir -p build
```

### 1. Versi Serial (*Baseline*)

```bash
g++ -O2 -std=c++17 src/serial.cpp -o build/serial
./build/serial Dataset/pg19
```

### 2. Versi Paralel Shared-Memory (OpenMP)

```bash
g++ -O2 -std=c++17 -fopenmp src/openmp.cpp -o build/openmp

# Contoh pengujian pada 1, 2, 4, 8, dan 16 thread
for t in 1 2 4 8 16; do
    ./build/openmp Dataset/pg19 $t
done
```

### 3. Versi Paralel Distributed-Memory (MPI)

```bash
mpic++ -O2 -std=c++17 src/mpi_wordcount.cpp -o build/mpi_wordcount

# Contoh pengujian pada 1, 2, 4, dan 8 process
for p in 1 2 4 8; do
    mpirun -np $p ./build/mpi_wordcount Dataset/pg19
done
```

---

## Metrik Evaluasi & Hasil Eksperimen

Performa dievaluasi menggunakan waktu eksekusi ($T$), percepatan (*Speedup*), dan efisiensi (*Efficiency*) terhadap jumlah *thread/process* ($p$):

$$S = \frac{T_{\text{serial}}}{T_{\text{paralel}}}, \qquad E = \frac{S}{p} \times 100\%$$

| Konfigurasi | Execution Time (detik) | Speedup ($S$) | Efficiency ($E$) |
| :--- | :---: | :---: | :---: |
| Serial (Baseline) | *Coming Soon* | 1.00 | 100% |
| OpenMP — 1 Thread | *Coming Soon* | *Coming Soon* | *Coming Soon* |
| OpenMP — 2 Thread | *Coming Soon* | *Coming Soon* | *Coming Soon* |
| OpenMP — 4 Thread | *Coming Soon* | *Coming Soon* | *Coming Soon* |
| OpenMP — 8 Thread | *Coming Soon* | *Coming Soon* | *Coming Soon* |
| OpenMP — 16 Thread | *Coming Soon* | *Coming Soon* | *Coming Soon* |
| MPI (Demonstratif) | *Coming Soon* | *Coming Soon* | *Coming Soon* |

---

## Referensi

- **Project Gutenberg:** [https://www.gutenberg.org/](https://www.gutenberg.org/)
- **PG-19 Benchmark Dataset (Kaggle):** [https://www.kaggle.com/datasets/tunguz/the-pg19-language-modeling-benchmark-dataset](https://www.kaggle.com/datasets/tunguz/the-pg19-language-modeling-benchmark-dataset)
- **Distributed Word Count System (EthanCornell):** [https://github.com/EthanCornell](https://github.com/EthanCornell)
- **OpenMP Primer (`parallel-runtimes/lomp`):** [https://github.com/parallel-runtimes/lomp](https://github.com/parallel-runtimes/lomp)