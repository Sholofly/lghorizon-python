""" "Test the component."""

import json
import logging
import time
from lghorizon import LGHorizonApi

api: LGHorizonApi

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

_Logger = logging.getLogger()

file_handler = logging.FileHandler("logfile.log", mode="w")
file_handler.setLevel(logging.DEBUG)
_Logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
_Logger.addHandler(console_handler)

secrets: dict[str, str] = None


def read_secrets(file_path):
    """Read secrets from file."""
    try:
        with open(file_path, "r", encoding="UTF-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Secrets file not found at {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON in {file_path}")
        return {}


def event_loop():
    """Default event loop."""
    while True:
        time.sleep(1)  # Simulate some work

        # Check for a breaking condition
        if break_condition():
            break


def break_condition():
    """Break event loop on conditions."""
    # Implement your breaking condition logic here
    return False  # Change this condition based on your requirements


if __name__ == "__main__":
    try:
        secrets = read_secrets("secrets.json")

        refresh_token: str = None
        if "refresh_token" in secrets:
            refresh_token = secrets["refresh_token"]

        profile_id: str = None
        if "profile_id" in secrets:
            profile_id = secrets["profile_id"]

        api = LGHorizonApi(
            secrets["username"],
            secrets["password"],
            secrets["country"],
            # identifier="DTV3907048",
            refresh_token=refresh_token,
            profile_id=profile_id,
        )
        api.connect()
        event_loop()
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    finally:
        print("Script is exiting.")
        if api:
            api.disconnect()
