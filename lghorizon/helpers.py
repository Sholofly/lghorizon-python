"""Helper functions."""
import random


def make_id(stringLength=10):
    """Create an id with given length."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(letters) for i in range(stringLength))
