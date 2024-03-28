import cv2
import json
import threading
import odoo

from .machine_learning.predict import ObjectTracking

MODEL_PATH = "addons/realtime_object_tracking/machine_learning/weights/best.pt"


class Camera(threading.Thread):
    def __init__(self, db, module_name):
        threading.Thread.__init__(self)
        self.cap = cv2.VideoCapture("D:\\CV\\yolov8\\test.mp4")
        self.db = db
        self.module_name = module_name
        self.state = "installed"

    def run(self):
        while self.state == "installed":
            registry = odoo.modules.registry.Registry(self.db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                module = env['ir.module.module'].search(
                    [('name', '=', self.module_name)], limit=1)
                self.state = module.state
                tracking = ObjectTracking(MODEL_PATH, self.cap)
                tracking.predict('odoo_16')
