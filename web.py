"""Web-based test UI for the LG Horizon Python library.

Run with:  python web.py
Then open: http://localhost:8080
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import aiohttp
from aiohttp import web

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_models import LGHorizonAuth
from lghorizon.const import COUNTRY_SETTINGS, MEDIA_KEYS

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="lghorizon_web.log",
    filemode="w",
)
_LOGGER = logging.getLogger(__name__)

try:
    LOCAL_TZ = ZoneInfo("Europe/Amsterdam")
except Exception:
    # tzdata package not installed; fall back to UTC
    from datetime import timezone
    LOCAL_TZ = timezone.utc

# ── Application state ────────────────────────────────────────

app_state: dict = {
    "session": None,       # aiohttp.ClientSession
    "auth": None,          # LGHorizonAuth
    "api": None,           # LGHorizonApi
    "devices": {},         # dict[str, LGHorizonDevice]
    "channels": {},        # dict[str, LGHorizonChannel]
    "ws_clients": set(),   # set of WebSocketResponse
    "connected": False,
}


# ── Helpers ──────────────────────────────────────────────────

def device_state_to_dict(device) -> dict:
    """Serialize a device and its state to a JSON-friendly dict."""
    s = device.device_state
    result = {
        "device_id": device.device_id,
        "name": device.device_friendly_name,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "platform_type": device.platform_type,
        "is_available": device.is_available,
        "state": s.state.value,
        "ui_state": s.ui_state_type.value,
        "media_type": s.media_type.value,
        "source_type": s.source_type.value,
        "channel_id": s.channel_id,
        "channel_name": s.channel_name,
        "show_title": s.show_title,
        "episode_title": s.episode_title,
        "season_number": s.season_number,
        "episode_number": s.episode_number,
        "app_name": s.app_name,
        "image": s.image,
        "speed": s.speed,
        "paused": s.paused,
        "position": s.position,
        "duration": s.duration,
        "start_time": s.start_time,
        "end_time": s.end_time,
    }
    return result


async def broadcast_state(device_id: str):
    """Push device state to all connected WebSocket clients."""
    device = app_state["devices"].get(device_id)
    if device is None:
        return
    msg = json.dumps({
        "type": "state_change",
        "device": device_state_to_dict(device),
    })
    dead = set()
    for ws in app_state["ws_clients"]:
        try:
            await ws.send_str(msg)
        except Exception:
            dead.add(ws)
    app_state["ws_clients"] -= dead


# ── Routes ───────────────────────────────────────────────────

routes = web.RouteTableDef()


@routes.get("/")
async def index(request: web.Request):
    """Serve the single-page UI."""
    html_path = Path(__file__).parent / "web_ui.html"
    return web.FileResponse(html_path)


@routes.get("/api/status")
async def get_status(request: web.Request):
    """Return current connection status. Used by frontend after page reload."""
    if not app_state["connected"]:
        return web.json_response({"connected": False})

    device_list = [device_state_to_dict(d) for d in app_state["devices"].values()]
    channel_list = [
        {"id": ch.id, "title": ch.title, "number": ch.channel_number, "is_radio": ch.is_radio}
        for ch in sorted(app_state["channels"].values(), key=lambda c: int(c.channel_number) if str(c.channel_number).isdigit() else 9999)
    ]
    return web.json_response({
        "connected": True,
        "devices": device_list,
        "channels": channel_list,
    })


@routes.get("/api/countries")
async def get_countries(request: web.Request):
    """Return supported countries with their auth method."""
    countries = []
    for code, settings in COUNTRY_SETTINGS.items():
        countries.append({
            "code": code,
            "name": settings["name"],
            "use_refreshtoken": settings["use_refreshtoken"],
        })
    return web.json_response({"countries": countries})


@routes.get("/api/keys")
async def get_keys(request: web.Request):
    """Return all available media keys grouped by category."""
    return web.json_response({"keys": MEDIA_KEYS})


@routes.post("/api/login")
async def login(request: web.Request):
    """Authenticate and initialize the API connection."""
    if app_state["connected"]:
        return web.json_response({"error": "Already connected. Logout first."}, status=400)

    data = await request.json()
    country = data.get("country", "")
    username = data.get("username", "")
    password = data.get("password", "")
    refresh_token = data.get("refresh_token", "")

    if country not in COUNTRY_SETTINGS:
        return web.json_response({"error": f"Unknown country: {country}"}, status=400)

    settings = COUNTRY_SETTINGS[country]
    if settings["use_refreshtoken"] and not refresh_token:
        return web.json_response({"error": "Refresh token is required for this provider."}, status=400)
    if not settings["use_refreshtoken"] and (not username or not password):
        return web.json_response({"error": "Username and password are required for this provider."}, status=400)

    try:
        session = aiohttp.ClientSession()
        auth = LGHorizonAuth(
            session,
            country,
            username=username,
            password=password,
            refresh_token=refresh_token,
        )
        api = LGHorizonApi(auth, profile_id=None)

        _LOGGER.info("Initializing API for country=%s", country)
        await api.initialize()

        devices = await api.get_devices()
        channels = await api.get_profile_channels()

        # Store in app state
        app_state["session"] = session
        app_state["auth"] = auth
        app_state["api"] = api
        app_state["devices"] = devices
        app_state["channels"] = channels
        app_state["connected"] = True

        # Set callbacks for live state updates
        for device in devices.values():
            await device.set_callback(broadcast_state)

        # Build response
        device_list = [device_state_to_dict(d) for d in devices.values()]
        channel_list = [
            {"id": ch.id, "title": ch.title, "number": ch.channel_number, "is_radio": ch.is_radio}
            for ch in sorted(channels.values(), key=lambda c: int(c.channel_number) if str(c.channel_number).isdigit() else 9999)
        ]

        _LOGGER.info("Login successful. %d devices, %d channels", len(device_list), len(channel_list))
        return web.json_response({
            "success": True,
            "devices": device_list,
            "channels": channel_list,
            "keys": MEDIA_KEYS,
        })

    except Exception as e:
        _LOGGER.error("Login failed: %s", e, exc_info=True)
        # Clean up on failure
        if app_state["session"]:
            await app_state["session"].close()
            app_state["session"] = None
        app_state["connected"] = False
        return web.json_response({"error": str(e)}, status=500)


@routes.post("/api/logout")
async def logout(request: web.Request):
    """Disconnect and clean up."""
    if not app_state["connected"]:
        return web.json_response({"error": "Not connected."}, status=400)

    try:
        api = app_state["api"]
        if api:
            await api.disconnect()
        session = app_state["session"]
        if session:
            await session.close()
    except Exception as e:
        _LOGGER.error("Error during logout: %s", e)
    finally:
        app_state["session"] = None
        app_state["auth"] = None
        app_state["api"] = None
        app_state["devices"] = {}
        app_state["channels"] = {}
        app_state["connected"] = False

        # Notify WebSocket clients
        for ws in app_state["ws_clients"]:
            try:
                await ws.send_str(json.dumps({"type": "disconnected"}))
            except Exception:
                pass
        app_state["ws_clients"].clear()

    return web.json_response({"success": True})


@routes.get("/api/devices")
async def get_devices(request: web.Request):
    """Return current device states."""
    if not app_state["connected"]:
        return web.json_response({"error": "Not connected."}, status=401)

    device_list = [device_state_to_dict(d) for d in app_state["devices"].values()]
    return web.json_response({"devices": device_list})


@routes.get("/api/channels")
async def get_channels(request: web.Request):
    """Return the channel list."""
    if not app_state["connected"]:
        return web.json_response({"error": "Not connected."}, status=401)

    channel_list = [
        {"id": ch.id, "title": ch.title, "number": ch.channel_number, "is_radio": ch.is_radio}
        for ch in sorted(app_state["channels"].values(), key=lambda c: int(c.channel_number) if str(c.channel_number).isdigit() else 9999)
    ]
    return web.json_response({"channels": channel_list})


@routes.post("/api/command")
async def handle_command(request: web.Request):
    """Execute a command on a device."""
    if not app_state["connected"]:
        return web.json_response({"error": "Not connected."}, status=401)

    data = await request.json()
    device_id = data.get("device_id")
    command = data.get("command")

    device = app_state["devices"].get(device_id)
    if device is None:
        return web.json_response({"error": f"Unknown device: {device_id}"}, status=404)

    try:
        if command == "turn_on":
            await device.turn_on()
        elif command == "turn_off":
            await device.turn_off()
        elif command == "pause":
            await device.pause()
        elif command == "play":
            await device.play()
        elif command == "stop":
            await device.stop()
        elif command in ("next_channel", "ChannelUp"):
            await device.next_channel()
        elif command in ("previous_channel", "ChannelDown"):
            await device.previous_channel()
        elif command == "rewind":
            await device.rewind()
        elif command == "fast_forward":
            await device.fast_forward()
        elif command == "record":
            await device.record()
        elif command == "enter":
            await device.press_enter()
        elif command == "skip_ad":
            skipped = await device.skip_ad_break()
            return web.json_response({"success": True, "skipped": skipped})
        elif command == "send_key":
            key = data.get("key", "")
            if not key:
                return web.json_response({"error": "Missing 'key' parameter."}, status=400)
            await device.send_key_to_box(key)
        elif command == "display_message":
            message = data.get("message", "")
            if not message:
                return web.json_response({"error": "Missing 'message' parameter."}, status=400)
            source_type = data.get("source_type", "linear")
            await device.display_message(source_type, message)
        elif command == "set_channel":
            channel_name = data.get("channel_name", "")
            if not channel_name:
                return web.json_response({"error": "Missing 'channel_name' parameter."}, status=400)
            await device.set_channel(channel_name)
        elif command == "set_channel_by_number":
            channel_number = data.get("channel_number", "")
            if not channel_number:
                return web.json_response({"error": "Missing 'channel_number' parameter."}, status=400)
            await device.set_channel_by_number(channel_number)
        else:
            return web.json_response({"error": f"Unknown command: {command}"}, status=400)

        return web.json_response({"success": True})

    except Exception as e:
        _LOGGER.error("Command %s failed: %s", command, e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


@routes.get("/ws")
async def websocket_handler(request: web.Request):
    """WebSocket endpoint for live device state updates."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    app_state["ws_clients"].add(ws)
    _LOGGER.info("WebSocket client connected (%d total)", len(app_state["ws_clients"]))

    # Send current state of all devices on connect
    if app_state["connected"]:
        for device in app_state["devices"].values():
            try:
                await ws.send_str(json.dumps({
                    "type": "state_change",
                    "device": device_state_to_dict(device),
                }))
            except Exception:
                pass

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.ERROR:
                _LOGGER.error("WebSocket error: %s", ws.exception())
    finally:
        app_state["ws_clients"].discard(ws)
        _LOGGER.info("WebSocket client disconnected (%d remaining)", len(app_state["ws_clients"]))

    return ws


# ── App lifecycle ────────────────────────────────────────────

async def on_shutdown(app: web.Application):
    """Clean up on server shutdown."""
    if app_state["connected"]:
        try:
            api = app_state["api"]
            if api:
                await api.disconnect()
            session = app_state["session"]
            if session:
                await session.close()
        except Exception as e:
            _LOGGER.error("Error during shutdown cleanup: %s", e)

    for ws in app_state["ws_clients"]:
        await ws.close()
    app_state["ws_clients"].clear()


def create_app() -> web.Application:
    """Create and configure the aiohttp web application."""
    app = web.Application()
    app.add_routes(routes)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    print("┌────────────────────────────────────────┐")
    print("│  LG Horizon Test UI                    │")
    print("│  Open: http://localhost:8080            │")
    print("└────────────────────────────────────────┘")
    web.run_app(create_app(), host="0.0.0.0", port=8080)
