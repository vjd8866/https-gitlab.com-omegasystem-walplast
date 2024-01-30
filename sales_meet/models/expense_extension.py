#!/usr/bin/env bash

from odoo.tools.translate import _
from datetime import datetime, timedelta, date
from odoo import api, fields, models, _, tools, SUPERUSER_ID
import logging
from time import gmtime, strftime
from odoo.exceptions import UserError , ValidationError
import dateutil.parser
from werkzeug.urls import url_encode
import odoo.addons.decimal_precision as dp

class expense_extension(models.Model):
    _inherit = "hr.expense"

    def _default_grade(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        grade = self.env['hr.employee'].sudo().search([('id', '=', employee_id.id)], limit=1).grade_id.id
        return grade

    def _default_work_location(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1).work_location

    
    def _compute_can_edit_name(self):
        self.can_edit_name = self.env.user.sudo().has_group('sales_meet.group_expense_manager_user')

    meeting_id = fields.Many2one("calendar.event", string="Meeting" )
    name = fields.Char(string='Expense Description', required=False)
    grade_id = fields.Many2one("grade.master", string="Grade" , default=_default_grade, store=True, track_visibility='onchange' )
    grade_amount = fields.Float(string='Amount allocated' , compute='_compute_grade_amount' , store=True, track_visibility='onchange')
    fixed_asset = fields.Boolean("Fixed Asset", store=True, track_visibility='onchange', compute='_compute_grade_amount')
    unit_amount = fields.Float(string='Unit Price', store=True, track_visibility='onchange', readonly=False )
    week_no = fields.Char(string='Week' , compute='_onchange_date' , store=True, track_visibility='onchange' , readonly=False )
    backdate_alert = fields.Boolean("Back Dated Record", store=True, track_visibility='onchange')
    work_location = fields.Char(string='Work Location', default=_default_work_location, store=True)
    idempere_no = fields.Char(string='Idempiere No' , store=True, track_visibility='onchange' , readonly=False )
    meeting_address = fields.Char(string='Meeting Address', compute='_onchange_meeting_id', store=True)
    claimed_amount = fields.Float(string='Claimed Amount', store=True, track_visibility='onchange', readonly=False )
    expense_attachments = fields.Many2many('ir.attachment', 'expense_attachments_rel' , copy=False, attachment=True)
    manager_id = fields.Many2one('hr.employee', string="Manager" , related="employee_id.parent_id")
    meeting_boolean = fields.Boolean("Meeting Bool" , default=False )
    once_only = fields.Boolean("Only Once", compute='_compute_grade_amount', store=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('can_be_expensed', '=', True)])
    can_edit_name = fields.Boolean(compute='_compute_can_edit_name')
    posted_bool = fields.Boolean('Posted', default=False)
    mobile_id = fields.Char('Mobile ID' )
    # expense_duplicated = fields.Boolean(compute='check_multiple_expense')

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve":
                expense.state = "approved"
            elif not expense.sheet_id.state == "post":
                expense.state = "done"
            else:
                expense.state = "reported"

    def unlink(self):
        for order in self:
            if order.state != 'draft'  and self.env.uid != 1:
                raise UserError(_('You can only Delete Draft Entries'))
        return super(expense_extension, self).unlink()

    def validate_expense(self,id=None,emp_id=None, product_id=None, product_name=None,
                              expense_date=None, meeting_id=None, total_amount=None):

        if total_amount == 0.0:
            raise UserError(_("You cannot Submit expense with 0.0 Rs !"))

        # print("1111111111111111111111111111111111111", emp_id, product_id, expense_date, meeting_id)

        expense_ids = self.env['hr.expense'].sudo().search([('id','!=',id),('employee_id', '=', emp_id),
                                                            ('product_id', '=', product_id),
                                                            ('date', '=', expense_date),
                                                            ('once_only','=',True)])

        # # print "--------------------- 1111111 expense_ids ------------", expense_ids
        if len(expense_ids) >= 1:
            # raise UserError(_("Expense Already Created for '%s' - Dated %s" %(self.product_id.name, self.date)))
            return "Expense Already Created for '%s' (Only Once in a Day) - Dated %s" %(product_name, expense_date)


        expense_ids2 = self.env['hr.expense'].sudo().search([('id','!=',id),('employee_id', '=', emp_id),
                                                            ('product_id', '=', product_id),
                                                            ('date', '=', expense_date),
                                                            ('meeting_id', '=', meeting_id)])


        # # print "--------------------- 2222222 expense_ids2 ------------ " , expense_ids2

        if len(expense_ids2) >= 1:
            # raise UserError(_("Expense Already Created for '%s' for this meeting dated - %s" %(self.product_id.name, self.date)))
            return "Expense Already Created for '%s' for this meeting dated - %s" %(product_name, expense_date)



    
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))

        # validate_expense = self.validate_expense(emp_id=self.employee_id.id, 
        #                       product_id=self.product_id.id,
        #                       product_name=self.product_id.name,
        #                       expense_date=self.date,
        #                       meeting_id=self.meeting_id.id,
        #                       total_amount=self.total_amount )  
        # print("---------validate_expense-------", validate_expense)
        # if validate_expense:
        #     raise UserError(validate_expense)

        return {
             'type': 'ir.actions.act_window',
             'view_mode': 'form',
             'res_model': 'hr.expense.sheet',
             'target': 'new',
             'context': {
                 'default_expense_line_ids': [line.id for line in self],
                 'default_employee_id': self[0].employee_id.id,
                 'default_name': self[0].name if len(self.ids) == 1 else '',
                 'default_expense_meeting_id': self[0].meeting_id.id,
             }
        }

    @api.onchange('claimed_amount')
    def _onchange_claimed_amount(self):
        if self.claimed_amount: self.unit_amount = self.claimed_amount

    @api.depends('meeting_id')
    # # @api.onchange('meeting_id')
    def _onchange_meeting_id(self):
        # if self.meeting_id: self.meeting_address = self.meeting_id.reverse_location
        self.meeting_address = ''



    @api.onchange('product_id')
    def _onchange_product_id(self):
        print("---------------------------- _onchange_product_id ---------------------------")
        amount = 0.0
        fixed_asset = False
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''

            grade_ids = self.env['grade.master'].sudo().search([('id', '=', self.grade_id.id)])
            for line_ids in grade_ids.grade_line_ids:
                for lines in line_ids:
                    if lines.name.id == self.product_id.id:
                        amount = lines.value
                        fixed_asset = lines.fixed_asset
                        if lines.fixed_asset:
                            self.unit_amount = amount
                            self.claimed_amount = amount

            self.name = self.name_creation(product_name=self.product_id.name, date=self.date)
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    def name_creation(self, product_name=False, date=False):
        print("------------- name_creation ----", product_name, date)
        daymonth = datetime.strptime(str(date), "%Y-%m-%d")
        month2 = daymonth.strftime("%b")
        day = daymonth.strftime("%d")
        week_day = daymonth.strftime("%a")
        year = daymonth.strftime("%y")
        name = product_name + ' ' + str(day) + ' ' + str(month2) + ' ' + str(week_day) + ' ' + str(year)
        return name


    @api.depends('product_id')
    def _compute_grade_amount(self):
        grade_amount = 0.0
        fixed_asset = once_only = False

        for res in self:
            # grade_ids = self.env['grade.master'].sudo().search([('id', '=', res.grade_id.id)])
            # for line_ids in grade_ids.grade_line_ids:
            #     for lines in line_ids:
            #         if lines.name.id == res.product_id.id:
            #             grade_amount = lines.value
            #             fixed_asset = lines.fixed_asset
            #             once_only = lines.once_only

            res.grade_amount = grade_amount
            res.fixed_asset = fixed_asset
            res.once_only =  once_only
            print("---------- _compute_grade_amount  --------", grade_amount, fixed_asset, once_only)


    @api.model
    def create(self, vals):
        # context = dict(self._context or {})
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1).id
        product_id = self.env['product.product'].sudo().search([('id', '=', vals['product_id'])], limit=1)
        # if vals['expense_duplicated']
        if 'date' in vals:
            expensedate = vals['date']
        else:
            expensedate = self._context.get('default_date',False)

        if 'meeting_id' in vals:
            expensemeeting_id = vals['meeting_id']
        else:
            expensemeeting_id = self._context.get('default_meeting_id',False)

        result = super(expense_extension, self).create(vals)
        validate_expense = self.validate_expense(
                                                  id=result.id,
                                                  emp_id=employee_id,
                                                  product_id=product_id.id,
                                                  product_name=product_id.name,
                                                  expense_date=expensedate,
                                                  meeting_id=expensemeeting_id,
                                                  total_amount=vals['unit_amount'] )
        print("---------validate_expense-------", validate_expense)
        if validate_expense:
            raise UserError(validate_expense)

        create_date = dateutil.parser.parse(str(result.create_date)).date()
        back_date = create_date - timedelta(days=15 )
        expense_date = datetime.strptime(str(result.date), '%Y-%m-%d').date()
        result.mobile_id = str(result.id)
        if expense_date < back_date:
            result.backdate_alert = True

        print("---------- Create Expense ----------", vals)
        return result

    @api.onchange('date')
    def _onchange_date(self):
        for res in self:
            if res.date and res.meeting_boolean == False:
                date = res.date
                today = datetime.now()
                daymonth = datetime.strptime(str(date), "%Y-%m-%d")
                month2 = daymonth.strftime("%b")
                week_number2 = (daymonth.day - 1) // 7 + 1
                res.week_no =  month2 + ' ' + str(week_number2) + ' Week'
                res.meeting_id = False

            return {'domain': {
                'meeting_id': [('user_id', 'in', [self.env.uid]),
                                ('meeting_type','=','check-in'),
                                ('expense_date', 'in', [res.date]),
                                ('name','!=',False),
                                '|',('active','=',False),('active','!=',False)]}}

    # 
    # def write(self, vals):
    #     res = super(expense_extension, self).write(vals)
    #     if self.expense_duplicated == True:
    #         raise UserError("Only one expense for a day can be created !!")
    #     return res


    # @api.depends('date','product_id')
    # def check_multiple_expense(self):
    #     for rec in self:
    #         if rec.date and rec.product_id:
    #             domain = [('employee_id', '=', rec.employee_id.id), ('date', '=', rec.date.encode('ascii', 'ignore')),
    #                  ('product_id', '=', rec.product_id.id)]
    #             if rec.id:
    #                 domain.append(('id','!=',rec.id))
    #             expnese_exists = self.env['hr.expense'].search(domain)
    #             if expnese_exists:
    #                 rec.update({'expense_duplicated': True})
    #                 raise UserError("Only one expense for a day can be created !!")
                # else:
                #     rec.update({'expense_duplicated ': False})



