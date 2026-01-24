"""Exceptions for the LGHorizon API."""


class LGHorizonApiError(Exception):
    """Generic LGHorizon exception."""


class LGHorizonApiConnectionError(LGHorizonApiError):
    """Generic LGHorizon exception."""


class LGHorizonApiUnauthorizedError(Exception):
    """Generic LGHorizon exception."""


class LGHorizonApiLockedError(LGHorizonApiUnauthorizedError):
    """Generic LGHorizon exception."""
