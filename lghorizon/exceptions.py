"""Exceptions for the LGHorizon API."""

class LGHorizonApiError(Exception):
    """Generic GeocachingApi exception."""

class LGHorizonApiConnectionError(LGHorizonApiError):
    """Generic GeocachingApi exception."""

class LGHorizonApiUnauthorizedError(Exception):
    """Generic GeocachingApi exception."""
        