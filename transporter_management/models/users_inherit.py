from odoo import api, fields, models, tools
from datetime import datetime, timedelta, date

class Users(models.Model):
    _inherit = 'res.users'

    factory_id = fields.Many2one('wp.plant',string="Factory")