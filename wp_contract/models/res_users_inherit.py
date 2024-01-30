from odoo import api, fields, models, _

class ContractUsers(models.Model):
    _inherit = 'res.users'

    department_id = fields.Many2one(comodel_name='hr.department',string="Department",compute="compute_users_department")
    allowed_department_ids = fields.Many2many('hr.department',string="Allowed Departments")

    def compute_users_department(self):
        for rec in self:
            employee = self.env['hr.employee'].sudo().search([('user_id','=',rec.id),('active','=',True)])
            if employee:
                rec.department_id = employee.department_id.id
            else:
                rec.department_id = False

# class ContractDepts(models.Model):
#     _inherit = 'hr.department'
#
#     contr_user_id = fields.Many2one('hr.department',"User")