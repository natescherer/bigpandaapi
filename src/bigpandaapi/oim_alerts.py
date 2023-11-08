"""Functions for BigPanda Open Integration Manager (OIM) alerts.

This implements functions that abstract the OIM alert features of BigPanda's API.

Typical usage example:

  properties = {
    "host": "HostName",
    "check": "CheckName",
    "description": "This is a description."
  }
  bigpandaapi.oim_send_alert(app_key=app_key,
                              org_token=org_token,
                              properties=properties)
"""

from __future__ import annotations  # TypedDict NotRequired Support for <3.10

import json
from typing import Mapping

import requests
from dateutil import parser
from typing_extensions import NotRequired  # TypedDict NotRequired Support for <3.11
from typing_extensions import TypedDict  # TypedDict NotRequired Support for <3.11

from .exceptions import BigPandaAPIException


__base_uri: str = "https://integrations.bigpanda.io/oim/api"


def oim_send_alert(
    app_key: str,
    org_token: str,
    properties: Mapping[str, str],
    status: str = "warning",
    timestamp: str | None = None,
) -> None:
    """Sends an alert to a BigPanda OIM Integration.

    Sends an alert to a BigPanda Open Integration Manager (OIM) integration.

    Args:
        app_key: The App Key for the OIM integration to which you'd like to send the
            alert.
        org_token: The token for the BigPanda org that the OIM integration is a part
            of. This is also referred to as the Auth Token in the BigPanda UI.
        properties: A dict of values that will be sent in the body of the alert. Each
            key-value pair will be parsed as a tag on the alert in BigPanda.
        status: One of "ok", "critical", "warning", or "acknowledged".
        timestamp: An optional string containing a datetime for the alert. If excluded,
            BigPanda will use the datetime when it receives the alert payload. ISO 8601
            format is recommended, and UTC will be assumed as the timezone if not
            specified.

    Raises:
        ValueError: An incorrect argument was provided.
        BigPandaAPIException: Something went wrong when connecting to the BigPanda API.
    """
    valid_statuses = {"ok", "critical", "warning", "acknowledged"}
    if status not in valid_statuses:
        raise ValueError("Status must be one of %r." % valid_statuses)

    class AlertBody(TypedDict):
        app_key: str
        status: str
        timestamp: NotRequired[float]

    main_body: AlertBody = {
        "app_key": app_key,
        "status": status,
    }
    combined_body = {**main_body, **properties}
    if timestamp:
        timestamp_datetime = parser.parse(timestamp)
        combined_body["timestamp"] = timestamp_datetime.timestamp()

    print("Sending OIM alert...")
    bp_session = requests.Session()
    bp_session.hooks = {"response": lambda r, *args, **kwargs: r.raise_for_status()}
    bp_session.headers.update({"Content-Type": "application/json"})
    bp_session.headers.update({"Authorization": f"Bearer {org_token}"})

    try:
        bp_session.post(f"{__base_uri}/alerts", data=json.dumps(combined_body))
    except requests.RequestException as exc:
        raise BigPandaAPIException("Sending alert failed.") from exc
    print("Done!")
