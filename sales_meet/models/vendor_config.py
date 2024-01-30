from odoo import tools, api, fields, models, _, tools, registry, SUPERUSER_ID


class VendorConfig(models.Model):
    _name = 'vendor.config'

    c_bpartner_id = fields.Char("C BPartner ID")
    name = fields.Char("Name contains..")
    based_on = fields.Selection(
        selection=[('id_based', "Based on C_BPartner_id"), ('name_based', "Based on Vendor name")],
        default='name_based')
    operation = fields.Selection(selection=[('block_amount', "Block Amount"), ('add_tds', "Add TDS")],
                                 default='block_amount')
    amount = fields.Float("Amount to Block")
    is_active = fields.Boolean("Active")
