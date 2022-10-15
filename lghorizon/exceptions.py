"""Python client for Arrix DCX960."""


class LGHorizonConnectionError(Exception):
    """Exception when no connection could be made."""

    pass


class LGHorizonAuthenticationError(Exception):
    """Exception when authentication fails."""

    pass
