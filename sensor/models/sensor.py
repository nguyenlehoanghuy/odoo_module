from odoo import fields, models


class Sensor(models.Model):
    _name = 'sensor'
    _description = 'Sensor'

    name = fields.Char()
    value_ids = fields.One2many(
        'sensor.value', 'sensor_id', string='Sensor value')
