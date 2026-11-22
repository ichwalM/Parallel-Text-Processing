#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <omp.h>
#include <string>
#include <unordered_map>
#include <vector>

namespace fs = std::filesystem;

void process_file(const fs::path& filepath,
                  std::unordered_map<std::string, uint64_t>& counts,
                  uint64_t& total_words) {
    std::ifstream file(filepath, std::ios::in | std::ios::binary);
    if (!file) {
        return;
    }

    file.seekg(0, std::ios::end);
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::string buffer(size, '\0');
    if (!file.read(&buffer[0], size)) {
        return;
    }

    std::string word;
    word.reserve(32);

    for (unsigned char ch : buffer) {
        if (std::isalpha(ch)) {
            word.push_back(static_cast<char>(std::tolower(ch)));
        } else if (!word.empty()) {
            counts[word]++;
            total_words++;
            word.clear();
        }
    }

    if (!word.empty()) {
        counts[word]++;
        total_words++;
    }
}

int main(int argc, char* argv[]) {
    std::string dir_path = (argc > 1) ? argv[1] : "Dataset/chunks";
    int num_threads = (argc > 2) ? std::stoi(argv[2]) : 4;

    std::vector<fs::path> files;
    for (const auto& entry : fs::directory_iterator(dir_path)) {
        if (entry.is_regular_file() && entry.path().extension() == ".txt") {
            files.push_back(entry.path());
        }
    }
    std::sort(files.begin(), files.end());

    if (files.empty()) {
        std::cerr << "Tidak ada file .txt di " << dir_path << "\n";
        return 1;
    }

    omp_set_num_threads(num_threads);
    std::vector<std::unordered_map<std::string, uint64_t>> local_maps(num_threads);
    std::vector<uint64_t> local_totals(num_threads, 0);

    auto start = std::chrono::high_resolution_clock::now();

    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        #pragma omp for schedule(dynamic)
        for (size_t i = 0; i < files.size(); ++i) {
            process_file(files[i], local_maps[tid], local_totals[tid]);
        }
    }

    auto mid = std::chrono::high_resolution_clock::now();

    std::unordered_map<std::string, uint64_t> global_counts;
    uint64_t total_words = 0;
    for (int t = 0; t < num_threads; ++t) {
        total_words += local_totals[t];
        for (const auto& kv : local_maps[t]) {
            global_counts[kv.first] += kv.second;
        }
    }

    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> parallel_time = mid - start;
    std::chrono::duration<double> agg_time = end - mid;
    std::chrono::duration<double> total_time = end - start;

    std::vector<std::pair<std::string, uint64_t>> sorted_words(
        global_counts.begin(), global_counts.end());
    std::sort(sorted_words.begin(), sorted_words.end(),
              [](const auto& a, const auto& b) {
                  if (a.second != b.second) return a.second > b.second;
                  return a.first < b.first;
              });

    std::cout << "=== OPENMP WORD COUNT (" << num_threads << " THREADS) ===\n";
    std::cout << "Jumlah File       : " << files.size() << "\n";
    std::cout << "Total Kata        : " << total_words << "\n";
    std::cout << "Kata Unik         : " << global_counts.size() << "\n";
    std::cout << std::fixed << std::setprecision(4);
    std::cout << "Parallel Phase    : " << parallel_time.count() << " detik\n";
    std::cout << "Aggregation Phase : " << agg_time.count() << " detik\n";
    std::cout << "Total Exec Time   : " << total_time.count() << " detik\n\n";
    std::cout << "Top 10 Kata Terbanyak:\n";
    for (size_t i = 0; i < std::min<size_t>(10, sorted_words.size()); ++i) {
        std::cout << std::setw(2) << (i + 1) << ". "
                  << std::left << std::setw(18) << sorted_words[i].first
                  << std::right << sorted_words[i].second << "\n";
    }

    return 0;
}