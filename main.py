"""Main class to test working of LG Horizon API"""

import asyncio
import json
import logging
import sys
import aiohttp

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_models import LGHorizonAuth, LGHorizonRecordingType

# Define an asyncio Event to signal shutdown
shutdown_event = asyncio.Event()

# Default timezone, overridden by secrets.json "timezone" field
LOCAL_TZ = ZoneInfo("Europe/Amsterdam")


async def read_input_and_signal_shutdown():
    """Reads a line from stdin and sets the shutdown event."""
    print("Press Enter to gracefully shut down...")
    await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    print("Enter pressed, shutting down...")
    shutdown_event.set()


_LOGGER = logging.getLogger(__name__)

SEPARATOR = "─" * 60


def format_duration(total_seconds):
    """Format seconds into a human-readable duration string."""
    if total_seconds is None:
        return "—"

    is_negative = total_seconds < 0
    total_seconds = abs(int(total_seconds))

    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        result = f"{hours}:{minutes:02}:{seconds:02}"
    elif minutes > 0:
        result = f"{minutes}:{seconds:02}"
    else:
        result = f"0:{seconds:02}"

    return f"-{result}" if is_negative else result


def format_timestamp(timestamp):
    """Convert a Unix timestamp to a readable datetime string in local timezone."""
    if timestamp is None:
        return "—"
    return datetime.fromtimestamp(timestamp, tz=LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")


def val(value, default="—"):
    """Return value or a default placeholder for None."""
    return value if value is not None else default


def print_header(title):
    """Print a section header."""
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


async def main():
    """Main function to run the LG Horizon API test script."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="lghorizon.log",
        filemode="w",
    )

    logging.info("Starting LG Horizon test script")
    with open("secrets.json", encoding="utf-8") as f:
        secrets = json.load(f)
        username = secrets.get("username")
        password = secrets.get("password")
        refresh_token = secrets.get("refresh_token")
        country = secrets.get("country", "nl")

    global LOCAL_TZ
    tz_name = secrets.get("timezone", "Europe/Amsterdam")
    LOCAL_TZ = ZoneInfo(tz_name)
    print(f"Using timezone: {tz_name}")

    async with aiohttp.ClientSession() as session:
        auth = LGHorizonAuth(
            session,
            country,
            username=username,
            password=password,
            refresh_token=refresh_token,
        )
        api = LGHorizonApi(auth, profile_id=None)

        # Start the input reader task
        input_task = asyncio.create_task(read_input_and_signal_shutdown())

        async def device_callback(device_id: str):
            device = devices[device_id]
            s = device.device_state

            print(f"\n{SEPARATOR}")
            print(f"  📡 STATE CHANGE: {device.device_friendly_name} ({device.device_id})")
            print(SEPARATOR)

            # Device info
            print(f"  State:          {s.state.value}")
            print(f"  UI State:       {s.ui_state_type.value}")
            print(f"  Media Type:     {s.media_type.value}")
            print(f"  Source Type:    {s.source_type.value}")

            # Content info
            print(f"  {SEPARATOR}")
            print(f"  Channel:        {val(s.channel_name)} ({val(s.channel_id)})")
            print(f"  Show:           {val(s.show_title)}")
            print(f"  Episode:        {val(s.episode_title)}")
            if s.season_number is not None or s.episode_number is not None:
                print(f"  Season/Episode: S{val(s.season_number, '?')}E{val(s.episode_number, '?')}")
            print(f"  App:            {val(s.app_name)}")
            print(f"  Image:          {val(s.image)}")

            # Playback info
            print(f"  {SEPARATOR}")
            print(f"  Speed:          {val(s.speed)}")
            print(f"  Paused:         {s.paused}")
            print(f"  Position:       {format_duration(s.position)}")
            print(f"  Duration:       {format_duration(s.duration)}")
            print(f"  Start Time:     {format_timestamp(s.start_time)}")
            print(f"  End Time:       {format_timestamp(s.end_time)}")
            print(f"  Last Update:    {format_timestamp(s.last_position_update)}")

            # Progress bar
            if s.duration and s.position and s.duration > 0:
                pct = min(s.position / s.duration, 1.0)
                bar_len = 40
                filled = int(bar_len * pct)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"  Progress:       [{bar}] {pct:.0%}")

            print()

        try:
            print("Connecting to LG Horizon API...")
            await api.initialize()

            # ── Profiles ──
            profiles = await api.get_profiles()
            print_header("PROFILES")
            for profile in profiles.values():
                fav_count = len(profile.favorite_channels)
                print(f"  • {profile.name} (id: {profile.id}, lang: {profile.options.lang}, favorites: {fav_count})")

            # ── Devices ──
            devices = await api.get_devices()
            print_header("DEVICES")
            for device in devices.values():
                print(f"  • {device.device_friendly_name}")
                print(f"    ID:           {device.device_id}")
                print(f"    Platform:     {device.platform_type}")
                print(f"    Manufacturer: {device.manufacturer}")
                print(f"    Model:        {device.model}")
                print(f"    Available:    {device.is_available}")
                print(f"    State:        {device.device_state.state.value}")
                print()

            # ── Channels ──
            channels = await api.get_profile_channels()
            print_header(f"CHANNELS ({len(channels)} total)")
            for ch in sorted(channels.values(), key=lambda c: int(c.channel_number) if str(c.channel_number).isdigit() else 9999):
                radio_tag = " [Radio]" if ch.is_radio else ""
                print(f"  {ch.channel_number:>4}  {ch.title}{radio_tag}")

            # ── Recordings ──
            if api.has_cloud_recording:
                quota = await api.get_recording_quota()
                print_header("RECORDING QUOTA")
                print(f"  Used:       {quota.occupied} MB / {quota.quota} MB ({quota.percentage_used:.1f}%)")

                recordings = await api.get_all_recordings()
                print_header(f"RECORDINGS ({recordings.total} total)")
                for rec in recordings.recordings:
                    type_label = rec.type.value.upper()
                    state_label = rec.recording_state.value
                    poster = f"  Poster: {rec.poster_url}" if rec.poster_url else ""

                    if rec.type == LGHorizonRecordingType.SINGLE:
                        ep_info = ""
                        if rec.season_number is not None:
                            ep_info = f" S{rec.season_number}E{rec.episode_number}"
                        print(f"  • [{type_label}] {rec.title}{ep_info} ({state_label}){poster}")
                    elif rec.type in (LGHorizonRecordingType.SEASON, LGHorizonRecordingType.SHOW):
                        print(f"  • [{type_label}] {rec.title} ({rec.no_of_episodes} episodes, {state_label}){poster}")
                    else:
                        print(f"  • [{type_label}] {rec.title} ({state_label})")
            else:
                print_header("RECORDINGS")
                print("  Cloud recording not available for this account.")

            # ── Live monitoring ──
            print_header("LIVE MONITORING")
            print("  Listening for device state changes...")
            print("  Press Enter to stop.\n")

            for device in devices.values():
                await device.set_callback(device_callback)

            # Wait until the shutdown event is set
            await shutdown_event.wait()

        except Exception as e:
            print(f"\nError: {e}")
            _LOGGER.error("An error occurred: %s", e, exc_info=True)
        finally:
            _LOGGER.info("Shutting down API and cancelling input task.")
            input_task.cancel()
            try:
                await input_task
            except asyncio.CancelledError:
                pass
            await api.disconnect()
            print("Shutdown complete.")
            _LOGGER.info("Shutdown complete.")


asyncio.run(main())
