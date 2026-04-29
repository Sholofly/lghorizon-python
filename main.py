"""Main class to test working of LG Horizon API"""

import asyncio
import json
import logging
import sys
import aiohttp

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_models import (
    LGHorizonAuth,
    LGHorizonRecordingType,
)

# Define an asyncio Event to signal shutdown
shutdown_event = asyncio.Event()

# Default timezone, overridden by secrets.json "timezone" field
LOCAL_TZ = ZoneInfo("Europe/Amsterdam")


async def read_input_async() -> str:
    """Read a line from stdin asynchronously."""
    return await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)


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

        # EPG cache for now/next in state callbacks
        epg_cache = {"epg": None}

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

            # Ad break info
            if s.ad_breaks:
                print(f"  {SEPARATOR}")
                print(f"  🚫 Ad Breaks:   {len(s.ad_breaks)} detected")
                for i, ab in enumerate(s.ad_breaks, 1):
                    marker = " ◀ NOW" if (s.position and ab.start_ms <= s.position * 1000 < ab.end_ms) else ""
                    print(f"    {i}. {format_duration(ab.start_ms // 1000)} - {format_duration(ab.end_ms // 1000)} ({format_duration(ab.duration_ms // 1000)}){marker}")
                ad_break = device.get_current_ad_break()
                if ad_break:
                    print(f"  >>> IN AD BREAK - ends at {format_duration(int(ad_break.end_s))}")

            # EPG now/next (simulates HA media_player extra_state_attributes)
            epg = epg_cache.get("epg")
            if epg and s.channel_id:
                import time as _time
                now_ts = _time.time()
                events = epg.get_channel_events(s.channel_id)
                current = None
                next_up = None
                for i, ev in enumerate(events):
                    if ev.start_time and ev.end_time and ev.start_time <= now_ts < ev.end_time:
                        current = ev
                        if i + 1 < len(events):
                            next_up = events[i + 1]
                        break
                if current:
                    print(f"  {SEPARATOR}")
                    print(f"  📺 EPG Now:     {current.title}")
                    if current.start_time and current.end_time:
                        dur = current.end_time - current.start_time
                        if dur > 0:
                            elapsed = now_ts - current.start_time
                            prog = min(elapsed / dur * 100, 100)
                            print(f"     Time:        {format_timestamp(current.start_time)} - {format_timestamp(current.end_time)}  ({prog:.0f}%)")
                    if next_up:
                        print(f"  📺 EPG Next:    {next_up.title} ({format_timestamp(next_up.start_time)})")

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

            # ── Replay Channels ──
            print_header("REPLAY CHANNELS")
            replay_channels = await api.get_replay_channels()
            print(f"  {len(replay_channels)} channels with replay/catch-up support")
            for rc in replay_channels[:10]:
                print(f"    {rc.name} ({rc.id})")
            if len(replay_channels) > 10:
                print(f"    ... and {len(replay_channels) - 10} more")

            # ── EPG (Today) ──
            import time as _time
            from datetime import date as date_type
            print_header("EPG (Today)")
            epg = await api.get_epg()
            epg_cache["epg"] = epg  # Store for state change callbacks
            print(f"  {len(epg.entries)} channels with EPG data")
            now_ts = int(_time.time())
            shown = 0
            for entry in epg.entries:
                if shown >= 5:
                    break
                current = None
                next_up = None
                for ev in entry.events:
                    if ev.start_time and ev.end_time:
                        if ev.start_time <= now_ts < ev.end_time:
                            current = ev
                        elif ev.start_time > now_ts and next_up is None:
                            next_up = ev
                if current:
                    ch_name = entry.channel_id
                    print(f"  {ch_name}:")
                    print(f"    Now:  {current.title}")
                    if next_up:
                        print(f"    Next: {next_up.title}")
                    shown += 1

            # ── Recordings ──
            if api.has_cloud_recording:
                quota = await api.get_recording_quota()
                print_header("RECORDING QUOTA")
                used_gb = quota.occupied / 1024
                total_gb = quota.quota / 1024
                free_gb = total_gb - used_gb
                pct = quota.percentage_used
                bar_len = 30
                filled = int(bar_len * pct / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"  [{bar}] {pct:.1f}%")
                print(f"  Used: {used_gb:.1f} GB / {total_gb:.1f} GB  —  Free: {free_gb:.1f} GB")

                # ── Managed Recordings ──
                print_header("MANAGED RECORDINGS (extended)")
                managed = await api.get_managed_recordings(limit=10)
                print(f"  Total: {managed.total} recordings ({managed.total_disk_space:.1f} hours disk space)")
                for rec in managed.recordings[:5]:
                    state_icon = {"recorded": "✅", "planned": "📅", "partiallyRecorded": "⚠️"}.get(rec.recording_state, "❓")
                    ep_info = ""
                    if rec.season_number is not None:
                        ep_info = f" S{rec.season_number}E{rec.episode_number}"
                    delete_info = f" (expires: {rec.delete_time[:10]})" if rec.delete_time else ""
                    print(f"  {state_icon} {rec.title}{ep_info} [{rec.recording_state}]{delete_info}")

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
            print("  Listening for device state changes...\n")

            for device in devices.values():
                await device.set_callback(device_callback)

            # Build device list for interactive commands
            device_list = list(devices.values())

            def print_help():
                print(f"\n{'─' * 60}")
                print("  Available commands:")
                print("  ─────────────────────────────────────────")
                print("  boxes                       - List all boxes")
                print("  msg <nr> <bericht>          - Send message to box")
                print("  channel <nr> <kanaal>       - Switch channel on box")
                print("  key <nr> <key>              - Send key press to box")
                print("  on <nr>                     - Turn box on")
                print("  off <nr>                    - Turn box off")
                print("  pause <nr>                  - Pause playback")
                print("  play <nr>                   - Resume playback")
                print("  stop <nr>                   - Stop playback")
                print("  skip <nr>                   - Skip ad break")
                print("  help                        - Show this help")
                print("  quit / exit                 - Shut down")
                print(f"{'─' * 60}\n")

            def print_boxes():
                print()
                for i, dev in enumerate(device_list):
                    status = dev.device_state.state.value
                    print(f"  [{i}] {dev.device_friendly_name} ({status})")
                print()

            print_help()

            # Interactive command loop
            while not shutdown_event.is_set():
                try:
                    line = await read_input_async()
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(maxsplit=2)
                    cmd = parts[0].lower()

                    if cmd in ("quit", "exit", "q"):
                        print("Shutting down...")
                        shutdown_event.set()
                        break

                    elif cmd == "help":
                        print_help()

                    elif cmd == "boxes":
                        print_boxes()

                    elif cmd == "msg":
                        if len(parts) < 3:
                            print("  Usage: msg <box_nr> <bericht>")
                            continue
                        try:
                            idx = int(parts[1])
                            message = parts[2]
                            dev = device_list[idx]
                            print(f"  Sending message to {dev.device_friendly_name}: {message}")
                            await dev.display_message("linear", message)
                            print("  ✓ Message sent!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number. Use 'boxes' to see available boxes (0-{len(device_list)-1}).")

                    elif cmd == "channel":
                        if len(parts) < 3:
                            print("  Usage: channel <box_nr> <channel_name>")
                            continue
                        try:
                            idx = int(parts[1])
                            channel_name = parts[2]
                            dev = device_list[idx]
                            print(f"  Switching {dev.device_friendly_name} to {channel_name}...")
                            await dev.set_channel(channel_name)
                            print("  ✓ Channel switched!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number. Use 'boxes' to see available boxes (0-{len(device_list)-1}).")
                        except Exception as e:
                            print(f"  Error: {e}")

                    elif cmd == "key":
                        if len(parts) < 3:
                            print("  Usage: key <box_nr> <key_name>")
                            continue
                        try:
                            idx = int(parts[1])
                            key_name = parts[2]
                            dev = device_list[idx]
                            print(f"  Sending key '{key_name}' to {dev.device_friendly_name}...")
                            await dev.send_key_to_box(key_name)
                            print("  ✓ Key sent!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number. Use 'boxes' to see available boxes (0-{len(device_list)-1}).")

                    elif cmd == "on":
                        if len(parts) < 2:
                            print("  Usage: on <box_nr>")
                            continue
                        try:
                            idx = int(parts[1])
                            dev = device_list[idx]
                            await dev.turn_on()
                            print(f"  ✓ {dev.device_friendly_name} turning on!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number.")

                    elif cmd == "off":
                        if len(parts) < 2:
                            print("  Usage: off <box_nr>")
                            continue
                        try:
                            idx = int(parts[1])
                            dev = device_list[idx]
                            await dev.turn_off()
                            print(f"  ✓ {dev.device_friendly_name} turning off!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number.")

                    elif cmd == "pause":
                        if len(parts) < 2:
                            print("  Usage: pause <box_nr>")
                            continue
                        try:
                            idx = int(parts[1])
                            dev = device_list[idx]
                            await dev.pause()
                            print(f"  ✓ Paused!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number.")

                    elif cmd == "play":
                        if len(parts) < 2:
                            print("  Usage: play <box_nr>")
                            continue
                        try:
                            idx = int(parts[1])
                            dev = device_list[idx]
                            await dev.play()
                            print(f"  ✓ Playing!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number.")

                    elif cmd == "stop":
                        if len(parts) < 2:
                            print("  Usage: stop <box_nr>")
                            continue
                        try:
                            idx = int(parts[1])
                            dev = device_list[idx]
                            await dev.stop()
                            print(f"  ✓ Stopped!")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number.")

                    elif cmd == "skip":
                        if len(parts) < 2:
                            print("  Usage: skip <box_nr>")
                            continue
                        try:
                            idx = int(parts[1])
                            dev = device_list[idx]
                            skipped = await dev.skip_ad_break()
                            if skipped:
                                print(f"  ✓ Ad break skipped!")
                            else:
                                print(f"  No ad break to skip.")
                        except (ValueError, IndexError):
                            print(f"  Invalid box number.")

                    else:
                        print(f"  Unknown command: {cmd}. Type 'help' for available commands.")

                except Exception as cmd_err:
                    print(f"  Command error: {cmd_err}")

        except KeyboardInterrupt:
            print("\nInterrupted, shutting down...")
        except Exception as e:
            print(f"\nError: {e}")
            _LOGGER.error("An error occurred: %s", e, exc_info=True)
        finally:
            _LOGGER.info("Shutting down API.")
            await api.disconnect()
            print("Shutdown complete.")
            _LOGGER.info("Shutdown complete.")


asyncio.run(main())
