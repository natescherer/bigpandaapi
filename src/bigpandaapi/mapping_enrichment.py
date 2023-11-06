"""Functions for mapping enrichments via BigPanda Alert Enrichment v2.1 API.

This implements functions that abstract the mapping-enrichment-related parts
of BigPanda's API.

Typical usage example:

  bigpandaapi.update_table(my_list_of_dicts,
                                 "my_enrichment",
                                 "API-KEY-HERE")
"""

import json
import time
from typing import Dict
from typing import List
from typing import Optional

import requests

from .exceptions import BigPandaAPIException
from .private import _list_of_dicts_to_csv_str


__base_uri: str = "https://api.bigpanda.io/resources/v2.1"


def mapping_update_table(
    input_list: List[Dict[str, str]],
    enrichment_name: str,
    api_key: str,
) -> None:
    """Updates a BigPanda Mapping Enrichment Table.

    Takes a list of dicts and updates an existing BigPanda Mapping Enrichment
    table. The table's schema must have already been defined at BigPanda.

    Args:
        input_list: A list of dictionaries containing the data to add to the
            table.
        enrichment_name: The name of the enrichment, which must have been
            already defined at BigPanda.
        api_key: An API key to authenticate to the BigPanda API.

    Raises:
        BigPandaAPIException: BigPanda's API returned an error.
    """
    # Construct session
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Authorization": f"Bearer {api_key}"})

    # Get the internal ID of the mapping enrichment based on the name
    print("Getting mapping ID from BigPanda...")
    r_id = bp_session.get(f"{__base_uri}/mapping-enrichment")
    mapping_enrichment = next(
        item
        for item in r_id.json()["data"]
        if item["config"]["name"] == enrichment_name
    )
    mapping_id = mapping_enrichment["id"]
    print(f"Enrichment {enrichment_name} has id {mapping_id}.")

    # Upload new mapping enrichment data
    r_upload = bp_session.post(
        f"{__base_uri}/mapping-enrichment/{mapping_id}/map",
        headers={"Content-Type": "text/csv; charset=utf8"},
        data=_list_of_dicts_to_csv_str(input_list).encode("UTF-8"),
    )
    try:
        job_id = r_upload.json()["job_id"]
    except KeyError as exc:
        raise BigPandaAPIException(
            "Job ID not returned by upload to BigPanda."
        ) from exc
    while True:
        print("Waiting 5 seconds for upload to process...")
        time.sleep(5)
        r_status = bp_session.get(f"{__base_uri}/alert-enrichments-jobs/{job_id}")
        if r_status.json()["status"] == "done" or r_status.json()["status"] == "failed":
            break

    # Finish up
    if r_status.json()["status"] == "done":
        print("Upload complete.")
    else:
        raise BigPandaAPIException(f"Upload with job ID {job_id} failed!")


def mapping_create_schema(
    query_tag: str, result_tag: str, api_key: str, enrichment_name: Optional[str] = None
) -> None:
    """Creates the schema for a new BigPanda Mapping Enrichment.

    Creates the schema for a new BigPanda Mapping Enrichment. This must be done
    before populating it with data via 'create_table' or 'update_table'.

    Args:
        query_tag: The name of the source tag that should be used to look up
            values in the table.
        result_tag: The name of the target tag that should be populated by
            the lookup in the table.
        api_key: An API key to authenticate to the BigPanda API.
        enrichment_name: The name of the enrichment. If not specified, defaults
            to the value of 'result_tag'.

    Raises:
        BigPandaAPIException: BigPanda's API returned an error.
    """
    if enrichment_name is None:
        enrichment_name = result_tag

    mapping_config = {
        "type": "mapping",
        "active": True,
        "when": "discard != true",
        "config": {
            "name": result_tag,
            "fields": [
                {"title": query_tag, "type": "query_tag"},
                {"title": result_tag, "type": "result_tag", "override_existing": True},
            ],
        },
    }

    print("Creating enrichment...")
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Content-Type": "application/json"})
    bp_session.headers.update({"Authorization": f"Bearer {api_key}"})

    try:
        bp_session.post(
            f"{__base_uri}/mapping-enrichment", data=json.dumps(mapping_config)
        )
    except requests.RequestException as exc:
        raise BigPandaAPIException(
            "Creation of mapping enrichment schema failed."
        ) from exc
    print("Done!")
