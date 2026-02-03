"""Helper functions."""

import random


async def make_id(string_length=10):
    """Create an id with given length."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(letters) for i in range(string_length))
