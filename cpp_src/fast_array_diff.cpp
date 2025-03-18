// fast_array_diff.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <unordered_set>
#include <variant>
#include <iostream>
#include <chrono>

namespace py = pybind11;

using PyValue = std::variant<int, double, std::string, bool>;

struct PyValueHash {
    std::size_t operator()(const PyValue& v) const {
        return std::visit([](auto&& arg) -> std::size_t {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::string>) {
                return std::hash<std::string>{}(arg);
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

std::vector<py::object> remove_items(const std::vector<py::object>& l1, const std::vector<py::object>& l2) {
    std::unordered_set<PyValue, PyValueHash, PyValueEqual> l2_set;
    for (const auto& item : l2) {
        try {
            l2_set.insert(py_to_variant(item));
        } catch (const std::exception& e) {
            continue;
        }
    }
    
    std::vector<py::object> result;
    result.reserve(l1.size()); // I am preallocate space since it's wayyy faster
    
    for (const auto& item : l1) {
        try {
            PyValue v = py_to_variant(item);
            if (l2_set.find(v) == l2_set.end()) {
                result.push_back(item);
            }
        } catch (const std::exception& e) {
            result.push_back(item);
        }
    }
    
    return result;
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

PYBIND11_MODULE(fast_array_diff, m) {
    m.doc() = "Fast array difference implementation using C++ and pybind11";
    m.def("remove_items", &remove_items, "Remove all elements of l2 from l1",
          py::arg("l1"), py::arg("l2"));
    m.def("benchmark_remove_items", &benchmark_remove_items, 
          "Benchmark the remove_items function and return result with execution time in ms",
          py::arg("l1"), py::arg("l2"));
}
