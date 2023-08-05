"""bigpandaapi's exception definitions.

This module contains the set of bigpandaapi's exceptions.
"""

from requests import RequestException


class BigPandaAPIException(RequestException):
    """There was an exception thrown by the BigPanda API."""
    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Initialize."""
        self.detail = kwargs.pop("detail", None)
        super().__init__(*args, **kwargs)
