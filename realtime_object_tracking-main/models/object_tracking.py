from odoo import fields, models


class ObjectTracking(models.Model):
    _name = 'object.tracking'
    _description = 'Object tracking'

    object = fields.Json()
    img = fields.Binary()
