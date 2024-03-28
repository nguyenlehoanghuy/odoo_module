from . import controllers
from . import camera
from . import models
from . import websocket
from . import machine_learning


def _post_init_hook(cr, registry):
    cam = camera.Camera('odoo_16', 'realtime_object_tracking')
    cam.start()
