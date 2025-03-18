use jwalk::WalkDir;
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
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

#[pymodule]
fn zhmiscellanyrusteffect(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(np_mean, m)?)?;
    m.add_function(wrap_pyfunction!(np_median, m)?)?;
    m.add_function(wrap_pyfunction!(list_files_recursive, m)?)?;
    m.add_function(wrap_pyfunction!(np_sum, m)?)?;
    Ok(())
}
