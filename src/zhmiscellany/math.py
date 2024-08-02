

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
    return [interval * i for i in range(segments)]


def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)
