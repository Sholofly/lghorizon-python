"""Contains LG authorization info."""
    
from datetime import datetime

class LGHorizonAuth:
    householdId: str
    accessToken: str
    refreshToken: str
    refreshTokenExpiry: datetime
    username: str
    mqttToken: str = None

    def __init__(self, auth_json:str):
        """Initialize a session."""
        self.householdId = auth_json["householdId"]
        self.accessToken = auth_json["accessToken"]
        self.refreshToken = auth_json["refreshToken"]
        self.refreshTokenExpiry = datetime.fromtimestamp(auth_json["refreshTokenExpiry"])
        self.username = auth_json["username"]
    
    def is_expired(self) -> bool:
        return self.refreshTokenExpiry
        