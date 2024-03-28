from odoo import http
from odoo.http import request, route


class Sensor(http.Controller):
    @http.route(['/sensors'], type='http', auth='public')
    def show_sensors(self):
        """
        Renders the Sensors page
        """
        return request.render('sensor.sensor_value')
