"""Python client for LGHorizon."""

# flake8: noqa
# Box states
ONLINE_RUNNING = "ONLINE_RUNNING"
ONLINE_STANDBY = "ONLINE_STANDBY"
UNKNOWN = "UNKNOWN"

BOX_PLAY_STATE_CHANNEL = "linear"
BOX_PLAY_STATE_REPLAY = "replay"
BOX_PLAY_STATE_DVR = "nDVR"
BOX_PLAY_STATE_BUFFER = "reviewbuffer"
BOX_PLAY_STATE_APP = "app"
BOX_PLAY_STATE_VOD = "VOD"

# List with available media keys.
MEDIA_KEY_POWER = "Power"
MEDIA_KEY_ENTER = "Enter"
MEDIA_KEY_ESCAPE = "Escape"  # Not yet implemented

MEDIA_KEY_HELP = "Help"  # Not yet implemented
MEDIA_KEY_INFO = "Info"  # Not yet implemented
MEDIA_KEY_GUIDE = "Guide"  # Not yet implemented

MEDIA_KEY_CONTEXT_MENU = "ContextMenu"  # Not yet implemented
MEDIA_KEY_CHANNEL_UP = "ChannelUp"
MEDIA_KEY_CHANNEL_DOWN = "ChannelDown"

MEDIA_KEY_RECORD = "MediaRecord"
MEDIA_KEY_PLAY_PAUSE = "MediaPlayPause"
MEDIA_KEY_STOP = "MediaStop"
MEDIA_KEY_REWIND = "MediaRewind"
MEDIA_KEY_FAST_FORWARD = "MediaFastForward"

RECORDING_TYPE_SINGLE = "single"
RECORDING_TYPE_SHOW = "show"
RECORDING_TYPE_SEASON = "season"

BE_AUTH_URL = "https://login.prd.telenet.be/openid/login.do"

PLATFORM_TYPES = {
    "EOS": {"manufacturer": "Arris", "model": "DCX960"},
    "EOS2": {"manufacturer": "HUMAX", "model": "2008C-STB-TN"},
    "HORIZON": {"manufacturer": "Arris", "model": "DCX960"},
    "APOLLO": {"manufacturer": "Arris", "model": "VIP5002W"},
}

COUNTRY_SETTINGS = {
    "nl": {
        "api_url": "https://spark-prod-nl.gnp.cloud.ziggogo.tv",
        "mqtt_url": "obomsg.prod.nl.horizon.tv",
        "use_refreshtoken": False,
        "name": "Ziggo",
    },
    "ch": {
        "api_url": "https://spark-prod-ch.gnp.cloud.sunrisetv.ch",
        "use_refreshtoken": True,
        "name": "UPC Switzerland",
    },
    "be-basetv": {
        "api_url": "https://spark-prod-be.gnp.cloud.base.tv",
        "use_refreshtoken": True,
        "name": "BASE TV (BE)",
    },
    "be-nl": {
        "api_url": "https://spark-prod-be.gnp.cloud.telenet.tv",
        "use_refreshtoken": True,
        "name": "Telenet (BE)",
    },
    "be-nl-preprod": {
        "api_url": "https://spark-preprod-be.gnp.cloud.telenet.tv",
        "use_refreshtoken": True,
        "name": "Telenet (BE, PREPROD)",
    },
    "gb": {
        "api_url": "https://spark-prod-gb.gnp.cloud.virgintvgo.virginmedia.com",
        "use_refreshtoken": True,
        "name": "Virgin Media (GB)",
    },
    "ie": {
        "api_url": "https://spark-prod-ie.gnp.cloud.virginmediatv.ie",
        "use_refreshtoken": False,
        "name": "Virgin Media (IE)",
    },
    "pl": {
        "api_url": "https://spark-prod-pl.gnp.cloud.upctv.pl",
        "use_refreshtoken": False,
        "name": "UPC (PL)",
    },
}
