from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning, ValidationError

class ContractRemarks(models.TransientModel):
    _name = 'contract.remarks'

    name = fields.Char("Remarks")
    remark_type = fields.Selection([('closed',"Closed"),('renewed',"Renewed")])
    contract_id = fields.Many2one('wp.contracts')
    #
    # @api.model
    # def default_get(self, fields_list):
    #     defaults = super(ContractRemarks, self).default_get(fields_list)
    #     active_id = self.env.context.get('active_id')
    #     contract = self.env['wp.contracts'].browse(active_id)
    #     if self.env.context.get('default_set_to_expired') == True:
    #         self.remark_type = 'closed'
    #
    #     if self.env.context.get('default_set_to_renewed') == True:
    #         self.remark_type =  'renewed'
    #
    #     self.contract_id = contract.id
    #
    #     return defaults

    # @api.model
    # def create(self,vals):
    #     contract = vals['contract_id']
    #     if vals['remark_type'] == 'closed':
    #         contract.status = 'expired'
    #         contract.closed_remarks = vals['name']
    #     if vals['remark_type'] == 'renewed':
    #         contract.status = 'renewed'
    #         contract.closed_remarks = vals['name']
    #
    #     return super(ContractRemarks, self).create(vals)


    def submit(self):
        active_id = self.env.context.get('active_id')
        contract = self.env['wp.contracts'].browse(active_id)
        if self.env.context.get('default_set_to_expired') == True:
            contract.status = 'expired'
            contract.closed_remarks = self.name
            contract.renewed_remarks = False
        if self.env.context.get('default_set_to_renewed') == True:
            contract.status = 'renewed'
            contract.renewed_remarks = self.name
            contract.closed_remarks = False
        self.contract_id = contract.id

        # contract = vals['contract_id']
        # if vals['remark_type'] == 'closed':
        #     contract.status = 'expired'
        #     contract.closed_remarks = vals['name']
        # if vals['remark_type'] == 'renewed':
        #     contract.status = 'renewed'
        #     contract.closed_remarks = vals['name']