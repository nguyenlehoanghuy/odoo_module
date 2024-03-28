import json
import paho.mqtt.client as mqtt
import threading
import odoo


class MQTTClient(threading.Thread):
    def __init__(self, host, port, db, module_name):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.db = db
        self.module_name = module_name
        self.client = mqtt.Client()
        self.state = "installed"

    def run(self):
        self.client.connect(self.host, self.port)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.loop_start()
        while self.state == "installed":
            registry = odoo.modules.registry.Registry(self.db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                module = env['ir.module.module'].search(
                    [('name', '=', self.module_name)], limit=1)
                self.state = module.state
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        print("[TEST] MQTT connected.")
        self.client.subscribe("matrix310/vernier/tmp-bta")
        self.client.subscribe("matrix310/vernier/odo-bta")
        self.client.subscribe("matrix310/vernier/fph-bta")
        self.client.subscribe("matrix752/vernier/tmp-bta")
        self.client.subscribe("matrix752/vernier/odo-bta")
        self.client.subscribe("matrix752/vernier/fph-bta")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection.")
        else:
            print("Disconnected.")

    def on_message(self, client, userdata, msg):
        print("[TEST] MQTT Message.")
        if msg.topic == "matrix310/vernier/tmp-bta" or msg.topic == "matrix752/vernier/tmp-bta":
            self.tmp_handle(self.db, json.loads(msg.payload))
        elif msg.topic == "matrix310/vernier/odo-bta" or msg.topic == "matrix752/vernier/odo-bta":
            self.odo_handle(self.db, json.loads(msg.payload))
        else:
            self.fph_handle(self.db, json.loads(msg.payload))

    def tmp_handle(self, db, data):
        try:
            registry = odoo.modules.registry.Registry(db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                sensor = env['sensor'].search(
                    [('name', '=', data['name'])], limit=1)
                # print("[TEST] Sensor name:", sensor['name'])
                sensor_value = env['sensor.value'].create({
                    'value': data['value'],
                    'sensor_id': sensor['id']
                })
                # print("[TEST] Sensor value:", sensor_value['value'])
        except Exception:
            print(Exception)

    def odo_handle(self, db, data):
        try:
            registry = odoo.modules.registry.Registry(db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                sensor = env['sensor'].search(
                    [('name', '=', data['name'])], limit=1)
                sensor_value = env['sensor.value'].create({
                    'value': data['value'],
                    'sensor_id': sensor['id']
                })
        except Exception:
            print(Exception)

    def fph_handle(self, db, data):
        try:
            registry = odoo.modules.registry.Registry(db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                sensor = env['sensor'].search(
                    [('name', '=', data['name'])], limit=1)
                sensor_value = env['sensor.value'].create({
                    'value': data['value'],
                    'sensor_id': sensor['id']
                })
        except Exception:
            print(Exception)
