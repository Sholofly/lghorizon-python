# LG Horizon API Python Library

A Python library to interact with and control LG Horizon set-top boxes (Ziggo, Telenet, Virgin Media, UPC, BASE TV). Provides authentication, real-time device monitoring via MQTT, and remote control capabilities.

## Supported Providers

| Code | Provider | Country |
|------|----------|---------|
| `nl` | Ziggo | Netherlands |
| `be-nl` | Telenet | Belgium |
| `be-basetv` | BASE TV | Belgium |
| `ch` | UPC Switzerland | Switzerland |
| `gb` | Virgin Media | United Kingdom |
| `ie` | Virgin Media | Ireland |
| `pl` | UPC | Poland |

## Features

### Authentication
- Username/password and refresh token authentication
- Automatic access token refreshing
- Token refresh callback for persisting new tokens
- Support for provider-specific auth flows

### Device Management
- Discover all set-top boxes on your account
- Device info: manufacturer, model, platform type
- Real-time availability monitoring (online/standby/offline)

### Real-time Status via MQTT
- Live device state changes via callback
- Playback info: channel, show title, episode, season/episode numbers
- Source types: linear TV, replay, VOD, nDVR, localDVR, review buffer, apps
- Media types: channel, movie, episode, app
- Playback position, duration, speed, paused state
- Channel and program images
- Automatic MQTT reconnection with exponential backoff

### Channel Information
- Full channel list with logos and stream images
- Channel number, radio flag, linear products
- Replay pre/post padding info
- Profile-specific favorite channels

### Recording Management
- List all recordings (single, season, show)
- Recording states: recorded, ongoing
- Episode details for season/show recordings
- Recording quota and usage percentage
- Play recordings on a set-top box

### Device Control
- Power on/off
- Play, pause, stop
- Rewind, fast forward
- Channel up/down and direct channel selection
- Record current program
- Set player position (seek)
- Send any remote control key press
- Display custom messages on the TV screen

## Installation

```bash
pip install lghorizon
```

**Requirements**: Python 3.10+, aiohttp, paho-mqtt, backoff

## Quick Start

Create a `secrets.json` file:

```json
{
  "username": "your_username",
  "password": "your_password",
  "country": "nl",
  "timezone": "Europe/Amsterdam"
}
```

> For providers with refresh token auth (Telenet, UPC CH, Virgin Media GB), use `"refresh_token"` instead of username/password.

### Basic usage

```python
import asyncio
import aiohttp
from lghorizon import LGHorizonApi, LGHorizonAuth

async def main():
    async with aiohttp.ClientSession() as session:
        auth = LGHorizonAuth(session, "nl", username="user", password="pass")
        api = LGHorizonApi(auth, profile_id=None)

        try:
            await api.initialize()
            devices = await api.get_devices()

            # Print all devices
            for device in devices.values():
                print(f"{device.device_friendly_name} ({device.manufacturer} {device.model})")
                print(f"  State: {device.device_state.state.value}")
                print(f"  Available: {device.is_available}")

            # Get channels
            channels = await api.get_profile_channels()
            for ch in channels.values():
                print(f"  {ch.channel_number} - {ch.title}")

            # Monitor state changes
            async def on_state_change(device_id: str):
                device = devices[device_id]
                s = device.device_state
                print(f"{device.device_friendly_name}: {s.channel_name} - {s.show_title}")
                print(f"  Source: {s.source_type.value}, Position: {s.position}/{s.duration}")

            for device in devices.values():
                await device.set_callback(on_state_change)

            # Keep running to receive MQTT updates
            await asyncio.Event().wait()

        finally:
            await api.disconnect()

asyncio.run(main())
```

### Device control

```python
device = devices["device-id"]

# Power
await device.turn_on()
await device.turn_off()

# Playback
await device.play()
await device.pause()
await device.stop()
await device.rewind()
await device.fast_forward()

# Channels
await device.next_channel()
await device.previous_channel()
await device.set_channel("NPO 1")

# Recording
await device.record()
await device.play_recording("recording-id")

# Position (milliseconds)
await device.set_player_position(60000)

# Display message on screen
await device.display_message("linear", "Hello from Python!")
```

### Recordings & quota

```python
if api.has_cloud_recording:
    # Quota
    quota = await api.get_recording_quota()
    print(f"Used: {quota.occupied}/{quota.quota} MB ({quota.percentage_used:.1f}%)")

    # All recordings
    recordings = await api.get_all_recordings()
    for rec in recordings.recordings:
        print(f"[{rec.type.value}] {rec.title} ({rec.recording_state.value})")

    # Episodes of a show recording
    episodes = await api.get_show_recording_episodes("show-recording-id")
    for ep in episodes.recordings:
        print(f"  S{ep.season_number}E{ep.episode_number}: {ep.episode_title}")
```

### Token refresh callback

```python
async def on_token_refresh(new_token: str):
    # Persist the new refresh token for next session
    save_to_storage(new_token)

await api.set_token_refresh_callback(on_token_refresh)
```

## Device State Properties

When monitoring a device, `device.device_state` exposes:

| Property | Type | Description |
|----------|------|-------------|
| `state` | `LGHorizonRunningState` | ONLINE_RUNNING, ONLINE_STANDBY, OFFLINE, etc. |
| `ui_state_type` | `LGHorizonUIStateType` | MAINUI, APPS, UNKNOWN |
| `source_type` | `LGHorizonSourceType` | LINEAR, VOD, NDVR, LOCALDVR, REPLAY, REVIEWBUFFER |
| `media_type` | `LGHorizonMediaType` | CHANNEL, MOVIE, EPISODE, APP |
| `channel_id` | `str \| None` | Current channel ID |
| `channel_name` | `str \| None` | Current channel name |
| `show_title` | `str \| None` | Current show/movie/app title |
| `episode_title` | `str \| None` | Current episode title |
| `season_number` | `int \| None` | Season number |
| `episode_number` | `int \| None` | Episode number |
| `position` | `int \| None` | Playback position in seconds |
| `duration` | `int \| None` | Content duration in seconds |
| `start_time` | `int \| None` | Program start (Unix timestamp) |
| `end_time` | `int \| None` | Program end (Unix timestamp) |
| `speed` | `int \| None` | Playback speed (0 = paused, 1 = normal) |
| `paused` | `bool` | Whether playback is paused |
| `image` | `str \| None` | Content/channel image URL |
| `app_name` | `str \| None` | Active app name (when source is APPS) |

## Error Handling

```python
from lghorizon import (
    LGHorizonApiError,              # Base exception
    LGHorizonApiConnectionError,    # Network/connection issues
    LGHorizonApiUnauthorizedError,  # Invalid credentials
    LGHorizonApiLockedError,        # Account locked
)

try:
    await api.initialize()
except LGHorizonApiLockedError:
    print("Account is locked, try again later")
except LGHorizonApiUnauthorizedError:
    print("Invalid credentials")
except LGHorizonApiConnectionError:
    print("Could not connect to the API")
except LGHorizonApiError as e:
    print(f"API error: {e}")
```

## Development

### Setup

```bash
git clone https://github.com/Sholofly/lghorizon-python.git
cd lghorizon-python
pip install -e .
pip install pytest pytest-asyncio
```

### Running tests

```bash
python -m pytest tests/ -v
```

### Running the demo script

1. Create a `secrets.json` (see Quick Start)
2. Run `python main.py`

The demo script prints all profiles, devices, channels, recordings, and then monitors live state changes with a visual progress bar.

## License

MIT License
