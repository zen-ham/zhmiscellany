import zhmiscellanyrusteffect

list_files_recursive = zhmiscellanyrusteffect.list_files_recursive
def numpy_mean(np_arr):
    import numpy as np
    return zhmiscellanyrusteffect.np_mean(np_arr.astype(np.float64, copy=False))
def numpy_sum(np_arr):
    import numpy as np
    return zhmiscellanyrusteffect.np_sum(np_arr.astype(np.float64, copy=False))
def numpy_median(np_arr):
    import numpy as np
    return zhmiscellanyrusteffect.np_median(np_arr.astype(np.float64, copy=False))