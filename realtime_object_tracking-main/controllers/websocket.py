# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from werkzeug.exceptions import ServiceUnavailable

from odoo.http import Controller, request, route
from ..websocket import WebsocketConnectionHandler


class WebsocketController(Controller):
    @route('/websocket/camera', type="http", auth="public", cors='*', websocket=True)
    def camera_handler(self):
        is_headful_browser = request.httprequest.user_agent and 'Headless' not in request.httprequest.user_agent.string
        if request.registry.in_test_mode() and is_headful_browser:
            # Prevent browsers from interfering with the unittests
            raise ServiceUnavailable()
        return WebsocketConnectionHandler.open_connection(request)
