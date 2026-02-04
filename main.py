"""Main class to test working of LG Horizon API"""

import asyncio
import json
import logging
import sys  # Import sys for stdin
import aiohttp

from datetime import datetime

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_models import LGHorizonAuth

# Define an asyncio Event to signal shutdown
shutdown_event = asyncio.Event()


async def read_input_and_signal_shutdown():
    """Reads a line from stdin and sets the shutdown event."""
    _LOGGER.info("Press Enter to gracefully shut down...")
    # run_in_executor is used to run blocking I/O operations in a separate thread
    # so it doesn't block the asyncio event loop.
    await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    _LOGGER.info("Enter pressed, signaling shutdown.")
    shutdown_event.set()


_LOGGER = logging.getLogger(__name__)


def format_duration(total_seconds):
    # Handle None immediately
    if total_seconds is None:
        return None

    # Store if the value is negative and work with positive numbers for calculation
    is_negative = total_seconds < 0
    total_seconds = abs(int(total_seconds))

    # Efficiently calculate hours, minutes, and seconds
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    # Determine the base format
    if hours > 0:
        result = f"{hours}:{minutes:02}:{seconds:02}"
    elif minutes > 0:
        result = f"{minutes}:{seconds:02}"
    else:
        result = f"{seconds}"

    # Add the minus sign if it was negative
    return f"-{result}" if is_negative else result


def convert_timestamp_to_datetime(timestamp):
    # Handle None to prevent crashes
    if timestamp is None:
        return None

    # Convert seconds to a datetime object
    return datetime.fromtimestamp(timestamp)


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
        country = secrets.get("country", "nl")

    async with aiohttp.ClientSession() as session:
        auth = LGHorizonAuth(session, country, username=username, password=password)
        api = LGHorizonApi(auth)

        # Start the input reader task
        input_task = asyncio.create_task(read_input_and_signal_shutdown())

        async def device_callback(device_id: str):
            device = devices[device_id]
            print(
                f"Device {device.device_id} state changed. Status:\n\nName: {device.device_friendly_name}\nState: {device.device_state.state.value}\nChannel: {device.device_state.channel_name} ({device.device_state.channel_id})\nShow: {device.device_state.show_title}\nEpisode: {device.device_state.episode_title}\nSource type: {device.device_state.source_type.value}\nlast pos update: {convert_timestamp_to_datetime(device.device_state.last_position_update)}\npos: {format_duration(device.device_state.position)}\nduration: {format_duration(device.device_state.duration)}\nstart time: {convert_timestamp_to_datetime(device.device_state.start_time)}\nend time: {convert_timestamp_to_datetime(device.device_state.end_time)}\n\n",
            )

        try:
            await api.initialize()
            devices = await api.get_devices()
            for device in devices.values():
                await device.set_callback(device_callback)

            quota = await api.get_recording_quota()
            print(f"Recording occupancy: {quota.percentage_used}")
            # Wait until the shutdown event is set
            await shutdown_event.wait()

        except Exception as e:
            print(f"An error occurred: {e}")
            _LOGGER.error("An error occurred: %s", e, exc_info=True)
        finally:
            _LOGGER.info("Shutting down API and cancelling input task.")
            input_task.cancel()
            try:
                await input_task  # Await to let it clean up if it was cancelled
            except asyncio.CancelledError:
                pass  # Expected if cancelled
            await api.disconnect()
            _LOGGER.info("Shutdown complete.")


asyncio.run(main())
