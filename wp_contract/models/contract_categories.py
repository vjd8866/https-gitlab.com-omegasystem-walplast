from odoo import api, fields, models, _

class Contracts(models.Model):
    _name = 'wp.contract.categories'

    name = fields.Char("Name")