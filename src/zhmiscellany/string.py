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


def multi_replace(string, replaces):
    for i in replaces:
        string = string.replace(i[0], i[1])
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


def remove_duplicate_lines(file_path):
    with open(file_path, 'r') as f:
        file_data = f.read()
    file_data = file_data.split('\n')
    file_data = list(dict.fromkeys(file_data))
    file_data = '\n'.join(file_data)
    return file_data