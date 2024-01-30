from odoo import api, fields, models, _
from datetime import datetime, timedelta, date

class ContractSupplier(models.Model):
    _name = 'contract.supplier'

    name = fields.Char("Name")
    contact_no = fields.Integer("Contact No.")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state',"State")
    country_id = fields.Many2one('res.country',"Country")
    zip_code = fields.Char("Zip Code")
