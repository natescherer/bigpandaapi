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
import re
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
    """Creates a BigPanda maintenance plan.

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

    Returns:
        list: A list of dicts representing the JSON data returned by BigPanda's API.

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

    try:
        r = bp_session.post(f"{__base_uri}/maintenance-plans", data=json.dumps(body))
    except requests.RequestException as exc:
        raise BigPandaAPIException("Creating maintenance plan failed.") from exc

    return r.json()


def maintenance_plan_get(
    api_key: str,
    id: str | None = None,
    only_active: bool = False,
    name: str | None = None,
):
    """Gets all BigPanda maintenance plans.

    Returns all BigPanda maintenance plans that the provided api_key has access to.

    Args:
        id: Optional string of a plan ID, which will cause this function to
            retrieve just that plan.
        name: Optional string of a regular expression which will be used to filter
            plans based on name. Providing this will cause the function to only return
            plans that match the provided regex. Important caveat: Names of maintenance
            plans are NOT required to be unique in BigPanda, so you can't be sure that
            a search for a static string will only return one plan.
        only_active: If set to True, will only return active maintenace plans instead
            of plans with any status.
        api_key: An API key to authenticate to the BigPanda API.

    Returns:
        list: A list of dicts representing the JSON data returned by BigPanda's API.

    Raises:
        ValueError: An incorrect argument was provided.
        BigPandaAPIException: BigPanda's API returned an error.
    """
    if name:
        try:
            name_pattern = re.compile(name)
        except re.error as exc:
            raise ValueError("Unable to compile 'name' into a regex.") from exc

    print("Getting maintenance plans...")
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Content-Type": "application/json"})
    bp_session.headers.update({"Authorization": f"Bearer {api_key}"})

    try:
        r = bp_session.get(f"{__base_uri}/maintenance-plans?active={only_active}")
    except requests.RequestException as exc:
        raise BigPandaAPIException("Getting maintenance plans failed.") from exc

    if r.status_code == 204:
        return []
    else:
        plan_list = r.json()
        if name:
            plan_list = [item for item in plan_list if name_pattern.match(item["name"])]
        elif id:
            plan_list = [item for item in plan_list if item["id"] == id]

        return plan_list


def maintenance_plan_delete(api_key: str, id: str):
    """Deletes a BigPanda maintenance plan.

    Deletes a BigPanda maintenance plan from the UI/API. If the plan is active, it will
    stop being enforced. You can also use maintenance_plan_stop to stop a plan from
    being active but maintain a record of the in the UI/API.

    Args:
        id: String of a plan ID to be deleted. Note that deleting via name is
            intentionally not provided as maintenance plan names in BigPanda are not
            forced to be unique. If you need to look up a plan ID, use the
            maintenance_plan_get function.
        api_key: An API key to authenticate to the BigPanda API.

    Raises:
        BigPandaAPIException: BigPanda's API returned an error.
    """
    print(f"Deleting maintenance plan with id {id!r}...")
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Content-Type": "application/json"})
    bp_session.headers.update({"Authorization": f"Bearer {api_key}"})

    try:
        bp_session.delete(f"{__base_uri}/maintenance-plans/{id}")
    except requests.RequestException as exc:
        raise BigPandaAPIException("Deleting maintenance plan failed.") from exc


def maintenance_plan_stop(api_key: str, id: str):
    """Stops a BigPanda maintenance plan.

    Stops an active BigPanda maintenance plan while leaving a record of it in the
    UI/API. You can also use maintenance_plan_delete to stop and delete the record of
    an active plan in one step.

    Args:
        id: String of a plan ID to be stopped. Note that stopping via name is
            intentionally not provided as maintenance plan names in BigPanda are not
            forced to be unique. If you need to look up a plan ID, use the
            maintenance_plan_get function.
        api_key: An API key to authenticate to the BigPanda API.

    Raises:
        BigPandaAPIException: BigPanda's API returned an error.
    """
    print(f"Stopping maintenance plan with id {id!r}...")
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Content-Type": "application/json"})
    bp_session.headers.update({"Authorization": f"Bearer {api_key}"})

    try:
        bp_session.post(f"{__base_uri}/maintenance-plans/{id}/stop")
    except requests.RequestException as exc:
        raise BigPandaAPIException("Stopping maintenance plan failed.") from exc
