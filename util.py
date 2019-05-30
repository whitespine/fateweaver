from typing import List, Callable
from inspect import signature


def predicate_transform(targ_list: List, func: Callable) -> List:
    """
    A particular function. Operates as follows:

    If the provided function func has N arguments, then for each
    sequence of N contiguous elements, func is called on those elements.

    If func returns None, nothing changes.
    If func returns a list, that list replaces the arguments it was called on.
    Iteration proceeds left to right, and restarts each time a transformation occurs
    """
    targ_list = list(targ_list)
    arg_count = len(signature(func).parameters)

    i = 0
    while i <= len(targ_list) - arg_count:
        # Get the slice
        target_slice = targ_list[i:i + arg_count]
        # Call the func
        new_slice = func(*target_slice)
        # If appropriate, re-do the list and reset. Otherwise, continue
        if new_slice is not None:
            targ_list = targ_list[:i] + new_slice + targ_list[i + arg_count:]
        else:
            i += 1

    return targ_list
