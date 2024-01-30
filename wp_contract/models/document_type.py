from odoo import api, fields, models, _

class ContractDocumentType(models.Model):
    _name = 'contract.document.type'

    name = fields.Char("Name")