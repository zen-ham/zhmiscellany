def print_dict(data, is_recursion=False):
    if is_recursion:
        stuff = []
        for key, value in data.items():
            if isinstance(value, dict):
                stuff.extend(print_dict(value, True))
            else:
                stuff.extend([f'{key}: {value}'])
        return stuff
    else:
        print('\n'.join(print_dict(data, True)))
