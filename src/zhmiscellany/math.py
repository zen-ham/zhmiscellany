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


def generate_grid(top_left, bottom_right, rows, cols, int_coords=True, row_major=True):
    x = np.linspace(top_left[0], bottom_right[0], cols)
    y = np.linspace(top_left[1], bottom_right[1], rows)
    grid = np.array(np.meshgrid(x, y)).T.reshape(-1, 2)

    if int_coords:
        grid = np.rint(grid).astype(int)

    grid = list(grid)

    grid = [(c[0], c[1]) for c in grid]

    if not row_major:
        grid.sort(key=lambda coord: (coord[1], coord[0]))
        return grid
    else:
        return [tuple(coord) for coord in grid]


def generate_eased_points(p1, p2, num_points):
    def ease_in_out(t):
        return t * t * (3 - 2 * t)  # Smoothstep formula
    x1, y1 = p1
    x2, y2 = p2

    # Generate normalized times (t) from 0 to 1
    t_values = np.linspace(0, 1, num_points)

    # Apply ease-in-out transformation to the normalized times
    eased_t_values = ease_in_out(t_values)

    # Interpolate x and y values using the eased t values
    points = [
        (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        for t in eased_t_values
    ]

    return points