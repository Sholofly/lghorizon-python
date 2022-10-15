from .lghorizon_auth import LGHorizonAuth
import paho.mqtt.client as mqtt
from ..helpers import make_id
import json
import logging
from typing import Callable

_logger = logging.getLogger(__name__)
DEFAULT_PORT = 443
class LGHorizonMqttClient:
    _brokerUrl:str = None
    _mqtt_client :mqtt.Client
    _auth: LGHorizonAuth
    clientId: str = None
    _on_connected_callback: Callable = None
    _on_message_callback: Callable[[str],None] = None

    @property
    def is_connected(self):
        return self._mqtt_client.is_connected

    def __init__(self, auth:LGHorizonAuth, on_connected_callback:Callable = None, on_message_callback:Callable[[str],None] = None):
        self._auth = auth
        self._brokerUrl = "obomsg.prod.nl.horizon.tv"
        self.clientId = make_id()
        self._mqtt_client = mqtt.Client(self.clientId, transport="websockets")
        self._mqtt_client.username_pw_set(self._auth.householdId, self._auth.mqttToken)
        self._mqtt_client.tls_set()
        self._mqtt_client.enable_logger(_logger)
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._on_connected_callback = on_connected_callback
        self._on_message_callback = on_message_callback
    
    def _on_mqtt_connect(self, client, userdata, flags, resultCode):
        if resultCode == 0:
            self._mqtt_client.on_message = self._on_client_message
            self._mqtt_client.subscribe(self._auth.householdId)
            self._mqtt_client.subscribe(self._auth.householdId + "/#")
            self._mqtt_client.subscribe(self._auth.householdId + "/" + self.clientId)
            self._mqtt_client.subscribe(self._auth.householdId + "/+/status")
            self._mqtt_client.subscribe(self._auth.householdId + "/+/networkRecordings")
            self._mqtt_client.subscribe(self._auth.householdId + "/+/networkRecordings/capacity")
            self._mqtt_client.subscribe(self._auth.householdId + "/watchlistService")
            self._mqtt_client.subscribe(self._auth.householdId + "/purchaseService")
            self._mqtt_client.subscribe(self._auth.householdId + "/personalizationService")
            self._mqtt_client.subscribe(self._auth.householdId + "/recordingStatus")
            self._mqtt_client.subscribe(self._auth.householdId + "/recordingStatus/lastUserAction")
            if self._on_connected_callback:
                self._on_connected_callback()
        elif resultCode == 5:
            client.username_pw_set(self._auth.householdId, self._auth.mqttToken)
            client.connect(self._brokerUrl, DEFAULT_PORT)
            client.loop_start()
        else:
            raise Exception("Could not connect to Mqtt server")
    
    def connect(self) -> None:
        self._mqtt_client.connect(self._brokerUrl, DEFAULT_PORT)
        self._mqtt_client.loop_start()
    
    def _on_client_message(self, client, userdata, message):
        """Handle messages received by mqtt client."""
        jsonPayload = json.loads(message.payload)
        if self._on_message_callback:
            self._on_message_callback(jsonPayload)

    def publish_message(self, topic:str, json_payload:str) -> None:
        self._mqtt_client.publish(topic, json_payload)
        
    def disconnect(self) -> None:
        if self._mqtt_client.is_connected:
            self._mqtt_client.disconnect()
