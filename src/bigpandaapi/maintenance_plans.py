"""Functions for maintenance plans via BigPanda Maintenance Plans v2 API.

This implements functions that abstract the maintenance-plan-related parts
of BigPanda's API.

Typical usage example:

  bigpandaapi.maintenance_plan_create(my_list_of_dicts,
                                 "my_enrichment",
                                 "API-KEY-HERE")
"""

from __future__ import annotations  # TypedDict NotRequired Support for <3.10

import json
from datetime import datetime
from datetime import timezone
from typing import Any

import dateutil
import pytimeparse2  # type: ignore
import requests
from typing_extensions import NotRequired  # TypedDict NotRequired Support for <3.11
from typing_extensions import TypedDict  # TypedDict NotRequired Support for <3.11

from .exceptions import BigPandaAPIException


__base_uri: str = "https://api.bigpanda.io/resources/v2.0"


def maintenance_plan_create(  # noqa: C901
    name: str,
    condition: dict[str, Any],
    api_key: str,
    description: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    end_time_delta: str | None = None,
) -> None:
    """Creates a BigPanda Maintenance Plan.

    Takes input values defining (at least) a condition and schedule for a BigPanda
    maintenance plan and creates it.

    Args:
        name: A string to define the name of the plan.
        condition: A query in BPQL object format (see
            https://docs.bigpanda.io/reference/bpql-object-syntax) that defines which
            incidents should be subject to the maintenance plan.
        start_time: An optional string containing a datetime for the the maintenance
            plan to begin. If excluded, the time that this function is executed will be
            used as the start time. ISO 8601 format is recommended, and UTC will be
            assumed as the timezone if not specified.
        end_time: A string containing a datetime for the the maintenance plan to end.
            ISO 8601 format is recommended, and UTC will be assumed as the timezone if
            not specified.  Either end_time or end_time_delta must be provided to
            this function, but not both.
        end_time_delta: A string containing a time delta to end the plan that
            will be computed based on the value of start_time. Can parse any format
            that pytimeparse2 can understand, but the '#d#h#m' format is recommended.
        api_key: An API key to authenticate to the BigPanda API.
        description: An optional string describing the maintenance plan that will be
            shown in the BigPanda UI.

    Raises:
        ValueError: An incorrect argument or combination of arguments was provided.
        BigPandaAPIException: BigPanda's API returned an error.
    """
    if start_time:
        try:
            start_time_datetime = dateutil.parser.parse(start_time)
        except dateutil.parser.ParserError as exc:
            raise ValueError("Unable to parse 'start_time'") from exc
    else:
        start_time_datetime = datetime.now(timezone.utc)
    if end_time and end_time_delta:
        raise ValueError(
            "Only one of the arguments 'end_time' and 'end_time_delta' can be provided."
        )
    elif end_time is None and end_time_delta is None:
        raise ValueError(
            "One of either argument 'end_time' or 'end_time_delta' must be provided."
        )
    elif end_time:
        try:
            end_time_datetime = dateutil.parser.parse(end_time)
        except dateutil.parser.ParserError as exc:
            raise ValueError("Unable to parse 'end_time'") from exc
    elif end_time_delta:
        try:
            end_time_delta_timedelta = pytimeparse2.parse(
                end_time_delta, raise_exception=True, as_timedelta=True
            )
        except ValueError as exc:
            raise ValueError("Unable to parse 'end_time_delta'") from exc
        end_time_datetime = start_time_datetime + end_time_delta_timedelta

    class MaintenancePlanBody(TypedDict):
        name: str
        condition: dict[str, Any]
        start: int
        end: int
        description: NotRequired[str]

    body: MaintenancePlanBody = {
        "name": name,
        "condition": condition,
        "start": int(round(start_time_datetime.timestamp())),
        "end": int(round(end_time_datetime.timestamp())),
    }
    if description:
        body["description"] = description

    print("Creating maintenance plan...")
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Content-Type": "application/json"})
    bp_session.headers.update({"Authorization": f"Bearer {api_key}"})

    print(json.dumps(body))

    try:
        bp_session.post(f"{__base_uri}/maintenance-plans", data=json.dumps(body))
    except requests.RequestException as exc:
        raise BigPandaAPIException("Creating maintenance plan failed.") from exc
