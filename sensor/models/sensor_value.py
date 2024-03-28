from odoo import fields, models


class SensorValue(models.Model):
    _name = 'sensor.value'
    _description = 'Sensor value'

    value = fields.Float()
    sensor_id = fields.Many2one('sensor', string='Sensor')
