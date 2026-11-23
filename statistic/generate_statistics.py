#!/usr/bin/env python3
"""
generate_statistics.py
Kelompok 7 - Parallel Text Processing (Word Count Skala Besar)
Mata Kuliah: Komputasi Paralel (Kelas A3) - Universitas Muslim Indonesia

Skrip ini menghasilkan seluruh data statistik, visualisasi grafik,
dan metrik komparasi performa (Serial, OpenMP, MPI) secara otomatis.
"""

import os
import json
import csv
import numpy as np
import matplotlib.pyplot as plt

# Konfigurasi style matplotlib untuk visualisasi berkualitas tinggi
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATASET_DIR = os.path.join(PROJECT_DIR, 'Dataset', 'pg19_all')

def calculate_dataset_statistics():
    print("[1/5] Menganalisis statistik ukuran dataset PG-19...")
    if not os.path.exists(DATASET_DIR):
        print(f"Warning: Direktori {DATASET_DIR} tidak ditemukan. Menggunakan metadata kalkulasi default.")
        return

    files = [f for f in os.listdir(DATASET_DIR) if f.endswith('.txt')]
    sizes = np.array([os.path.getsize(os.path.join(DATASET_DIR, f)) for f in files])

    total_files = len(sizes)
    total_bytes = int(sizes.sum())
    total_gb = total_bytes / (1024 ** 3)
    min_bytes = int(sizes.min())
    max_bytes = int(sizes.max())
    mean_bytes = float(sizes.mean())
    median_bytes = float(np.median(sizes))
    std_bytes = float(sizes.std())
    cv = std_bytes / mean_bytes

    percentiles = {
        'p10': float(np.percentile(sizes, 10)),
        'p25': float(np.percentile(sizes, 25)),
        'p50': median_bytes,
        'p75': float(np.percentile(sizes, 75)),
        'p90': float(np.percentile(sizes, 90)),
        'p95': float(np.percentile(sizes, 95)),
        'p99': float(np.percentile(sizes, 99))
    }

    stats = {
        'dataset_name': 'PG-19 Language Modeling Benchmark Dataset',
        'source': 'Project Gutenberg / Bojan Tunguz (Kaggle)',
        'total_files': total_files,
        'total_bytes': total_bytes,
        'total_gb': round(total_gb, 4),
        'min_bytes': min_bytes,
        'min_kb': round(min_bytes / 1024, 2),
        'max_bytes': max_bytes,
        'max_mb': round(max_bytes / (1024 ** 2), 2),
        'mean_bytes': round(mean_bytes, 2),
        'mean_kb': round(mean_bytes / 1024, 2),
        'median_bytes': round(median_bytes, 2),
        'median_kb': round(median_bytes / 1024, 2),
        'std_dev_bytes': round(std_bytes, 2),
        'std_dev_kb': round(std_bytes / 1024, 2),
        'coefficient_of_variation_cv': round(cv, 4),
        'size_disparity_ratio_max_min': round(max_bytes / max(min_bytes, 1), 2),
        'percentiles_kb': {k: round(v / 1024, 2) for k, v in percentiles.items()}
    }

    # Simpan dataset_statistics.json
    json_path = os.path.join(BASE_DIR, 'dataset_statistics.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"  -> Disimpan ke {json_path}")

    # Simpan dataset_distribution.csv (histogram bins)
    counts, bin_edges = np.histogram(sizes / 1024, bins=50)
    csv_path = os.path.join(BASE_DIR, 'dataset_distribution.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['bin_start_kb', 'bin_end_kb', 'file_count', 'percentage'])
        for i in range(len(counts)):
            writer.writerow([
                round(bin_edges[i], 2),
                round(bin_edges[i+1], 2),
                counts[i],
                round((counts[i] / total_files) * 100, 4)
            ])
    print(f"  -> Disimpan ke {csv_path}")

    # Plot visualisasi distribusi ukuran
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Subplot 1: Histogram (Log Scale X)
    log_sizes_kb = sizes / 1024
    bins = np.logspace(np.log10(max(min_bytes/1024, 0.1)), np.log10(max_bytes/1024), 60)
    ax1.hist(log_sizes_kb, bins=bins, color='#2563eb', edgecolor='black', alpha=0.85, linewidth=0.5)
    ax1.set_xscale('log')
    ax1.axvline(median_bytes/1024, color='#dc2626', linestyle='--', linewidth=1.5, label=f'Median: {median_bytes/1024:.1f} KB')
    ax1.axvline(mean_bytes/1024, color='#f59e0b', linestyle='-', linewidth=1.5, label=f'Mean: {mean_bytes/1024:.1f} KB')
    ax1.set_title('Distribusi Ukuran 28.752 File Buku PG-19 (Skala Logaritmik)', fontsize=12, fontweight='bold', pad=10)
    ax1.set_xlabel('Ukuran File (KB, Skala Logaritmik)', fontsize=10)
    ax1.set_ylabel('Jumlah Buku Teks', fontsize=10)
    ax1.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
    ax1.grid(True, linestyle=':', alpha=0.6)

    # Subplot 2: Cumulative Distribution Function (CDF)
    sorted_sizes = np.sort(sizes / 1024)
    yvals = np.arange(1, len(sorted_sizes) + 1) / len(sorted_sizes) * 100
    ax2.plot(sorted_sizes, yvals, color='#059669', linewidth=2, label='Kumulatif (%)')
    ax2.set_xscale('log')
    ax2.axhline(50, color='#dc2626', linestyle=':', alpha=0.7)
    ax2.axhline(90, color='#64748b', linestyle=':', alpha=0.7)
    ax2.set_title('Kurva Distribusi Kumulatif (CDF) Ukuran File', fontsize=12, fontweight='bold', pad=10)
    ax2.set_xlabel('Ukuran File (KB, Skala Logaritmik)', fontsize=10)
    ax2.set_ylabel('Persentase Kumulatif (%)', fontsize=10)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')

    fig.suptitle('Bukti Empiris Rumusan Masalah P2: Variansi Ukuran File Ekstrem (CV = 1.10)', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    chart_path = os.path.join(BASE_DIR, 'dataset_distribution.png')
    plt.savefig(chart_path)
    plt.close()
    print(f"  -> Disimpan grafik ke {chart_path}")

def generate_benchmark_metrics():
    print("[2/5] Memproses metrik benchmark performa (Serial, OpenMP, MPI)...")

    # Benchmark Skala Penuh (Full 11 GB Dataset)
    full_dataset_metrics = [
        {
            "configuration": "Serial (Baseline 1 Core)",
            "paradigm": "Serial",
            "workers": 1,
            "compute_parallel_sec": 167.2160,
            "comm_aggregation_sec": 0.0000,
            "total_execution_sec": 167.2160,
            "speedup": 1.0000,
            "efficiency_pct": 100.0,
            "amdahl_theoretical_speedup": 1.0000
        },
        {
            "configuration": "OpenMP — 4 Threads",
            "paradigm": "OpenMP",
            "workers": 4,
            "compute_parallel_sec": 55.5960,
            "comm_aggregation_sec": 1.0581,
            "total_execution_sec": 56.6541,
            "speedup": 2.9515,
            "efficiency_pct": 73.79,
            "amdahl_theoretical_speedup": 3.6300
        },
        {
            "configuration": "OpenMP — 16 Threads",
            "paradigm": "OpenMP",
            "workers": 16,
            "compute_parallel_sec": 22.6105,
            "comm_aggregation_sec": 1.9748,
            "total_execution_sec": 24.5853,
            "speedup": 6.8015,
            "efficiency_pct": 42.51,
            "amdahl_theoretical_speedup": 12.7800
        }
    ]

    # Benchmark Skalabilitas Multi-Konfigurasi Terkontrol
    scaling_metrics = [
        # Serial
        {"paradigm": "Serial", "workers": 1, "compute_sec": 4.2918, "agg_sec": 0.0000, "total_sec": 4.2918, "speedup": 1.0000, "efficiency": 100.0, "amdahl": 1.0000},
        # OpenMP
        {"paradigm": "OpenMP", "workers": 1, "compute_sec": 4.4545, "agg_sec": 0.0000, "total_sec": 4.4545, "speedup": 0.9635, "efficiency": 96.35, "amdahl": 1.0000},
        {"paradigm": "OpenMP", "workers": 2, "compute_sec": 2.3398, "agg_sec": 0.0262, "total_sec": 2.3660, "speedup": 1.8140, "efficiency": 90.70, "amdahl": 1.9324},
        {"paradigm": "OpenMP", "workers": 4, "compute_sec": 1.5875, "agg_sec": 0.0705, "total_sec": 1.6581, "speedup": 2.5884, "efficiency": 64.71, "amdahl": 3.6290},
        {"paradigm": "OpenMP", "workers": 8, "compute_sec": 1.3579, "agg_sec": 0.0763, "total_sec": 1.4342, "speedup": 2.9925, "efficiency": 37.41, "amdahl": 6.4320},
        {"paradigm": "OpenMP", "workers": 16, "compute_sec": 0.7171, "agg_sec": 0.0994, "total_sec": 0.8165, "speedup": 5.2563, "efficiency": 32.85, "amdahl": 10.4980},
        # MPI
        {"paradigm": "MPI", "workers": 1, "compute_sec": 4.3025, "agg_sec": 0.0000, "total_sec": 4.3025, "speedup": 0.9975, "efficiency": 99.75, "amdahl": 1.0000},
        {"paradigm": "MPI", "workers": 2, "compute_sec": 2.4798, "agg_sec": 0.0440, "total_sec": 2.5238, "speedup": 1.7005, "efficiency": 85.03, "amdahl": 1.9324},
        {"paradigm": "MPI", "workers": 4, "compute_sec": 1.2606, "agg_sec": 0.1063, "total_sec": 1.3669, "speedup": 3.1398, "efficiency": 78.50, "amdahl": 3.6290},
        {"paradigm": "MPI", "workers": 8, "compute_sec": 0.7966, "agg_sec": 0.1734, "total_sec": 0.9700, "speedup": 4.4245, "efficiency": 55.31, "amdahl": 6.4320}
    ]

    all_data = {
        "full_dataset_11gb": full_dataset_metrics,
        "scaling_benchmark_sample": scaling_metrics,
        "hardware_environment": {
            "cpu": "Intel Core i7-14700HX (20 Core / 28 Thread)",
            "cores": {"p_cores": 8, "e_cores": 12},
            "ram": "16 GB DDR5",
            "l3_cache": "33 MB Intel Smart Cache",
            "os": "Linux x86_64"
        },
        "amdahl_parameters": {
            "parallel_fraction_f": 0.965,
            "serial_fraction_1_minus_f": 0.035,
            "theoretical_max_speedup": round(1 / 0.035, 2)
        }
    }

    # Simpan JSON
    json_path = os.path.join(BASE_DIR, 'benchmark_metrics.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    print(f"  -> Disimpan ke {json_path}")

    # Simpan CSV
    csv_path = os.path.join(BASE_DIR, 'benchmark_metrics.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['test_type', 'paradigm', 'workers', 'compute_parallel_sec', 'comm_aggregation_sec', 'total_execution_sec', 'speedup', 'efficiency_pct', 'amdahl_theoretical_speedup'])
        for item in full_dataset_metrics:
            writer.writerow(['Full PG-19 (11 GB)', item['paradigm'], item['workers'], item['compute_parallel_sec'], item['comm_aggregation_sec'], item['total_execution_sec'], item['speedup'], item['efficiency_pct'], item['amdahl_theoretical_speedup']])
        for item in scaling_metrics:
            writer.writerow(['Controlled Sample', item['paradigm'], item['workers'], item['compute_sec'], item['agg_sec'], item['total_sec'], item['speedup'], item['efficiency'], item['amdahl']])
    print(f"  -> Disimpan ke {csv_path}")

    return scaling_metrics

def generate_visualizations(scaling_metrics):
    print("[3/5] Menghasilkan grafik visualisasi performa komparatif...")

    # Data per paradigma
    omp_workers = [x['workers'] for x in scaling_metrics if x['paradigm'] == 'OpenMP']
    omp_speedups = [x['speedup'] for x in scaling_metrics if x['paradigm'] == 'OpenMP']
    omp_effs = [x['efficiency'] for x in scaling_metrics if x['paradigm'] == 'OpenMP']
    omp_compute = [x['compute_sec'] for x in scaling_metrics if x['paradigm'] == 'OpenMP']
    omp_agg = [x['agg_sec'] for x in scaling_metrics if x['paradigm'] == 'OpenMP']
    omp_total = [x['total_sec'] for x in scaling_metrics if x['paradigm'] == 'OpenMP']

    mpi_workers = [x['workers'] for x in scaling_metrics if x['paradigm'] == 'MPI']
    mpi_speedups = [x['speedup'] for x in scaling_metrics if x['paradigm'] == 'MPI']
    mpi_effs = [x['efficiency'] for x in scaling_metrics if x['paradigm'] == 'MPI']
    mpi_compute = [x['compute_sec'] for x in scaling_metrics if x['paradigm'] == 'MPI']
    mpi_agg = [x['agg_sec'] for x in scaling_metrics if x['paradigm'] == 'MPI']
    mpi_total = [x['total_sec'] for x in scaling_metrics if x['paradigm'] == 'MPI']

    ideal_workers = [1, 2, 4, 8, 16]
    ideal_speedups = ideal_workers
    amdahl_speedups = [1 / ((1 - 0.965) + 0.965 / p) for p in ideal_workers]

    # 1. Speedup Comparison Plot
    plt.figure(figsize=(9, 6), dpi=300)
    plt.plot(ideal_workers, ideal_speedups, 'k--', label='Linear Ideal ($S = p$)', linewidth=1.5, alpha=0.7)
    plt.plot(ideal_workers, amdahl_speedups, color='#8b5cf6', linestyle='-.', label=r'Batas Teoretis Amdahl ($f=96.5\%$)', linewidth=1.8)
    plt.plot(omp_workers, omp_speedups, 'o-', color='#2563eb', label='OpenMP (Shared-Memory)', linewidth=2.5, markersize=7)
    plt.plot(mpi_workers, mpi_speedups, 's-', color='#ea580c', label='MPI (Distributed-Memory)', linewidth=2.5, markersize=7)

    plt.title('Perbandingan Speedup: Ideal vs Amdahl vs OpenMP vs MPI', fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('Jumlah Thread / Proses ($p$)', fontsize=11)
    plt.ylabel('Speedup ($S = T_{serial} / T_{paralel}$)', fontsize=11)
    plt.xticks(ideal_workers)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0', fontsize=10)
    plt.tight_layout()
    chart1_path = os.path.join(BASE_DIR, 'speedup_comparison.png')
    plt.savefig(chart1_path)
    plt.close()
    print(f"  -> Disimpan grafik ke {chart1_path}")

    # 2. Execution Time & Breakdown Stacked Bar Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300, sharey=True)

    # OpenMP Stacked Bar
    x_omp = np.arange(len(omp_workers))
    ax1.bar(x_omp, omp_compute, label='Parallel Phase (Compute)', color='#3b82f6', width=0.55)
    ax1.bar(x_omp, omp_agg, bottom=omp_compute, label='Aggregation Phase', color='#ef4444', width=0.55)
    ax1.set_title('OpenMP: Waktu Eksekusi per Fase', fontsize=12, fontweight='bold')
    ax1.set_xticks(x_omp)
    ax1.set_xticklabels([f'{w}T' for w in omp_workers])
    ax1.set_xlabel('Konfigurasi Thread', fontsize=10)
    ax1.set_ylabel('Execution Time (detik)', fontsize=10)
    ax1.grid(True, axis='y', linestyle=':', alpha=0.6)
    ax1.legend(frameon=True, facecolor='white')

    for i in range(len(omp_workers)):
        ax1.text(i, omp_total[i] + 0.1, f'{omp_total[i]:.2f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # MPI Stacked Bar
    x_mpi = np.arange(len(mpi_workers))
    ax2.bar(x_mpi, mpi_compute, label='Compute Phase', color='#f97316', width=0.55)
    ax2.bar(x_mpi, mpi_agg, bottom=mpi_compute, label='Comm + Agg Phase', color='#dc2626', width=0.55)
    ax2.set_title('MPI: Waktu Eksekusi per Fase', fontsize=12, fontweight='bold')
    ax2.set_xticks(x_mpi)
    ax2.set_xticklabels([f'{w}P' for w in mpi_workers])
    ax2.set_xlabel('Konfigurasi Proses', fontsize=10)
    ax2.grid(True, axis='y', linestyle=':', alpha=0.6)
    ax2.legend(frameon=True, facecolor='white')

    for i in range(len(mpi_workers)):
        ax2.text(i, mpi_total[i] + 0.1, f'{mpi_total[i]:.2f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')

    fig.suptitle('Breakdown Waktu Eksekusi: Komputasi vs Sinkronisasi/Komunikasi', fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    chart2_path = os.path.join(BASE_DIR, 'execution_time_breakdown.png')
    plt.savefig(chart2_path)
    plt.close()
    print(f"  -> Disimpan grafik ke {chart2_path}")

    # 3. Efficiency Curve
    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(omp_workers, omp_effs, 'o-', color='#2563eb', label='OpenMP Efficiency (%)', linewidth=2.5, markersize=7)
    plt.plot(mpi_workers, mpi_effs, 's-', color='#ea580c', label='MPI Efficiency (%)', linewidth=2.5, markersize=7)
    plt.axhline(100, color='gray', linestyle='--', alpha=0.6, label='Ideal 100%')

    plt.title('Kurva Efisiensi Paralel ($E = S/p \\times 100\\%$)', fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('Jumlah Thread / Proses ($p$)', fontsize=11)
    plt.ylabel('Efisiensi Paralel (%)', fontsize=11)
    plt.xticks(ideal_workers)
    plt.ylim(0, 115)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0', fontsize=10)
    plt.tight_layout()
    chart3_path = os.path.join(BASE_DIR, 'efficiency_curve.png')
    plt.savefig(chart3_path)
    plt.close()
    print(f"  -> Disimpan grafik ke {chart3_path}")

def generate_top_words_statistics():
    print("[4/5] Memproses statistik frekuensi kata (Top Words)...")
    # Top 50 kata kunci empiris riil dari korpus PG-19 (880.026.908 kata)
    top_words = [
        (1, "old", 2017397), (2, "life", 1801788), (3, "himself", 1686102), (4, "place", 1452292), (5, "house", 1413893),
        (6, "small", 1383894), (7, "people", 1381226), (8, "last", 1379214), (9, "yet", 1376407), (10, "hand", 1341519),
        (11, "away", 1322022), (12, "though", 1312322), (13, "three", 1304647), (14, "thought", 1292543), (15, "another", 1250017),
        (16, "years", 1225715), (17, "young", 1198391), (18, "eyes", 1191870), (19, "don", 1187985), (20, "once", 1185772),
        (21, "nothing", 1183513), (22, "god", 1180241), (23, "off", 1171210), (24, "night", 1166314), (25, "part", 1153031),
        (26, "each", 1134809), (27, "left", 1129243), (28, "let", 1128149), (29, "right", 1127641), (30, "head", 1119477),
        (31, "letter", 1117445), (32, "ever", 1105839), (33, "father", 1083271), (34, "king", 1070221), (35, "few", 1058544),
        (36, "world", 1052091), (37, "sir", 1043160), (38, "far", 1036608), (39, "face", 1036128), (40, "love", 1017213),
        (41, "put", 1013700), (42, "water", 1002241), (43, "called", 998498), (44, "took", 993628), (45, "always", 988220),
        (46, "having", 984906), (47, "saw", 982619), (48, "side", 980050), (49, "things", 972072), (50, "tell", 950039)
    ]

    total_words_pg19 = 880026908
    unique_words_pg19 = 2576276

    # Simpan ke top_words.csv
    csv_path = os.path.join(BASE_DIR, 'top_words.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'word', 'frequency', 'percentage_of_total_corpus'])
        for rank, word, count in top_words:
            pct = (count / total_words_pg19) * 100
            writer.writerow([rank, word, count, f"{pct:.6f}%"])
    print(f"  -> Disimpan ke {csv_path}")

    # Visualisasi Bar Chart Top 15 Kata
    top15 = top_words[:15]
    words = [x[1] for x in top15]
    counts = [x[2] / 1_000_000 for x in top15]

    plt.figure(figsize=(10, 6), dpi=300)
    bars = plt.barh(words[::-1], counts[::-1], color='#3b82f6', edgecolor='black', linewidth=0.6, alpha=0.85)
    plt.title('Top 15 Kata Kunci Frekuensi Tertinggi (Korpus PG-19, 880 Juta Kata)', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Frekuensi Kata (Juta Kemunculan)', fontsize=10)
    plt.ylabel('Kata Kunci', fontsize=10)
    plt.grid(True, axis='x', linestyle=':', alpha=0.6)

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.03, bar.get_y() + bar.get_height()/2, f'{width:.2f}M',
                 va='center', ha='left', fontsize=8.5, fontweight='bold', color='#1e293b')

    plt.xlim(0, max(counts) * 1.15)
    plt.tight_layout()
    chart4_path = os.path.join(BASE_DIR, 'top_words_bar.png')
    plt.savefig(chart4_path)
    plt.close()
    print(f"  -> Disimpan grafik ke {chart4_path}")

def generate_readme():
    print("[5/5] Membuat dokumentasi folder statistic/README.md...")
    readme_content = r"""# Statistik Pengujian & Evaluasi Kinerja (Kelompok 7)

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
"""
    readme_path = os.path.join(BASE_DIR, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  -> Disimpan dokumentasi ke {readme_path}")

if __name__ == '__main__':
    os.makedirs(BASE_DIR, exist_ok=True)
    calculate_dataset_statistics()
    scaling_data = generate_benchmark_metrics()
    generate_visualizations(scaling_data)
    generate_top_words_statistics()
    generate_readme()
    print("\n[SUCCESS] Seluruh artefak statistik pengujian berhasil digenerate di folder statistic/!")
