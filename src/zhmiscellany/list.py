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
