import numpy as np


def image_diff(img1, img2):
    img1 = img1.resize((100, 100))
    img2 = img2.resize((100, 100))

    # Convert images to numpy arrays
    img_arr1 = np.array(img1)
    img_arr2 = np.array(img2)

    # Calculate RMSE
    mse = np.mean((img_arr1 - img_arr2) ** 2)
    rmse = np.sqrt(mse)
    return rmse