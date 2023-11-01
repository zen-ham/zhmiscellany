def remove_duplicates(l_list):
    return list(dict.fromkeys(l_list))


def subtract_lists(lists):
    l_list = []
    for i in lists:
        l_list.extend(i)
    return remove_duplicates(l_list)


def remove_duplicates_by_element(tuple_list, element):
    seen = {}
    result = []
    for tpl in tuple_list:
        if tpl[element] not in seen:
            seen[tpl[element]] = True
            result.append(tpl)
    return result
