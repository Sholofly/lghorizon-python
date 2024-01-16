import json
import logging
import time
from lghorizon import LGHorizonApi, LGHorizonBox

api: LGHorizonApi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

_Logger = logging.getLogger()

file_handler = logging.FileHandler("logfile.log", mode="w")
file_handler.setLevel(logging.DEBUG)
_Logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
_Logger.addHandler(console_handler)


def read_secrets(file_path):
    try:
        with open(file_path, "r") as file:
            secrets = json.load(file)
        return secrets
    except FileNotFoundError:
        print(f"Error: Secrets file not found at {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON in {file_path}")
        return {}


def event_loop():
    while True:
        time.sleep(1)  # Simulate some work
        box: LGHorizonBox
        for box in api.settop_boxes.values():
            if not box.playing_info:
                continue
            _Logger.info(box.playing_info.image)
        # Check for a breaking condition
        if break_condition():
            break


def break_condition():
    # Implement your breaking condition logic here
    return False  # Change this condition based on your requirements


if __name__ == "__main__":
    try:
        secrets_file_path = "secrets.json"
        secrets = read_secrets(secrets_file_path)
        api = LGHorizonApi(secrets["username"], secrets["password"], secrets["country"])
        api.connect()
        event_loop()
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    finally:
        print("Script is exiting.")
        if api:
            api.disconnect()
