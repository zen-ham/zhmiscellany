// faster_array_diff_optimized.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <unordered_set>
#include <variant>
#include <iostream>
#include <chrono>
#include <optional>
#include <limits>
#include <stdexcept>
#include <utility>

#ifdef _WIN32
#include <intrin.h>
#else
#include <cpuid.h>
#endif

#ifdef __AVX2__
#include <immintrin.h>
#endif

#include <xmmintrin.h> // For _mm_prefetch

namespace py = pybind11;

using PyValue = std::variant<int, double, std::string, bool>;

// Simple FNV-1a based string hash that returns a 64-bit hash value.
struct SimpleStringHash {
    std::size_t operator()(const std::string& str) const {
        std::size_t hash = 1469598103934665603ull;
        for (unsigned char c : str) {
            hash ^= c;
            hash *= 1099511628211ull;
        }
        return hash;
    }
};

// Custom memory allocator (unchanged)
template <typename T>
class FastAllocator {
public:
    using value_type = T;

    FastAllocator() noexcept = default;

    template <typename U>
    FastAllocator(const FastAllocator<U>&) noexcept {}

    T* allocate(std::size_t n) {
        if (n > std::numeric_limits<std::size_t>::max() / sizeof(T))
            throw std::bad_alloc();

#ifdef _WIN32
        if (auto p = static_cast<T*>(_aligned_malloc(n * sizeof(T), 32)))
            return p;
#else
        void* ptr = nullptr;
        if (posix_memalign(&ptr, 32, n * sizeof(T)) == 0)
            return static_cast<T*>(ptr);
#endif

        throw std::bad_alloc();
    }

    void deallocate(T* p, std::size_t) noexcept {
#ifdef _WIN32
        _aligned_free(p);
#else
        free(p);
#endif
    }
};

// Updated PyValueHash uses SimpleStringHash for std::string
struct PyValueHash {
    std::size_t operator()(const PyValue& v) const {
        return std::visit([](auto&& arg) -> std::size_t {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::string>) {
                return SimpleStringHash{}(arg);
            } else {
                return std::hash<T>{}(arg);
            }
        }, v);
    }
};

struct PyValueEqual {
    bool operator()(const PyValue& lhs, const PyValue& rhs) const {
        if (lhs.index() != rhs.index()) return false;
        return std::visit([&rhs](auto&& lhs_val) -> bool {
            using T = std::decay_t<decltype(lhs_val)>;
            return lhs_val == std::get<T>(rhs);
        }, lhs);
    }
};

// Type-specific containers to avoid dispatch on every lookup.
struct FastTypeContainers {
    std::unordered_set<int, std::hash<int>, std::equal_to<int>, FastAllocator<int>> int_set;
    std::unordered_set<double, std::hash<double>, std::equal_to<double>, FastAllocator<double>> double_set;
    std::unordered_set<std::string, SimpleStringHash, std::equal_to<std::string>, FastAllocator<std::string>> string_set;
    std::unordered_set<bool> bool_set;

    void insert(const PyValue& v) {
        std::visit([this](auto&& arg) {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, int>)
                int_set.insert(arg);
            else if constexpr (std::is_same_v<T, double>)
                double_set.insert(arg);
            else if constexpr (std::is_same_v<T, std::string>)
                string_set.insert(arg);
            else if constexpr (std::is_same_v<T, bool>)
                bool_set.insert(arg);
        }, v);
    }

    bool contains(const PyValue& v) const {
        return std::visit([this](auto&& arg) -> bool {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, int>)
                return int_set.find(arg) != int_set.end();
            else if constexpr (std::is_same_v<T, double>)
                return double_set.find(arg) != double_set.end();
            else if constexpr (std::is_same_v<T, std::string>)
                return string_set.find(arg) != string_set.end();
            else if constexpr (std::is_same_v<T, bool>)
                return bool_set.find(arg) != bool_set.end();
        }, v);
    }
};

// Converts a Python object to a PyValue variant. Supports int, float, str, and bool.
PyValue py_to_variant(const py::handle& obj) {
    if (py::isinstance<py::int_>(obj)) {
        return py::cast<int>(obj);
    } else if (py::isinstance<py::float_>(obj)) {
        return py::cast<double>(obj);
    } else if (py::isinstance<py::str>(obj)) {
        return py::cast<std::string>(obj);
    } else if (py::isinstance<py::bool_>(obj)) {
        return py::cast<bool>(obj);
    } else {
        throw std::runtime_error("Unsupported type in input array");
    }
}

// Updated remove_items that precomputes conversions for l1.
std::vector<py::object> remove_items(const std::vector<py::object>& l1, const std::vector<py::object>& l2) {
    // Insert l2 items into type-specific sets.
    FastTypeContainers l2_sets;
    for (const auto& item : l2) {
        try {
            l2_sets.insert(py_to_variant(item));
        } catch (const std::exception& e) {
            continue;
        }
    }

    // Precompute conversion for l1 items to avoid repeated dynamic dispatch.
    std::vector<std::pair<py::object, std::optional<PyValue>>> l1_conversions;
    l1_conversions.reserve(l1.size());
    for (const auto& item : l1) {
        try {
            PyValue v = py_to_variant(item);
            l1_conversions.push_back({item, std::move(v)});
        } catch (const std::exception& e) {
            l1_conversions.push_back({item, std::nullopt});
        }
    }

    std::vector<py::object> result;
    result.reserve(l1.size());
    for (size_t i = 0; i < l1_conversions.size(); ++i) {
        // Prefetch future elements to improve cache utilization.
        if (i + 8 < l1_conversions.size()) {
            _mm_prefetch(reinterpret_cast<const char*>(&l1_conversions[i + 8]), _MM_HINT_T0);
        }
        const auto& [obj, maybe_variant] = l1_conversions[i];
        // If conversion failed or the converted value is not in l2, keep the item.
        if (!maybe_variant.has_value() || !l2_sets.contains(maybe_variant.value())) {
            result.push_back(obj);
        }
    }
    return result;
}

