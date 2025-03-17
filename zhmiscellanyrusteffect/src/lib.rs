use jwalk::WalkDir;
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use ordered_float::OrderedFloat;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use std::arch::x86_64::*;
use std::collections::HashSet;

#[pyfunction]
fn np_mean(numbers: PyReadonlyArray1<f64>) -> PyResult<f64> {
    let array = numbers.as_array();
    Ok(array.sum() / array.len() as f64)
}

#[pyfunction]
fn np_sum(numbers: PyReadonlyArray1<f64>) -> PyResult<f64> {
    let array = numbers.as_array();
    Ok(array.sum() as f64)
}

#[pyfunction]
fn np_median(numbers: PyReadonlyArray1<f64>) -> PyResult<f64> {
    let mut numbers = numbers.as_array().to_vec();
    let len = numbers.len();

    if len == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err("Empty list"));
    }

    numbers.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap());
    let mid = len / 2;

    if len % 2 == 0 {
        Ok((numbers[mid - 1] + numbers[mid]) / 2.0)
    } else {
        Ok(numbers[mid])
    }
}

/// Recursively lists all files in a given folder.
#[pyfunction]
fn list_files_recursive(folder: String) -> PyResult<Vec<String>> {
    let files: Vec<String> = WalkDir::new(folder)
        .skip_hidden(false)
        .into_iter()
        .flatten()
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| entry.path().to_string_lossy().into_owned())
        .collect();

    Ok(files)
}

#[pyfunction]
fn np_list_subtract<'py>(
    py: Python<'py>,
    l1: PyReadonlyArray1<f64>,
    l2: PyReadonlyArray1<f64>,
) -> PyResult<Py<PyArray1<f64>>> {
    let arr1 = l1.as_array();
    let arr2 = l2.as_array();
    let remove_set: HashSet<OrderedFloat<f64>> = arr2.iter().cloned().map(OrderedFloat).collect();

    let mut result = Vec::with_capacity(arr1.len());
    let mut i = 0;

    unsafe {
        if is_x86_feature_detected!("avx2") {
            let len = arr1.len();
            while i + 4 <= len {
                let chunk = _mm256_loadu_pd(arr1.as_ptr().add(i)); // Load 4 doubles
                let mask = _mm256_cmp_pd(chunk, _mm256_set1_pd(0.0), _CMP_NEQ_OQ); // Compare against 0
                let mask_bits = _mm256_movemask_pd(mask);

                if mask_bits != 0 {
                    for j in 0..4 {
                        let val = *arr1.get(i + j).unwrap();
                        if !remove_set.contains(&OrderedFloat(val)) {
                            result.push(val);
                        }
                    }
                }
                i += 4;
            }
        }
    }

    // Process the remainder
    for &x in &arr1[i..] {
        if !remove_set.contains(&OrderedFloat(x)) {
            result.push(x);
        }
    }

    Ok(result.into_pyarray(py).to_owned().into())
}

#[pymodule]
fn zhmiscellanyrusteffect(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(np_mean, m)?)?;
    m.add_function(wrap_pyfunction!(np_median, m)?)?;
    m.add_function(wrap_pyfunction!(list_files_recursive, m)?)?;
    m.add_function(wrap_pyfunction!(np_sum, m)?)?;
    m.add_function(wrap_pyfunction!(np_list_subtract, m)?)?;
    Ok(())
}
