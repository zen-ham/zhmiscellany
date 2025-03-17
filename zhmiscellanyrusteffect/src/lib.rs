use jwalk::WalkDir;
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use ordered_float::OrderedFloat;
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

#[pyfunction]
fn np_list_subtract<'py, T>(
    py: Python<'py>,
    l1: PyReadonlyArray1<T>,
    l2: PyReadonlyArray1<T>,
) -> PyResult<Py<PyArray1<T>>>
where
    T: numpy::Element + Clone + Eq + Hash,
{
    let arr1 = l1.as_array();
    let arr2 = l2.as_array();
    let remove_set: HashSet<T> = arr2.iter().cloned().collect();
    let result: Vec<T> = arr1
        .iter()
        .cloned()
        .filter(|x| !remove_set.contains(x))
        .collect();
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