// Updated remove_items_alt with precomputation.
std::vector<py::object> remove_items_alt(const std::vector<py::object>& l1, const std::vector<py::object>& l2) {
    std::unordered_set<PyValue, PyValueHash, PyValueEqual, FastAllocator<PyValue>> l2_set;
    l2_set.reserve(l2.size());

    for (const auto& item : l2) {
        try {
            l2_set.insert(py_to_variant(item));
        } catch (const std::exception& e) {
            continue;
        }
    }

    // Precompute conversion for l1 items.
    std::vector<std::pair<py::object, std::optional<PyValue>>> l1_conversions;
    l1_conversions.reserve(l1.size());
    for (const auto& item : l1) {
        try {
            PyValue v = py_to_variant(item);
            l1_conversions.push_back({item, std::move(v)});
        } catch (const std::exception& e) {
            l1_conversions.push_back({item, std::nullopt});
        }
    }

    std::vector<py::object> result;
    result.reserve(l1.size());
    for (size_t i = 0; i < l1_conversions.size(); ++i) {
        if (i + 8 < l1_conversions.size()) {
            _mm_prefetch(reinterpret_cast<const char*>(&l1_conversions[i + 8]), _MM_HINT_T0);
        }
        const auto& [obj, maybe_variant] = l1_conversions[i];
        if (!maybe_variant.has_value() || (l2_set.find(maybe_variant.value()) == l2_set.end())) {
            result.push_back(obj);
        }
    }
    return result;
}

// Numeric-optimized version remains unchanged.
std::vector<py::object> remove_items_numeric_optimized(const std::vector<py::object>& l1, const std::vector<py::object>& l2) {
    bool all_ints_l1 = true;
    bool all_ints_l2 = true;

    for (const auto& item : l1) {
        if (!py::isinstance<py::int_>(item)) {
            all_ints_l1 = false;
            break;
        }
    }

    for (const auto& item : l2) {
        if (!py::isinstance<py::int_>(item)) {
            all_ints_l2 = false;
            break;
        }
    }

    if (all_ints_l1 && all_ints_l2 && l2.size() <= 64) {
#ifdef __AVX2__
        std::vector<int> l2_ints;
        l2_ints.reserve(l2.size());
        for (const auto& item : l2) {
            l2_ints.push_back(py::cast<int>(item));
        }

        std::vector<py::object> result;
        result.reserve(l1.size());
        for (const auto& item : l1) {
            int val = py::cast<int>(item);
            bool found = false;
            for (size_t i = 0; i + 8 <= l2_ints.size(); i += 8) {
                __m256i needle = _mm256_set1_epi32(val);
                __m256i haystack = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(&l2_ints[i]));
                __m256i cmp = _mm256_cmpeq_epi32(needle, haystack);
                int mask = _mm256_movemask_ps(_mm256_castsi256_ps(cmp));
                if (mask != 0) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                for (size_t i = (l2_ints.size() / 8) * 8; i < l2_ints.size(); ++i) {
                    if (val == l2_ints[i]) {
                        found = true;
                        break;
                    }
                }
            }
            if (!found) {
                result.push_back(item);
            }
        }
        return result;
#else
        return remove_items(l1, l2);
#endif
    }

    return remove_items(l1, l2);
}

std::pair<std::vector<py::object>, double> benchmark_remove_items(
    const std::vector<py::object>& l1,
    const std::vector<py::object>& l2) {

    auto start = std::chrono::high_resolution_clock::now();
    auto result = remove_items(l1, l2);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double, std::milli> duration = end - start;
    return {result, duration.count()};
}

std::pair<std::vector<py::object>, double> benchmark_remove_items_alt(
    const std::vector<py::object>& l1,
    const std::vector<py::object>& l2) {

    auto start = std::chrono::high_resolution_clock::now();
    auto result = remove_items_alt(l1, l2);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double, std::milli> duration = end - start;
    return {result, duration.count()};
}

std::pair<std::vector<py::object>, double> benchmark_remove_items_numeric(
    const std::vector<py::object>& l1,
    const std::vector<py::object>& l2) {

    auto start = std::chrono::high_resolution_clock::now();
    auto result = remove_items_numeric_optimized(l1, l2);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double, std::milli> duration = end - start;
    return {result, duration.count()};
}

PYBIND11_MODULE(faster_array_diff, m) {
    m.doc() = "Fast array difference implementation using C++ and pybind11 with optimizations for heterogeneous data";

    m.def("remove_items", &remove_items,
          "Remove all elements of l2 from l1 using optimized type-specific containers",
          py::arg("l1"), py::arg("l2"));

    m.def("remove_items_alt", &remove_items_alt,
          "Alternative implementation using original hash set with optimizations",
          py::arg("l1"), py::arg("l2"));

    m.def("remove_items_numeric", &remove_items_numeric_optimized,
          "Optimized implementation for numeric data using AVX2 when available",
          py::arg("l1"), py::arg("l2"));

    m.def("benchmark_remove_items", &benchmark_remove_items,
          "Benchmark the optimized remove_items function and return result with execution time in ms",
          py::arg("l1"), py::arg("l2"));

    m.def("benchmark_remove_items_alt", &benchmark_remove_items_alt,
          "Benchmark the alternative implementation and return result with execution time in ms",
          py::arg("l1"), py::arg("l2"));

    m.def("benchmark_remove_items_numeric", &benchmark_remove_items_numeric,
          "Benchmark the numeric-optimized implementation and return result with execution time in ms",
          py::arg("l1"), py::arg("l2"));
}