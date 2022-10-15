
from typing import Dict
from .lghorizon_box import LGHorizonBox
_supported_platforms = ["EOS", "EOS2", "HORIZON", "APOLLO"]

class LGHorizonCustomer:
    customerId:str = None
    hashedCustomerId:str = None 
    countryId: str = None
    cityId: int = 0
    settop_boxes: Dict[str, LGHorizonBox] = None

    def __init__(self, json_payload):
        self.customerId = json_payload["customerId"]
        self.hashedCustomerId = json_payload["hashedCustomerId"]
        self.countryId = json_payload["countryId"]
        self.cityId = json_payload["cityId"]
        if not "assignedDevices" in json_payload:
            return

        
