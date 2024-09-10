import numpy as np


def smart_percentage(things, total_things):
    if total_things == 0:
        return total_things
    else:
        div = 0
        while 100/total_things < 1/(10**div):
            div += 1
        percentage = round((things/total_things)*100, div)
        if str(percentage).endswith('.0'):
            return round(percentage)
        else:
            return percentage


def calculate_evenly_spaced_points(duration, segments, offset=0):
    interval = duration / (segments - 1)
    return [(interval * i)+offset for i in range(segments)]


def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)


def generate_grid(top_left, bottom_right, rows, cols, int_coords=True):
    x = np.linspace(top_left[0], bottom_right[0], cols)
    y = np.linspace(top_left[1], bottom_right[1], rows)
    grid = np.array(np.meshgrid(x, y)).T.reshape(-1, 2)

    if int_coords:
        grid = np.rint(grid).astype(int)

    return [tuple(coord) for coord in grid]
