# LG Horizon API Python Library

A Python library to interact with and control LG Horizon set-top boxes. This library provides functionalities for authentication, real-time device status monitoring via MQTT, and various control commands for your Horizon devices.

## Features

- **Authentication**: Supports authentication using username/password or a refresh token. The library automatically handles access token refreshing.
- **Device Management**: Discover and manage multiple LG Horizon set-top boxes associated with your account.
- **Real-time Status**: Monitor device status (online/running/standby) and current playback information (channel, show, VOD, recording, app) through MQTT.
- **Channel Information**: Retrieve a list of available channels and profile-specific favorite channels.
- **Recording Management**:
  - Get a list of all recordings.
  - Retrieve recordings for specific shows.
  - Check recording quota and usage.
- **Device Control**: Send various commands to your set-top box:
  - Power on/off.
  - Play, pause, stop, rewind, fast forward.
  - Change channels (up/down, direct channel selection).
  - Record current program.
  - Set player position for VOD/recordings.
  - Display custom messages on the TV screen.
  - Send emulated remote control key presses.
- **Robustness**: Includes automatic MQTT reconnection with exponential backoff and token refresh logic to maintain a stable connection.

## Installation

```bash
pip install lghorizon-python # (Replace with actual package name if different)
```

## Usage

Here's a basic example of how to use the library to connect to your LG Horizon devices and monitor their state:

First, create a `secrets.json` file in the root of your project with your LG Horizon credentials:

```json
{
  "username": "your_username",
  "password": "your_password",
  "country": "nl" // e.g., "nl" for Netherlands, "be" for Belgium
}
```

Then, you can use the library as follows:

```python
import asyncio
import json
import logging
import aiohttp

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_models import LGHorizonAuth

_LOGGER = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.INFO) # Set to DEBUG for more verbose output

    with open("secrets.json", encoding="utf-8") as f:
        secrets = json.load(f)
        username = secrets.get("username")
        password = secrets.get("password")
        country = secrets.get("country", "nl")

    async with aiohttp.ClientSession() as session:
        auth = LGHorizonAuth(session, country, username=username, password=password)
        api = LGHorizonApi(auth)

        async def device_state_changed_callback(device_id: str):
            device = devices[device_id]
            _LOGGER.info(
                f"Device {device.device_friendly_name} ({device.device_id}) state changed:\n"
                f"  State: {device.device_state.state.value}\n"
                f"  UI State: {device.device_state.ui_state_type.value}\n"
                f"  Source Type: {device.device_state.source_type.value}\n"
                f"  Channel: {device.device_state.channel_name or 'N/A'} ({device.device_state.channel_id or 'N/A'})\n"
                f"  Show: {device.device_state.show_title or 'N/A'}\n"
                f"  Episode: {device.device_state.episode_title or 'N/A'}\n"
                f"  Position: {device.device_state.position or 'N/A'} / {device.device_state.duration or 'N/A'}\n"
            )

        try:
            _LOGGER.info("Initializing LG Horizon API...")
            await api.initialize()
            devices = await api.get_devices()

            for device in devices.values():
                _LOGGER.info(f"Registering callback for device: {device.device_friendly_name}")
                await device.set_callback(device_state_changed_callback)

            _LOGGER.info("API initialized. Monitoring device states. Press Ctrl+C to exit.")
            # Keep the script running to receive MQTT updates
            while True:
                await asyncio.sleep(3600) # Sleep for a long time, MQTT callbacks will still fire

        except Exception as e:
            _LOGGER.error(f"An error occurred: {e}", exc_info=True)
        finally:
            _LOGGER.info("Disconnecting from LG Horizon API.")
            await api.disconnect()
            _LOGGER.info("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Authentication

The `LGHorizonAuth` class handles authentication. You can initialize it with a username and password, or directly with a refresh token if you have one. The library automatically refreshes access tokens as needed.

```python
# Using username and password
auth = LGHorizonAuth(session, "nl", username="your_username", password="your_password")

# Using a refresh token (e.g., if you've saved it from a previous session)
# auth = LGHorizonAuth(session, "nl", refresh_token="your_refresh_token")
```

You can also set a callback to receive the updated refresh token when it's refreshed, allowing you to persist it for future sessions:

```python
def token_updated_callback(new_refresh_token: str):
    print(f"New refresh token received: {new_refresh_token}")
    # Here you would typically save this new_refresh_token
    # to your secrets.json or other persistent storage.

# After initializing LGHorizonApi:
# api.set_token_refresh_callback(token_updated_callback)
```

## Error Handling

The library defines custom exceptions for common error scenarios:

- `LGHorizonApiError`: Base exception for all API-related errors.
- `LGHorizonApiConnectionError`: Raised for network or connection issues.
- `LGHorizonApiUnauthorizedError`: Raised when authentication fails (e.g., invalid credentials).
- `LGHorizonApiLockedError`: A specific type of `LGHorizonApiUnauthorizedError` indicating a locked account.

These exceptions allow for more granular error handling in your application.

## Development

To run the example script (`main.py`) from the repository:

1.  Clone this repository.
2.  Install dependencies: `pip install -r requirements.txt` (ensure `requirements.txt` is up-to-date).
3.  Create a `secrets.json` file as described in the Usage section.
4.  Run `python main.py`.
