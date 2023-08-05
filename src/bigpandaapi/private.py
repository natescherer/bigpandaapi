"""bigpandaapi's privates.

This module contains the set of bigpandaapi's private functions and classes.
"""

import csv
import io
from typing import Dict, List


def _list_of_dicts_to_csv_str(input_list: List[Dict[str, str]]) -> str:
    """Converts a list of dicts to CSV format.

    Takes a list of dicts and converts it to a string containing the data in
    CSV format.

    Args:
        input_list: A list of dictionaries.

    Returns:
        String in CSV format containing the same data as the input_list arg.

    Raises:
        None
    """
    fieldnames_set = set()
    for internal_dict in input_list:
        for field in internal_dict:
            fieldnames_set.add(field)
    sorted_fieldnames = sorted(fieldnames_set)

    with io.StringIO() as csv_string:
        writer = csv.DictWriter(
            csv_string,
            fieldnames=sorted_fieldnames,
            extrasaction='ignore',
            dialect="unix")
        writer.writeheader()
        writer.writerows(input_list)
        return csv_string.getvalue()
