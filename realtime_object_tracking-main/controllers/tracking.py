from odoo import http
from odoo.http import request, route


class ObjectTracking(http.Controller):
    @http.route(['/tracking'], type='http', auth='public')
    def show_sensors(self):
        """
        Renders the Tracking page
        """
        return request.render('realtime_object_tracking.tracking')
