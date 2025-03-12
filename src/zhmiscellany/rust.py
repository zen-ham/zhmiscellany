import zhmiscellanyrusteffect
import numpy as np

list_files_recursive = zhmiscellanyrusteffect.list_files_recursive
def numpy_mean(np_arr):
    return zhmiscellanyrusteffect.np_mean(np_arr.astype(np.float64, copy=False))
def numpy_sum(np_arr):
    return zhmiscellanyrusteffect.np_sum(np_arr.astype(np.float64, copy=False))
def numpy_median(np_arr):
    return zhmiscellanyrusteffect.np_median(np_arr.astype(np.float64, copy=False))

def mean(lst):
    array = np.array(lst, dtype=np.float64)
    return zhmiscellanyrusteffect.np_mean(array)

def sum(lst):
    array = np.array(lst, dtype=np.float64)
    return zhmiscellanyrusteffect.np_sum(array)

def median(lst):
    array = np.array(lst, dtype=np.float64)
    return zhmiscellanyrusteffect.np_median(array)