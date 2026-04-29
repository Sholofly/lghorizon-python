"""Python client for LGHorizon."""

BOX_PLAY_STATE_CHANNEL = "linear"
BOX_PLAY_STATE_REPLAY = "replay"
BOX_PLAY_STATE_DVR = "nDVR"
BOX_PLAY_STATE_BUFFER = "reviewbuffer"
BOX_PLAY_STATE_APP = "app"
BOX_PLAY_STATE_VOD = "VOD"

# List with available media keys.
# Power
MEDIA_KEY_POWER = "Power"
MEDIA_KEY_STANDBY = "Standby"
MEDIA_KEY_WAKEUP = "WakeUp"

# Media Playback
MEDIA_KEY_PLAY = "MediaPlay"
MEDIA_KEY_PAUSE = "MediaPause"
MEDIA_KEY_PLAY_PAUSE = "MediaPlayPause"
MEDIA_KEY_STOP = "MediaStop"
MEDIA_KEY_RECORD = "MediaRecord"
MEDIA_KEY_FAST_FORWARD = "MediaFastForward"
MEDIA_KEY_REWIND = "MediaRewind"
MEDIA_KEY_TRACK_NEXT = "MediaTrackNext"
MEDIA_KEY_TRACK_PREVIOUS = "MediaTrackPrevious"

# Channel / Navigation
MEDIA_KEY_CHANNEL_UP = "ChannelUp"
MEDIA_KEY_CHANNEL_DOWN = "ChannelDown"
MEDIA_KEY_TOP_MENU = "MediaTopMenu"
MEDIA_KEY_GUIDE = "Guide"
MEDIA_KEY_HELP = "Help"
MEDIA_KEY_INFO = "Info"
MEDIA_KEY_CONTEXT_MENU = "ContextMenu"
MEDIA_KEY_NEXT_USER_PROFILE = "NextUserProfile"
MEDIA_KEY_TV = "TV"
MEDIA_KEY_TELETEXT = "Teletext"
MEDIA_KEY_SUBTITLE = "Subtitle"
MEDIA_KEY_AUDIO_TRACK = "AudioTrack"

# UI Navigation (D-Pad)
MEDIA_KEY_ARROW_UP = "ArrowUp"
MEDIA_KEY_ARROW_DOWN = "ArrowDown"
MEDIA_KEY_ARROW_LEFT = "ArrowLeft"
MEDIA_KEY_ARROW_RIGHT = "ArrowRight"
MEDIA_KEY_ENTER = "Enter"
MEDIA_KEY_ESCAPE = "Escape"
MEDIA_KEY_BACKSPACE = "Backspace"

# Colour Buttons
MEDIA_KEY_RED = "Red"
MEDIA_KEY_GREEN = "Green"
MEDIA_KEY_YELLOW = "Yellow"
MEDIA_KEY_BLUE = "Blue"

# Digit Keys
MEDIA_KEY_0 = "0"
MEDIA_KEY_1 = "1"
MEDIA_KEY_2 = "2"
MEDIA_KEY_3 = "3"
MEDIA_KEY_4 = "4"
MEDIA_KEY_5 = "5"
MEDIA_KEY_6 = "6"
MEDIA_KEY_7 = "7"
MEDIA_KEY_8 = "8"
MEDIA_KEY_9 = "9"

# Grouped for API/UI consumers
MEDIA_KEYS = {
    "Power": [MEDIA_KEY_POWER, MEDIA_KEY_STANDBY, MEDIA_KEY_WAKEUP],
    "Playback": [
        MEDIA_KEY_PLAY, MEDIA_KEY_PAUSE, MEDIA_KEY_PLAY_PAUSE,
        MEDIA_KEY_STOP, MEDIA_KEY_RECORD,
        MEDIA_KEY_FAST_FORWARD, MEDIA_KEY_REWIND,
        MEDIA_KEY_TRACK_NEXT, MEDIA_KEY_TRACK_PREVIOUS,
    ],
    "Navigation": [
        MEDIA_KEY_CHANNEL_UP, MEDIA_KEY_CHANNEL_DOWN,
        MEDIA_KEY_TOP_MENU, MEDIA_KEY_GUIDE, MEDIA_KEY_HELP,
        MEDIA_KEY_INFO, MEDIA_KEY_CONTEXT_MENU,
        MEDIA_KEY_NEXT_USER_PROFILE, MEDIA_KEY_TV,
        MEDIA_KEY_TELETEXT, MEDIA_KEY_SUBTITLE, MEDIA_KEY_AUDIO_TRACK,
    ],
    "D-Pad": [
        MEDIA_KEY_ARROW_UP, MEDIA_KEY_ARROW_DOWN,
        MEDIA_KEY_ARROW_LEFT, MEDIA_KEY_ARROW_RIGHT,
        MEDIA_KEY_ENTER, MEDIA_KEY_ESCAPE, MEDIA_KEY_BACKSPACE,
    ],
    "Colour": [MEDIA_KEY_RED, MEDIA_KEY_GREEN, MEDIA_KEY_YELLOW, MEDIA_KEY_BLUE],
    "Digits": [
        MEDIA_KEY_0, MEDIA_KEY_1, MEDIA_KEY_2, MEDIA_KEY_3, MEDIA_KEY_4,
        MEDIA_KEY_5, MEDIA_KEY_6, MEDIA_KEY_7, MEDIA_KEY_8, MEDIA_KEY_9,
    ],
}

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
