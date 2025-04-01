import string, time, datetime


def convert_to_base62(number):
    number = int(str(number).replace('.', ''))
    # Base 62 characters: digits (0-9), lowercase letters (a-z), and uppercase letters (A-Z)
    base62_chars = string.digits + string.ascii_lowercase + string.ascii_uppercase
    if number == 0:
        return base62_chars[0]

    base62_str = ''
    while number > 0:
        number, remainder = divmod(number, 62)
        base62_str = base62_chars[remainder] + base62_str

    return base62_str


def get_universally_unique_string():
    #number = None
    #if not number:
    timestamp = str(time.perf_counter_ns())
    #else:
    #    timestamp = number
    unique_number = int(timestamp)

    unique_filename = convert_to_base62(unique_number)
    return unique_filename


def multi_replace(string, replaces, recursive=False):
    st = ''
    while st != string:
        st = string
        for i in replaces:
            string = string.replace(i[0], i[1])
        if not recursive:
            break
    return string


def timestamp_to_time(unix_timestamp):
    # Convert the Unix timestamp to a datetime object
    dt_object = datetime.datetime.fromtimestamp(unix_timestamp)

    # Convert the datetime object to a time of day
    time_of_day = dt_object.strftime('%H:%M:%S')

    return time_of_day


def truncate_string(input_string, max_length):
    if len(input_string) <= max_length:
        return input_string
    else:
        return input_string[:max_length]


def concatenate_strings_to_length(strings, limit):
    output = []
    tstring = ''
    temp = ''
    for string in strings:
        tstring = temp
        temp = f'{temp}{string}'
        if len(temp) > limit:
            output.append(tstring)
            temp = string
    output.append(tstring)
    return output


def smart_round(number, decimals=0):
    if str(round(number, decimals)).endswith('.0'):
        return round(number)
    else:
        return round(number, decimals)


def convert_bytes(size):
    power = 2**10
    n = 0
    units = {0: 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB', 5: 'PB', 6: 'EB', 7: 'ZB', 8: 'YB'}

    while size > power:
        size /= power
        n += 1

    return f"{smart_round(size, 2)}{units[n]}"


def multi_split(string, splits):
    string = [string]
    for i in splits:
        temp = []
        for stri in string:
            temp.extend(stri.split(i))
        string = temp
    string = [i for i in string if i != '']

    return string


def format_duration(seconds):
    # Define time units in seconds
    minute, hour, day = 60, 3600, 86400
    week = day * 7
    month = day * 30  # Approximation, since months vary in length
    year = day * 365  # Approximation, not accounting for leap years

    # Calculate the number of years, months, weeks, days, hours, minutes, and seconds
    years = seconds // year
    seconds %= year
    months = seconds // month
    seconds %= month
    weeks = seconds // week
    seconds %= week
    days = seconds // day
    seconds %= day
    hours = seconds // hour
    seconds %= hour
    minutes = seconds // minute
    seconds %= minute

    # Build the formatted string
    parts = []
    if years > 0:
        parts.append(f"{round(years) if str(years).endswith('.0') else years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{round(months) if str(months).endswith('.0') else months} month{'s' if months != 1 else ''}")
    if weeks > 0:
        parts.append(f"{round(weeks) if str(weeks).endswith('.0') else weeks} week{'s' if weeks != 1 else ''}")
    if days > 0:
        parts.append(f"{round(days) if str(days).endswith('.0') else days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{round(hours) if str(hours).endswith('.0') else hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{round(minutes) if str(minutes).endswith('.0') else minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts:
        parts.append(f"{round(seconds) if str(seconds).endswith('.0') else seconds} second{'s' if seconds != 1 else ''}")

    return ', '.join(parts)


def filter_chars(input_string, filter_string):
    result = ""
    for c in list(input_string):
        if c in filter_string:
            result += c
    return result


def truncate_middle(s, length, truncation_string='...'):
    if length >= len(s):
        return s

    left_len = (length - len(truncation_string)) // 2
    right_len = length - len(truncation_string) - left_len

    truncated = s[:left_len] + truncation_string + s[-right_len:]
    return truncated