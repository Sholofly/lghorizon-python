"""Main class to test working of LG Horizon API"""

import asyncio
import json
import logging

import aiohttp

from lghorizon import LGHorizonApi
from lghorizon.models import LGHorizonAuth


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
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await api.disconnect()

    def device_callback(self, device_id: str):
        print(f"Device {device_id} state changed.")


asyncio.run(main())
