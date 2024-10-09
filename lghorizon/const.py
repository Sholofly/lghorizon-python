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

COUNTRY_SETTINGS = {
    "nl": {
        "api_url": "https://spark-prod-nl.gnp.cloud.ziggogo.tv",
        "mqtt_url": "obomsg.prod.nl.horizon.tv",
        "use_oauth": False,
        "channels": [
            {
                "channelId": "NL_000073_019506",
                "channelName": "Netflix",
                "channelNumber": "150",
            },
            {
                "channelId": "NL_000074_019507",
                "channelName": "Videoland",
                "channelNumber": "151",
            },
            {
                "channelId": "NL_000194_019352",
                "channelName": "NPO",
                "channelNumber": "152",
            },
            {
                "channelId": "NL_000199_019356",
                "channelName": "Prime Video",
                "channelNumber": "153",
            },
        ],
        "platform_types": {
            "EOS": {"manufacturer": "Arris", "model": "DCX960"},
            "APOLLO": {"manufacturer": "Arris", "model": "VIP5002W"},
        },
        "language": "nl",
    },
    "ch": {
        "api_url": "https://spark-prod-ch.gnp.cloud.sunrisetv.ch",
        "use_oauth": False,
        "channels": [],
        "language": "de",
    },
    "be-nl": {
        "api_url": "https://spark-prod-be.gnp.cloud.telenet.tv",
        "use_oauth": True,
        "oauth_username_fieldname": "j_username",
        "oauth_password_fieldname": "j_password",
        "oauth_add_accept_header": False,
        "oauth_url": "https://login.prd.telenet.be/openid/login.do",
        "oauth_quote_login": False,
        "oauth_redirect_header": "Location",
        "channels": [
            {"channelId": "netflix", "channelName": "Netflix", "channelNumber": "600"},
            {"channelId": "youtube", "channelName": "Youtube", "channelNumber": "-1"},
        ],
        "platform_types": {
            "EOS": {"manufacturer": "Arris", "model": "DCX960"},
            "HORIZON": {"manufacturer": "Arris", "model": "DCX960"},
            "EOS2": {"manufacturer": "HUMAX", "model": "2008C-STB-TN"},
        },
        "language": "nl",
    },
    "be-nl-preprod": {
        "api_url": "https://spark-preprod-be.gnp.cloud.telenet.tv",
        "use_oauth": True,
        "oauth_username_fieldname": "j_username",
        "oauth_password_fieldname": "j_password",
        "oauth_add_accept_header": False,
        "oauth_url": "https://login.prd.telenet.be/openid/login.do",
        "oauth_quote_login": False,
        "oauth_redirect_header": "Location",
        "channels": [
            {"channelId": "netflix", "channelName": "Netflix", "channelNumber": "600"},
            {"channelId": "youtube", "channelName": "Youtube", "channelNumber": "-1"},
        ],
        "platform_types": {
            "EOS": {"manufacturer": "Arris", "model": "DCX960"},
            "HORIZON": {"manufacturer": "Arris", "model": "DCX960"},
            "EOS2": {"manufacturer": "HUMAX", "model": "2008C-STB-TN"},
        },
        "language": "nl",
    },
    "gb": {
        "api_url": "https://spark-prod-gb.gnp.cloud.virgintvgo.virginmedia.com",
        "channels": [],
        "language": "en",
    },
    "ie": {
        "api_url": "https://spark-prod-ie.gnp.cloud.virginmediatv.ie",
        "use_oauth": False,
        "channels": [],
        "language": "en",
    },
    "pl": {
        "api_url": "https://spark-prod-pl.gnp.cloud.upctv.pl",
        "use_oauth": False,
        "channels": [],
        "language": "pl",
        "platform_types": {
            "EOS": {"manufacturer": "Arris", "model": "DCX960"},
            "APOLLO": {"manufacturer": "Arris", "model": "VIP5002W"},
        },
    },
}
