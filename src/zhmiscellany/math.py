import time
import zhmiscellany.string


def calculate_eta(timestamps, total_timestamps):
    if not timestamps:
        return "Not enough data to calculate ETA."

    if total_timestamps <= len(timestamps):
        return "All timestamps recorded."

    # Calculate average time per timestamp
    total_time = timestamps[-1] - timestamps[0]
    average_time_per_timestamp = total_time / len(timestamps)

    # Calculate remaining time based on the average time per timestamp
    remaining_timestamps = total_timestamps - len(timestamps)
    estimated_remaining_time = remaining_timestamps * average_time_per_timestamp

    # Calculate the estimated arrival time
    current_time = time.time()
    estimated_arrival_time = current_time + estimated_remaining_time

    return zhmiscellany.string.timestamp_to_time(estimated_arrival_time)


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
