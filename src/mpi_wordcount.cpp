#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mpi.h>
#include <sstream>
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

std::string serialize_map(const std::unordered_map<std::string, uint64_t>& counts) {
    std::ostringstream oss;
    for (const auto& kv : counts) {
        oss << kv.first << ' ' << kv.second << '\n';
    }
    return oss.str();
}

void deserialize_and_merge(const std::string& payload,
                           std::unordered_map<std::string, uint64_t>& global_counts) {
    std::istringstream iss(payload);
    std::string word;
    uint64_t count;
    while (iss >> word >> count) {
        global_counts[word] += count;
    }
}

int main(int argc, char* argv[]) {
    MPI_Init(&argc, &argv);

    int rank = 0;
    int size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    std::string dir_path = (argc > 1) ? argv[1] : "Dataset/pg19";

    std::vector<fs::path> files;
    for (const auto& entry : fs::recursive_directory_iterator(dir_path)) {
        if (entry.is_regular_file() && entry.path().extension() == ".txt") {
            files.push_back(entry.path());
        }
    }
    std::sort(files.begin(), files.end());

    if (files.empty()) {
        if (rank == 0) {
            std::cerr << "Tidak ada file .txt di " << dir_path << "\n";
        }
        MPI_Finalize();
        return 1;
    }

    std::unordered_map<std::string, uint64_t> local_counts;
    local_counts.reserve(200000);
    std::string buffer;
    uint64_t local_words = 0;
    uint64_t local_bytes = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();

    for (size_t i = static_cast<size_t>(rank); i < files.size(); i += static_cast<size_t>(size)) {
        process_file(files[i], buffer, local_counts, local_words, local_bytes);
    }

    uint64_t global_words = 0;
    uint64_t global_bytes = 0;
    MPI_Reduce(&local_words, &global_words, 1, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_bytes, &global_bytes, 1, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);

    double mid_time = MPI_Wtime();

    if (rank == 0) {
        std::unordered_map<std::string, uint64_t> global_counts = std::move(local_counts);

        for (int src = 1; src < size; ++src) {
            uint64_t payload_size = 0;
            MPI_Recv(&payload_size, 1, MPI_UINT64_T, src, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            if (payload_size > 0) {
                std::string payload(payload_size, '\0');
                MPI_Recv(&payload[0], static_cast<int>(payload_size), MPI_CHAR, src, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                deserialize_and_merge(payload, global_counts);
            }
        }

        double end_time = MPI_Wtime();

        std::vector<std::pair<std::string, uint64_t>> sorted_words(
            global_counts.begin(), global_counts.end());
        std::sort(sorted_words.begin(), sorted_words.end(),
                  [](const auto& a, const auto& b) {
                      if (a.second != b.second) return a.second > b.second;
                      return a.first < b.first;
                  });

        double total_gb = static_cast<double>(global_bytes) / (1024.0 * 1024.0 * 1024.0);

        std::cout << "=== MPI WORD COUNT (PG-19 FULL | " << size << " PROCESSES) ===\n";
        std::cout << "Jumlah Buku       : " << files.size() << "\n";
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Total Ukuran      : " << total_gb << " GB\n";
        std::cout << "Total Kata        : " << global_words << "\n";
        std::cout << "Kata Unik         : " << global_counts.size() << "\n";
        std::cout << std::setprecision(4);
        std::cout << "Compute Phase     : " << (mid_time - start_time) << " detik\n";
        std::cout << "Comm + Agg Phase  : " << (end_time - mid_time) << " detik\n";
        std::cout << "Total Exec Time   : " << (end_time - start_time) << " detik\n\n";
        std::cout << "Top 10 Kata Kunci:\n";
        for (size_t i = 0; i < std::min<size_t>(10, sorted_words.size()); ++i) {
            std::cout << std::setw(2) << (i + 1) << ". "
                      << std::left << std::setw(18) << sorted_words[i].first
                      << std::right << sorted_words[i].second << "\n";
        }
    } else {
        std::string payload = serialize_map(local_counts);
        uint64_t payload_size = payload.size();
        MPI_Send(&payload_size, 1, MPI_UINT64_T, 0, 0, MPI_COMM_WORLD);
        if (payload_size > 0) {
            MPI_Send(payload.data(), static_cast<int>(payload_size), MPI_CHAR, 0, 1, MPI_COMM_WORLD);
        }
    }

    MPI_Finalize();
    return 0;
}