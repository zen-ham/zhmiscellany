def remove_duplicates(l_list):
    return list(dict.fromkeys(l_list))


def subtract_lists(lists):
    l_list = []
    for i in lists:
        l_list.extend(i)
    return remove_duplicates(l_list)