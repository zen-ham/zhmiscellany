from itertools import chain

def remove_duplicates(l_list):
    return list(dict.fromkeys(l_list))


def subtract_lists(main_list, *other_lists):
    # Create a set of all items in other lists
    other_items = set(item for sublist in other_lists for item in sublist)

    # Return items from the main list that are not in other lists
    return [item for item in main_list if item not in other_items]


def remove_duplicates_by_element(tuple_list, element):
    seen = {}
    result = []
    for tpl in tuple_list:
        if tpl[element] not in seen:
            seen[tpl[element]] = True
            result.append(tpl)
    return result


def multi_split(string_list, splits):
    string = string_list
    for i in splits:
        temp = []
        for stri in string:
            temp.extend(stri.split(i))
        string = temp

    return string


def split_into_n_groups(lst, n):
    avg_size = len(lst) // n
    remainder = len(lst) % n
    sublists = []
    
    start = 0
    for i in range(n):
        end = start + avg_size + (1 if i < remainder else 0)  # Distribute remainder
        sublists.append(lst[start:end])
        start = end
    
    return sublists


def split_into_sublists(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def flatten(an_iterable):
    return list(chain.from_iterable(an_iterable))


def dedupe(an_iterable):
    return list(dict.fromkeys(an_iterable))