
def add_value_to_indexed_list(index_dict: dict, key, value) -> None:
    if key in index_dict:
        index_dict[key].append(value)
    else:
        index_dict[key] = [value]