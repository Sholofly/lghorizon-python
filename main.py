"""Main class to test working of LG Horizon API"""

import asyncio
import json

import aiohttp

from lghorizon import LGHorizonApi
from lghorizon.models import LGHorizonAuth


async def main():
    """main loop"""
    with open("secrets.json", encoding="utf-8") as f:
        secrets = json.load(f)
        username = secrets.get("username")
        password = secrets.get("password")
        country = secrets.get("country", "nl")

    async with aiohttp.ClientSession() as session:
        auth = LGHorizonAuth(session, country, username=username, password=password)
        api = LGHorizonApi(auth)
        await api.initialize()

        try:
            print("Listening to MQTT broker... Press Ctrl+C to exit")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            await api.disconnect()


asyncio.run(main())
