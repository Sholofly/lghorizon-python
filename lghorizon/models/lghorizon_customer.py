from typing import Optional, Dict
from .lghorizon_profile import LGHorizonProfile


class LGHorizonCustomer:
    """LGHorizon customer"""

    customer_id: Optional[str] = None
    hashed_customer_id: Optional[str] = None
    country_id: Optional[str] = None
    city_id: int = 0
    settop_boxes: Optional[list[str]] = None
    profiles: Dict[str, LGHorizonProfile] = {}

    def __init__(self, json_payload):
        self.customer_id = json_payload["customerId"]
        self.hashed_customer_id = json_payload["hashedCustomerId"]
        self.country_id = json_payload["countryId"]
        self.city_id = json_payload["cityId"]
        if "assignedDevices" in json_payload:
            self.settop_boxes = json_payload["assignedDevices"]
        if "profiles" in json_payload:
            for profile in json_payload["profiles"]:
                self.profiles[profile["profileId"]] = LGHorizonProfile(profile)