class HrExpenseSheetExtension(models.Model):
    _inherit = "hr.expense.sheet"

    
    def _compute_can_edit_name(self):
        self.can_edit_name = self.env.user.has_group('sales_meet.group_expense_manager_user')
        print("---------- can_edit_name -------- HrExpenseSheetExtension ")

    parent_boolean = fields.Boolean("Manager approval", store=True, track_visibility='onchange')

    state = fields.Selection([('draft', 'Draft'),('submit', 'Submitted'),
                              ('manager_approve', 'Manager Approved'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, 
                              track_visibility='onchange', copy=False, default='draft', required=True)

    parent_id = fields.Many2one('hr.employee', string="Manager" )
    expense_note = fields.Text(string="Expense Note" ,readonly=True)
    meeting_id = fields.Integer('Expense Meeting')
    reason = fields.Text(string="Reason", readonly=True ) #
    expense_meeting_id = fields.Many2one("calendar.event", string="Meeting" )
    expense_date  = fields.Date(string="Expense Date")
    meeting_date  = fields.Date(string="Meeting Date")
    expense_submit = fields.Boolean("Submitted", store=True)
    manager_approve = fields.Char(string="", default="Manager Approval Needed")
    approve_date  = fields.Date(string="Approve Date")
    can_edit_name = fields.Boolean(compute='_compute_can_edit_name')
    meeting_address = fields.Char(string='Meeting Address', store=True )

    
    def unlink(self):
        for order in self:
            if order.state  and self.env.uid != 1:
                raise UserError(_("You can't Delete Submitted Entries"))
        return super(HrExpenseSheetExtension, self).unlink()

    def action_save(self,context):
        write_data = self.search([('id', '=', context[0])]).sudo().write({'expense_date': date.today(), 
                                                                          'expense_submit': True})
        return {'type': 'ir.actions.act_window_close'}


    
    def action_get_meeting(self):
        print("---------- action_get_meeting ------------------" , self.expense_meeting_id.id)
        meeting_ids = self.env['calendar.event'].search([("id","=",self.expense_meeting_id.id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sales_meet.action_calendar_event_crm')
        list_view_id = imd.xmlid_to_res_id('sales_meet.view_calendar_event_tree_extension')
        form_view_id = imd.xmlid_to_res_id('sales_meet.view_calendar_event_form_extension')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'],
                [False, 'graph'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            
            'context': action.context,
            'res_model': action.res_model,
        }
        # 'target': action.target,
        if len(meeting_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % meeting_ids.ids
        elif len(meeting_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = meeting_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only HR Officers can approve expenses"))
        self.sudo().write({'state': 'approve', 'approve_date':date.today()})


    
    def approve_expense_sheets_manager(self):
        expense_manager = self.env.user.has_group('sales_meet.group_expense_manager_user')
        if str(self.parent_id.work_email) == str(self.env.user.login) or \
                self.env.user.has_group('sales_meet.group_expense_manager_user') or self.env.uid == 1:
            self.sudo().write({'state': 'manager_approve','approve_date':date.today()})
        else:
            raise UserError("Only %s 's manager (%s) or Expense Manager can approve his \
                expenses" %(self.employee_id.name,self.employee_id.parent_id.name))
        
    
    
    def refuse_expenses(self, reason):
        if not  (str(self.parent_id.work_email) == str(self.env.user.login) \
                or  self.env.user.has_group('sales_meet.group_expense_manager_user')) \
                and self.env.uid != 1:

            raise UserError(_("Only Expense Managers can refuse expenses"))
        self.sudo().write({'state': 'cancel','reason':reason})
        for sheet in self:
            body = (_("Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : \
             </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (sheet.name, reason))
            sheet.sudo().message_post(body=body)

    @api.model
    def create(self, vals):
        result = super(HrExpenseSheetExtension, self).create(vals)
        manager_users = []
        for res in result:
            for rec in result.expense_line_ids:
                res.meeting_date = result.expense_line_ids.meeting_id.expense_date
                res.meeting_address = result.expense_line_ids.meeting_address
                res.expense_note = 'Meeting :  ' + result.expense_line_ids.meeting_id.name \
                                   + '\n' + 'Amount Allocated :  ' + str(rec.grade_amount) \
                          + '\n' + 'Amount Claimed   :  ' + str(rec.claimed_amount) \
                       + '\n' + ( ('Reference        :  ' + rec.reference) if rec.reference else '')
                if float(rec.grade_amount) != 0.0:
                    if rec.claimed_amount > rec.grade_amount:

                        parent_id = self.env['hr.employee'].sudo().search([('id', '=', res.employee_id.id)]).parent_id.id
                        parent_user_id = self.env['hr.employee'].sudo().search([('id', '=', res.employee_id.id)]).parent_id.user_id

                        res.parent_id = parent_id
                        manager_users.append(parent_user_id)
                        recepients = manager_users

                        main_id = result.id
                        expensename = result.name
                        employeename = result.employee_id.name
                        meetingvisit = result.expense_line_ids.meeting_id.name
                        grade_amount = result.expense_line_ids.grade_amount
                        claimed_amount = result.expense_line_ids.claimed_amount
                        reference = result.expense_line_ids.reference
                        company_id = result.company_id.id

                        self.sudo().mail_send(recepients , main_id, expensename , employeename , \
                            meetingvisit , grade_amount, claimed_amount , reference, company_id)


        return result



    
    def mail_send(self, recepients=[],main_id=False, expensename=False , employeename=False , 
        meetingvisit=False , grade_amount=False, claimed_amount=False , reference=False, company_id=False):
        email_from = 'expense@walplast.com'

        body = """<h3>Following are the details as Below Listed. </h3>
            <table>
              <tr><th style=" text-align: left;padding: 8px;">Description</td><td> : %s</td></tr>
              <tr><th style=" text-align: left;padding: 8px;">Employee</td><td> : %s</td></tr>
              <tr><th style=" text-align: left;padding: 8px;">Meeting</td><td> : %s</td></tr>
              <tr><th style=" text-align: left;padding: 8px;">Amount Allocated</td><td> : %s</td></tr>
              <tr><th style=" text-align: left;padding: 8px;">Amount Claimed</td><td> : %s</td></tr>
              <tr><th style=" text-align: left;padding: 8px;">Bill Reference</td><td> : %s</td></tr>
            </table>
            <br/><br/>

        """ % (expensename or '', employeename  or '', meetingvisit  or '' , \
            grade_amount  or '', claimed_amount  or '' , reference  or '' )

        subject = "[Approval] - %s 's Reimbursment for ( %s ) " % (employeename or '' ,expensename or '')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        for rec in recepients:
            approve_url = base_url + '/expense?%s' % (url_encode({
                    'model': self._name,
                    'meeting_id': main_id,
                    'res_id': rec.id,
                    'action': 'approve_expense_sheets_manager',
                }))
            reject_url = base_url + '/expense?%s' % (url_encode({
                    'model': self._name,
                    'meeting_id': main_id,
                    'res_id': rec.id,
                    'action': 'refuse_expenses',
                }))

            report_check = base_url + '/web#%s' % (url_encode({
                'model': self._name,
                'view_type': 'form',
                'id': main_id,
            }))

            full_body = body + """<br/>
            <table class="table" style="border-collapse: collapse; border-spacing: 0px;">
                <tbody>
                    <tr class="text-center">
                        <td>
                            <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                text-align: center; vertical-align: middle; cursor: pointer; 
                                white-space: nowrap; background-image: none; background-color: #337ab7; 
                                border: 1px solid #337ab7; margin-right: 10px;">Approve</a>
                        </td>
                        <td>
                            <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                text-align: center; vertical-align: middle; cursor: pointer; 
                                white-space: nowrap; background-image: none; background-color: #337ab7; 
                                border: 1px solid #337ab7; margin-right: 10px;">Reject</a>
                        </td>

                        <td>
                            <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                text-align: center; vertical-align: middle; cursor: pointer; 
                                white-space: nowrap; background-image: none; background-color: #337ab7; 
                                border: 1px solid #337ab7; margin-right: 10px;">Check Request</a>
                        </td>

                    </tr>
                </tbody>
            </table>
            """ % (approve_url, reject_url, report_check)

            approver_ids = self.env['hr.expense.wpconfig'].sudo().search([("company_id","=",company_id)])
            email_cc = []

            for approvers_config in approver_ids:
                for approver in approvers_config.expense_approver_one2many:
                    email_cc.append(approver.approver.email)

            email_cc_listToStr = ','.join([str(elem) for elem in email_cc])

            # print "-------------- Expense Email Sent to " , email_cc , email_cc_listToStr

            composed_mail = self.env['mail.mail'].sudo().create({
                    'model': self._name,
                    'res_id': main_id,
                    'email_from': email_from,
                    'email_to': rec.email,
                    'email_cc' : email_cc_listToStr,
                    'subject': subject,
                    'body_html': full_body,
                    'auto_delete': False,
                })
            composed_mail.sudo().send()
              


    
    def action_sheet_move_create(self):
        self.write({'state': 'post'})



class HrExpenseWpConfig(models.Model):
    _name = "hr.expense.wpconfig"
    _order= "id desc"

    @api.model
    def create(self, vals):
        result = super(HrExpenseWpConfig, self).create(vals)

        a = self.search([("company_id","=",result.company_id.id)])
        if len(a) >1:
            raise UserError(_('You can only create 1 Config Record per company'))
        else:
            result.name = result.company_id.short_name + "- Approvers"

        return result

    name = fields.Char(string = "Name" )
    company_id = fields.Many2one('res.company' , string = "Company")
    expense_approver_one2many = fields.One2many('hr.expense.approver','config_id',string="Expense Approver")

class HrExpenseApprover(models.Model):
    _name = "hr.expense.approver"
    _order= "sequence"

    config_id = fields.Many2one('hr.expense.wpconfig', string='Config', ondelete='cascade')
    approver = fields.Many2one('res.users', string='Approver', required=True)
    sequence = fields.Integer(string='Approver sequence')
