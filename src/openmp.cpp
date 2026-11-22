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
#include <unordered_set>
#include <vector>

namespace fs = std::filesystem;

const std::unordered_set<std::string> STOPWORDS = {
    "the", "and", "that", "have", "for", "not", "with", "you", "this", "but",
    "his", "from", "they", "say", "her", "she", "will", "one", "all", "would",
    "there", "their", "what", "out", "about", "who", "get", "which", "when",
    "make", "can", "like", "time", "just", "him", "know", "take", "into",
    "year", "your", "good", "some", "could", "them", "see", "other", "than",
    "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give", "day",
    "most", "was", "were", "are", "been", "being", "had", "has", "did", "does",
    "doing", "should", "may", "might", "must", "shall", "very", "much", "more",
    "such", "upon", "before", "where", "here", "through", "down", "still",
    "under", "while", "great", "little", "own", "man", "men", "said", "made",
    "came", "went", "never", "too", "every", "without", "again", "those",
    "both", "same", "between", "against", "long", "many", "found"
};

void process_file(const fs::path& filepath,
                  std::string& buffer,
                  std::unordered_map<std::string, uint64_t>& counts,
                  uint64_t& total_words,
                  uint64_t& total_bytes) {
    std::ifstream file(filepath, std::ios::in | std::ios::binary);
    if (!file) {
        return;
    }

    file.seekg(0, std::ios::end);
    std::streamsize size = file.tellg();
    if (size <= 0) {
        return;
    }
    file.seekg(0, std::ios::beg);

    buffer.resize(static_cast<size_t>(size));
    if (!file.read(&buffer[0], size)) {
        return;
    }
    total_bytes += static_cast<uint64_t>(size);

    std::string word;
    word.reserve(32);

    for (unsigned char ch : buffer) {
        if (std::isalpha(ch)) {
            word.push_back(static_cast<char>(std::tolower(ch)));
        } else if (!word.empty()) {
            if (word.size() >= 3 && STOPWORDS.find(word) == STOPWORDS.end()) {
                counts[word]++;
                total_words++;
            }
            word.clear();
        }
    }

    if (!word.empty() && word.size() >= 3 && STOPWORDS.find(word) == STOPWORDS.end()) {
        counts[word]++;
        total_words++;
    }
}

int main(int argc, char* argv[]) {
    std::string dir_path = (argc > 1) ? argv[1] : "Dataset/pg19";
    int num_threads = (argc > 2) ? std::stoi(argv[2]) : 4;
    if (num_threads < 1) {
        num_threads = 1;
    }

    std::vector<fs::path> files;
    for (const auto& entry : fs::recursive_directory_iterator(dir_path)) {
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
    std::vector<uint64_t> local_bytes(num_threads, 0);

    auto start = std::chrono::high_resolution_clock::now();

    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        std::string buffer;
        local_maps[tid].reserve(200000);

        #pragma omp for schedule(dynamic, 4)
        for (size_t i = 0; i < files.size(); ++i) {
            process_file(files[i], buffer, local_maps[tid], local_totals[tid], local_bytes[tid]);
        }
    }

    auto mid = std::chrono::high_resolution_clock::now();

    std::unordered_map<std::string, uint64_t> global_counts = std::move(local_maps[0]);
    uint64_t total_words = local_totals[0];
    uint64_t total_bytes = local_bytes[0];

    for (int t = 1; t < num_threads; ++t) {
        total_words += local_totals[t];
        total_bytes += local_bytes[t];
        for (const auto& kv : local_maps[t]) {
            global_counts[kv.first] += kv.second;
        }
        local_maps[t].clear();
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

    double total_gb = static_cast<double>(total_bytes) / (1024.0 * 1024.0 * 1024.0);

    std::cout << "=== OPENMP WORD COUNT (PG-19 FULL | " << num_threads << " THREADS) ===\n";
    std::cout << "Jumlah Buku       : " << files.size() << "\n";
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Total Ukuran      : " << total_gb << " GB\n";
    std::cout << "Total Kata        : " << total_words << "\n";
    std::cout << "Kata Unik         : " << global_counts.size() << "\n";
    std::cout << std::setprecision(4);
    std::cout << "Parallel Phase    : " << parallel_time.count() << " detik\n";
    std::cout << "Aggregation Phase : " << agg_time.count() << " detik\n";
    std::cout << "Total Exec Time   : " << total_time.count() << " detik\n\n";
    std::cout << "Top 10 Kata Kunci:\n";
    for (size_t i = 0; i < std::min<size_t>(10, sorted_words.size()); ++i) {
        std::cout << std::setw(2) << (i + 1) << ". "
                  << std::left << std::setw(18) << sorted_words[i].first
                  << std::right << sorted_words[i].second << "\n";
    }

    return 0;
}