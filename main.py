"""Main class to test working of LG Horizon API"""

import asyncio
import json
import logging

import aiohttp

from lghorizon import LGHorizonApi
from lghorizon.models import LGHorizonAuth

_LOGGER = logging.getLogger(__name__)


async def main():
    """main loop"""
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

        try:
            await api.initialize()
            devices = await api.get_devices()

            async def device_callback(device_id: str):
                device = devices[device_id]
                print(
                    f"Device {device.device_id} state changed. Status:\n\nName: {device.device_friendly_name}\nState: {device.device_state.state.value}\nChannel: {device.device_state.channel_title}\nTitle: {device.device_state.title}\n\n",
                )

            for device in devices.values():
                await device.set_callback(device_callback)
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await api.disconnect()


asyncio.run(main())
