import base64
import functools
import hashlib
import logging
import threading
import odoo

from psycopg2.pool import PoolError
from werkzeug.exceptions import BadRequest

from odoo import api
from odoo.http import root, Response, SessionExpiredException
from odoo.addons.bus.websocket import Websocket, CloseCode, UpgradeRequired, ConnectionState, acquire_cursor

from .machine_learning.predict import ObjectTracking

MODEL_PATH = "addons/realtime_object_tracking/machine_learning/weights/best.pt"

_logger = logging.getLogger(__name__)


class WebsocketConnectionHandler:
    SUPPORTED_VERSIONS = {'13'}
    # Given by the RFC in order to generate Sec-WebSocket-Accept from
    # Sec-WebSocket-Key value.
    _HANDSHAKE_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    _REQUIRED_HANDSHAKE_HEADERS = {
        'connection', 'host', 'sec-websocket-key',
        'sec-websocket-version', 'upgrade',
    }

    @classmethod
    def _get_handshake_response(cls, headers):
        """
        :return: Response indicating the server performed a connection
        upgrade.
        :raise: BadRequest
        :raise: UpgradeRequired
        """
        cls._assert_handshake_validity(headers)
        # sha-1 is used as it is required by
        # https://datatracker.ietf.org/doc/html/rfc6455#page-7
        accept_header = hashlib.sha1(
            (headers['sec-websocket-key'] + cls._HANDSHAKE_GUID).encode()).digest()
        accept_header = base64.b64encode(accept_header)
        return Response(status=101, headers={
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Accept': accept_header,
        })

    @classmethod
    def _assert_handshake_validity(cls, headers):
        """
        :raise: UpgradeRequired if there is no intersection between
        the version the client supports and those we support.
        :raise: BadRequest in case of invalid handshake.
        """
        missing_or_empty_headers = {
            header for header in cls._REQUIRED_HANDSHAKE_HEADERS
            if header not in headers
        }
        if missing_or_empty_headers:
            raise BadRequest(
                f"""Empty or missing header(s): {', '.join(missing_or_empty_headers)}"""
            )

        if headers['upgrade'].lower() != 'websocket':
            raise BadRequest('Invalid upgrade header')
        if 'upgrade' not in headers['connection'].lower():
            raise BadRequest('Invalid connection header')
        if headers['sec-websocket-version'] not in cls.SUPPORTED_VERSIONS:
            raise UpgradeRequired()

        key = headers['sec-websocket-key']
        try:
            decoded_key = base64.b64decode(key, validate=True)
        except ValueError:
            raise BadRequest("Sec-WebSocket-Key should be b64 encoded")
        if len(decoded_key) != 16:
            raise BadRequest(
                "Sec-WebSocket-Key should be of length 16 once decoded"
            )

    @classmethod
    def open_connection(cls, request):
        """
        Open a websocket connection if the handshake is successful.
        :return: Response indicating the server performed a connection
        upgrade.
        :raise: UpgradeRequired if there is no intersection between the
        versions the client supports and those we support.
        :raise: BadRequest if the handshake data is incorrect.
        """
        response = cls._get_handshake_response(request.httprequest.headers)
        response.call_on_close(functools.partial(
            cls._serve_forever,
            Websocket(request.httprequest.environ['socket'], request.session),
            request.db,
            request.httprequest
        ))
        # Force save the session. Session must be persisted to handle
        # WebSocket authentication.
        request.session.is_dirty = True
        return response

    @classmethod
    def _serve_forever(cls, websocket, db, httprequest):
        current_thread = threading.current_thread()
        current_thread.type = 'websocket'

        try:
            tracking = ObjectTracking(MODEL_PATH)
            tracking.predict(websocket, db)
            # registry = odoo.modules.registry.Registry(db)
            # with odoo.api.Environment.manage(), registry.cursor() as cr:
            #     env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
            #     tmp = env['sensor'].search(
            #         [('name', '=', 'Temperature')], limit=1)
            #     tmp_value = env['sensor.value'].search(
            #         [('sensor_id', '=', tmp['id'])], limit=1, order="create_date DESC")
            #     odo = env['sensor'].search(
            #         [('name', '=', 'Dissolved oxygen')], limit=1)
            #     odo_value = env['sensor.value'].search(
            #         [('sensor_id', '=', odo['id'])], limit=1, order="create_date DESC")
            #     fph = env['sensor'].search(
            #         [('name', '=', 'pH')], limit=1)
            #     fph_value = env['sensor.value'].search(
            #         [('sensor_id', '=', fph['id'])], limit=1, order="create_date DESC")

            #     print("[TEST] Websocket send.")
            #     websocket._send({
            #         'name': tmp['name'],
            #         'value': tmp_value['value']})
            #     websocket._send({
            #         'name': odo['name'],
            #         'value': odo_value['value']})
            #     websocket._send({
            #         'name': fph['name'],
            #         'value': fph_value['value']})
        except SessionExpiredException:
            websocket.disconnect(CloseCode.SESSION_EXPIRED)
        except PoolError:
            websocket.disconnect(CloseCode.TRY_LATER)
        except ConnectionResetError:
            websocket.disconnect(CloseCode.ABNORMAL_CLOSURE)
        except ConnectionAbortedError:
            websocket.disconnect(CloseCode.ABNORMAL_CLOSURE)
        except Exception:
            websocket.disconnect(CloseCode.ABNORMAL_CLOSURE)
