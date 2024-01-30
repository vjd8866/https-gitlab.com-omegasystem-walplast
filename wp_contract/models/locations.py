from odoo import api, fields, models, _

class locations(models.Model):
    _name = 'wp.locations'

    name = fields.Char("Name")
    desc = fields.Char("Description")
    search_key = fields.Char("Search Key")
    company_id = fields.Many2one('res.company',"Company")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state', "State")
    country_id = fields.Many2one('res.country', "Country")
    zip_code = fields.Char("Zip Code")