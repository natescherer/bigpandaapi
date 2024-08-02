"""bigpandaapi's privates.

This module contains the set of bigpandaapi's private functions and classes.
"""

import csv
import io
from typing import Dict
from typing import List


def _extract_enrichment_name_from_csv(csv_path: str) -> str:
    """Extracts the enrichment name from a csv file at the input path.

    Takes the path of a csv file, loads the file's data, and parses the
    enrichment name from the file data.

    Args:
        csv_path: The path to a CSV file containing the enrichment data.

    Returns:
        String containing the name of the enrichment.

    Raises:
        None
    """
    with open(csv_path) as csvfile:
        first_line = csvfile.readline()

    return first_line.rstrip("\n").split(",")[1]


def _list_of_dicts_to_csv_str(list_of_dicts: List[Dict[str, str]]) -> str:
    """Converts a list of dicts to CSV format.

    Takes a list of dicts and converts it to a string containing the data in
    CSV format.

    Args:
        list_of_dicts: A list of dictionaries defining the enrichment data.

    Returns:
        String in CSV format containing the same data as the list_of_dicts arg.

    Raises:
        None
    """
    fieldnames_set = set()
    for internal_dict in list_of_dicts:
        for field in internal_dict:
            fieldnames_set.add(field)
    sorted_fieldnames = sorted(fieldnames_set)

    with io.StringIO() as csv_string:
        writer = csv.DictWriter(
            csv_string,
            fieldnames=sorted_fieldnames,
            extrasaction="ignore",
            dialect="unix",
        )
        writer.writeheader()
        writer.writerows(list_of_dicts)
        return csv_string.getvalue()
