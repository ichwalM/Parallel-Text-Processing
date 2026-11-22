#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
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

    std::unordered_map<std::string, uint64_t> global_counts;
    global_counts.reserve(1000000);
    std::string buffer;
    uint64_t total_words = 0;
    uint64_t total_bytes = 0;

    auto start = std::chrono::high_resolution_clock::now();

    for (size_t i = 0; i < files.size(); ++i) {
        process_file(files[i], buffer, global_counts, total_words, total_bytes);
        if ((i + 1) % 500 == 0 || (i + 1) == files.size()) {
            double pct = 100.0 * static_cast<double>(i + 1) / static_cast<double>(files.size());
            std::cerr << "\rMemproses file: " << (i + 1) << "/" << files.size()
                      << " (" << std::fixed << std::setprecision(1) << pct << "%)" << std::flush;
        }
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::cerr << "\r\033[K";
    std::chrono::duration<double> elapsed = end - start;

    std::vector<std::pair<std::string, uint64_t>> sorted_words(
        global_counts.begin(), global_counts.end());
    std::sort(sorted_words.begin(), sorted_words.end(),
              [](const auto& a, const auto& b) {
                  if (a.second != b.second) return a.second > b.second;
                  return a.first < b.first;
              });

    double total_gb = static_cast<double>(total_bytes) / (1024.0 * 1024.0 * 1024.0);

    std::cout << "=== SERIAL WORD COUNT (PG-19 FULL) ===\n";
    std::cout << "Jumlah Buku    : " << files.size() << "\n";
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Total Ukuran   : " << total_gb << " GB\n";
    std::cout << "Total Kata     : " << total_words << "\n";
    std::cout << "Kata Unik      : " << global_counts.size() << "\n";
    std::cout << std::setprecision(4);
    std::cout << "Execution Time : " << elapsed.count() << " detik\n\n";
    std::cout << "Top 10 Kata Kunci:\n";
    for (size_t i = 0; i < std::min<size_t>(10, sorted_words.size()); ++i) {
        std::cout << std::setw(2) << (i + 1) << ". "
                  << std::left << std::setw(18) << sorted_words[i].first
                  << std::right << sorted_words[i].second << "\n";
    }

    return 0;
}