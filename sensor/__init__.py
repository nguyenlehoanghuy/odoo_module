from . import controllers
from . import mqtt_client
from . import models
from . import websocket


def _post_init_hook(cr, registry):
    client = mqtt_client.MQTTClient(
        'test.mosquitto.org', 1883, 'odoo_16', 'sensor')
    client.start()
