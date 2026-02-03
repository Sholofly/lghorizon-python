"""Exceptions for the LGHorizon API."""


class LGHorizonApiError(Exception):
    """Generic LGHorizon exception."""


class LGHorizonApiConnectionError(LGHorizonApiError):
    """Exception for connection-related errors with the LG Horizon API."""


class LGHorizonApiUnauthorizedError(Exception):
    """Exception for unauthorized access to the LG Horizon API."""


class LGHorizonApiLockedError(LGHorizonApiUnauthorizedError):
    """Exception for locked account errors with the LG Horizon API."""
