from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, Warning, ValidationError
from odoo.http import request
import re
# import date_converter
DATETIME_FORMAT = "%Y-%m-%d"

class Contracts(models.Model):
    _name = 'wp.contracts'

    # def compute_reminders(self):
    #     for rec in self:
    #         reminders = self.env['contract.reminder'].search([('contract_id','=',rec.id),('contract_id','!=',False)])
    #         rec.reminder_count = len(reminders)
    @api.constrains('contact_no')
    def contact_no_constraint(self):
        if self.contact_no and (len(self.contact_no) != 10 or not self.contact_no.isdigit()):
            # match = re.match('^[0-9]\d{10}$', self.contact_no)
            raise ValidationError('Contact No. can be 10 digit and 0-9 only')

    @api.constrains('consultant_contact_no')
    def consultant_contact_no_constraint(self):
        if self.consultant_contact_no and (len(self.consultant_contact_no) != 10 or not self.consultant_contact_no.isdigit()):
            raise ValidationError('Consultant Contact No. can be 10 digit and 0-9 only')

    @api.constrains('name')
    def limit_name(self):
        for rec in self:
            if rec.name and len(rec.name) > 10:
                raise UserError(_('More 10 words are not allowed for contract name!!'))

    def set_default_department(self):
        user = self.env.user
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        return employee.department_id.id

    
    def compute_department(self):
        for rec in self:
            if rec.user_id:
                rec.department_bool = True
                rec.department_id = rec.user_id.department_id.id
            else:
                rec.department_bool = False
                rec.department_id = False

    
    def set_default_spoc(self):
        user = self.env.user
        employee = self.env['hr.employee'].sudo().search([('user_id','=',user.id)],limit=1)
        return employee.id


    #IT Contract
    category = fields.Many2one('wp.contract.categories',"Category")
    name = fields.Char("Contract Name")
    product_key = fields.Char("Product Key")
    no_of_license = fields.Integer("No. of Licenses")
    company_id = fields.Many2one('res.company',"Company",default=lambda self: self.env.company)
    vendor_id = fields.Many2one('res.partner',"Vendor")
    supplier_id = fields.Many2one('contract.supplier',"Supplier")
    po_cost = fields.Float("PO Cost")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    reminder_days = fields.Integer("Reminder In Days")
    desc = fields.Text("Description")
    upload_file = fields.Many2many('ir.attachment','contract_attachment_rel',string="Upload File")

    contract_type = fields.Selection(selection=[('it_contract',"IT Contract"),('non_it_contract',"Non-IT Contract")])
    status = fields.Selection([('to_be_renewed',"To be renewed"),('renewed',"Renewed"),('expired',"Expired")],default='to_be_renewed')
    is_expired = fields.Boolean("Is Expired")
    is_renewed = fields.Boolean("Is Renewed")
    closed_remarks = fields.Char("Remarks (Closed)")
    renewed_remarks = fields.Char("Remarks (Renewed)")
    # reminder_count = fields.Integer(compute=compute_reminders)
    first_followers = fields.Many2many('hr.employee','employee_first_follow_rel',string="First Followers")
    second_followers = fields.Many2many('hr.employee','employee_second_follow_rel',string="Second Followers")
    # trigger_reminder_before = fields.Integer("Trigger Reminder Before (In Days)")
    show_product_key = fields.Boolean(default='False')
    department_bool = fields.Boolean(compute=compute_department)
    department_id = fields.Many2one('hr.department',"Default Department",default=set_default_department)
    department_id_1 = fields.Many2one('hr.department',"Department")
    user_id = fields.Many2one('res.users',"User",default=lambda self: self.env.user)

    #Non-IT Contract
    # sr_no = fields.Char("Sr. No")
    location = fields.Many2one('wp.locations',"Location")
    document_no = fields.Char("Document No.")
    document_type = fields.Many2one('contract.document.type',"Document Type")
    act_of_document = fields.Char("Document comes under the act")
    desc_of_document = fields.Char("Description of Document")
    license_registration_no = fields.Char("License/Registration No.")
    document_issued_on = fields.Date("Document issued on ")
    # valid_from = fields.Date("Valid From")
    # valid_to = fields.Date("Valid To")
    validity = fields.Integer("No of years Validity")
    renewal_reminder = fields.Date("Document Renewal Reminder")
    document_hp = fields.Char("HP Mentioned in document")
    no_of_employees = fields.Integer("No. of employees in document")
    spoc_name = fields.Many2one('hr.employee',"SPOC's Name",default=set_default_spoc)
    govt_approver = fields.Char("Govt. Approving authority")
    contact_person = fields.Char("Contact Person name")
    contact_no = fields.Char("Contact No.")
    consultant_name = fields.Char("Consultant Name")
    consultant_contact_no = fields.Char("Consultant Contact No.")
    official_fees_paid = fields.Float("Official Fees Paid ")
    fees_paid_on_dated = fields.Date("Fees paid on dated")
    other_expenses_paid = fields.Char("Other expenses paid")
    expenses_paid_dated = fields.Date("Paid on dated")
    documents = fields.Many2many('ir.attachment','document_contract_rel',string="Documents")
    
    @api.onchange('department_id_1')
    def onchange_department_id_1(self):
        return {'domain': {'department_id_1': ['|',('id', '=', self.env.user.department_id.id),('id','in',self.env.user.allowed_department_ids.ids)]}}

    def set_to_expired(self):
        # self.is_expired = True
        # self.is_renewed = False
        self.status = 'expired'

    def set_to_renewed(self):
        # self.is_renewed = True
        # self.is_expired = False
        self.status = 'renewed'

    def display_product_key(self):
        raise UserError(_("Product key : %s" % self.product_key))

    def _send_contract_reminder(self):
        ##IT Contract###
        # users = self.env['res.users'].sudo().search([('active', '=', True)])
        # for user in users:
        #     message = """Hello, <br/><p> Please refer to the contract expiration details given below:</p><br/>
        #                                                 <table class="table">
        #
        #                                                     <tr class="text-center">
        #                                                         <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Contract for</th>
        #                                                         <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Expiring On</th>
        #                                                     </tr>
        #                                                     """
        #     first_follow_message = """"""
        #     second_follow_message = """"""
        #     send_first_reminder = False
        #     send_second_reminder = False
        #     contracts = self.env['wp.contracts'].sudo().search(
        #         [('end_date', '!=', False), ('contract_type', '=', 'it_contract')])
        #     employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id), ('active', '=', True)],
        #                                                      limit=1)
        #     for rec in contracts:
        #         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        #         base_url += '/web#id=%d&view_type=form&model=%s' % (rec.id, rec._name)
        #
        #         if rec.status == 'to_be_renewed' and (
        #                 rec.second_followers != False and employee.id in rec.second_followers.ids):
        #             today = datetime
        #             end_date = datetime.strptime(rec.end_date, DATETIME_FORMAT)
        #             first_rem = end_date + timedelta(days=-15)
        #             second_rem = end_date + timedelta(days=-7)
        #             third_rem = end_date + timedelta(days=-3)
        #             fourth_rem = end_date + timedelta(days=-1)
        #
        #             if rec.end_date and (
        #                     today.strftime(DATETIME_FORMAT) == first_rem.strftime(DATETIME_FORMAT) or today.strftime(
        #                 DATETIME_FORMAT) == second_rem.strftime(DATETIME_FORMAT)
        #                     or today.strftime(DATETIME_FORMAT) == third_rem.strftime(DATETIME_FORMAT) or today.strftime(
        #                 DATETIME_FORMAT) == fourth_rem.strftime(DATETIME_FORMAT)):
        #                 send_second_reminder = True
        #                 second_follow_message = message + """<tr class="text-center">
        #                                 <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;"><a style="text-decoration:none;" href='""" + base_url + """'>""" \
        #                                         + rec.name + """</a></td><td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">""" + rec.end_date + """</td></tr>"""
        #     first_follow_message += """</table>"""
        #     second_follow_message += """</table>"""
        #
        #     if send_second_reminder == True:
        #         composed_mail = self.env['mail.mail'].sudo().create({
        #             'email_from': 'it@walplast.com',
        #             'email_to': user.login,
        #             'subject': "IT Contract Renewal Reminder",
        #             'body_html': second_follow_message
        #         })
        #         composed_mail.send()
        ### Non-IT contract###
        # for user in users:

        due_date_msg = """Hi, <br/><p>Below contracts are about to expire:</p><br/>
                                                    <table class="table" style="font-size: 12px;">
                                                        <tr class="text-center">
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Contract</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document #</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document Type</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Company</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Location</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid From</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid To</th>
                                                        </tr> """
        first_rem_msg = """Hi, <br/><p>Below contracts are about to expire:</p><br/>
                                                    <table class="table" style="font-size: 12px;">

                                                        <tr class="text-center">
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Contract</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document #</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document Type</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Company</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Location</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid From</th>
                                                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid To</th>
                                                        </tr> """
        second_rem_msg = """Hi, <br/><p>Below contracts are about to expire:</p><br/>
                                                                <table class="table" style="font-size: 12px;">
                                                                    <tr class="text-center">
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Contract</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document #</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document Type</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Company</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Location</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid From</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid To</th>
                                                                    </tr> """
        third_rem_msg = """Hi, <br/><p> Below contracts are about to expire:</p><br/>
                                                                <table class="table" style="font-size: 12px;">
                                                                    <tr class="text-center">
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Contract</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document #</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document Type</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Company</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Location</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid From</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid To</th>
                                                                    </tr> """
        fourth_rem_msg = """Hi, <br/><p> Below contracts are about to expire:</p><br/>
                                                                <table class="table" style="font-size: 12px;">
                                                                    <tr class="text-center">
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Contract</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document #</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document Type</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Company</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Location</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid From</th>
                                                                        <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Valid To</th>
                                                                    </tr> """
        due_date_rem = False
        first_inter_rem = False
        second_inter_rem = False
        third_inter_rem = False
        fourth_inter_rem = False

        due_date_sub = "Contract Renewal Reminder"
        first_rem_sub = "Contract Renewal Reminder Number 2"
        second_rem_sub = "Contract Renewal Reminder Number 3"
        third_rem_sub = "Contract Renewal Reminder Number 4"
        fourth_rem_sub = "Contract Renewal Reminder Number 5"

        contracts = self.env['wp.contracts'].sudo().search(
            [('end_date', '!=', False), ('contract_type', '=', 'non_it_contract')])

        for rec in contracts:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/web#id=%d&view_type=form&model=%s' % (rec.id, rec._name)
            if rec.status == 'to_be_renewed':
                today = datetime.today().date()
                renewal = datetime.strptime(str(rec.renewal_reminder), DATETIME_FORMAT)
# Content For Due date reminder
                if rec.renewal_reminder and (today.strftime(DATETIME_FORMAT) == renewal.strftime(DATETIME_FORMAT)):
                    due_date_email_to = ""
                    for follower in rec.first_followers:
                        due_date_email_to += str(follower.user_id.login) + ","
                    due_date_rem = True
                    due_date_msg = due_date_msg + """<tr class="text-center">
                                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;"><a style="text-decoration:none;" href=""" + base_url + """> """+ rec.name+ """</a></td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.document_no +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.document_type.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.company_id.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.location.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+str(rec.start_date) +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">""" + str(rec.end_date) + """</td></tr>"""

            if rec.status == 'to_be_renewed':
                today = datetime.today()
                end_date = datetime.strptime(str(rec.end_date), DATETIME_FORMAT)
                first_rem = end_date + timedelta(days=-15)
                second_rem = end_date + timedelta(days=-7)
                third_rem = end_date + timedelta(days=-3)
                fourth_rem = end_date + timedelta(days=-1)
# Content For 1st, 2nd, 3rd and 4th reminder

                if rec.end_date and (today.strftime(DATETIME_FORMAT) == first_rem.strftime(DATETIME_FORMAT)):
                    first_rem_email_to = ""
                    for follower in rec.first_followers:
                        first_rem_email_to += str(follower.user_id.login) + ","
                    first_inter_rem = True
                    first_rem_msg += """<tr class="text-center">
                                     <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;"><a style="text-decoration:none;" href=""" + base_url + """> """+ rec.name+ """</a></td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.document_no +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.document_type.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.company_id.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.location.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+str(rec.start_date) +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">""" + str(rec.end_date) + """</td></tr>"""

                if rec.end_date and today.strftime(DATETIME_FORMAT) == second_rem.strftime(DATETIME_FORMAT):
                    second_rem_email_to = ""
                    second_rem_email_cc = ""
                    for first_follower in rec.first_followers:
                        second_rem_email_to += str(first_follower.user_id.login) + ","

                    for second_follower in rec.second_followers:
                        second_rem_email_cc += str(second_follower.user_id.login) + ","
                    second_inter_rem = True
                    second_rem_msg += """<tr class="text-center">
                                     <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;"><a style="text-decoration:none;" href=""" + base_url + """> """+ rec.name+ """</a></td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.document_no +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.document_type.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.company_id.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+rec.location.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+str(rec.start_date) +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">""" + str(rec.end_date) + """</td></tr>"""

                if rec.end_date and today.strftime(DATETIME_FORMAT) == third_rem.strftime(DATETIME_FORMAT):
                    third_rem_email_to = ""
                    third_rem_email_cc = ""
                    for first_follower in rec.first_followers:
                        third_rem_email_cc += str(first_follower.user_id.login) + ","

                    for second_follower in rec.second_followers:
                        third_rem_email_to += str(second_follower.user_id.login) + ","

                    third_inter_rem = True
                    third_rem_msg += """<tr class="text-center">
                                     <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;"><a style="text-decoration:none;" href=""" + base_url + """> """+ rec.name+ """</a></td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.document_no +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.document_type.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.company_id.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.location.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ str(rec.start_date) +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">""" + str(rec.end_date) + """</td></tr>"""

                if rec.end_date and today.strftime(DATETIME_FORMAT) == fourth_rem.strftime(DATETIME_FORMAT):
                    fourth_rem_email_to = ""
                    for first_follower in rec.first_followers:
                        fourth_rem_email_to += str(first_follower.user_id.login) + ","

                    for second_follower in rec.second_followers:
                        fourth_rem_email_to += str(second_follower.user_id.login) + ","

                    fourth_inter_rem = True
                    fourth_rem_msg += """<tr class="text-center">
                                     <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;"><a style="text-decoration:none;" href=""" + base_url + """> """+ rec.name+ """</a></td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.document_no +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.document_type.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.company_id.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ rec.location.name +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">"""+ str(rec.start_date) +"""</td>
                                           <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">""" + str(rec.end_date) + """</td></tr>"""



        due_date_msg += """ </table> <br/><p>You can set the contract to Expire or Renew the same and create a new contract</p>
        <br/><p><b>Do not reply to this email as it is an unmonitored email box.</b></p><br/>Thank you."""

        first_rem_msg += """</table> <br/><p>You can set the contract to Expire or Renew the same and create a new contract</p>
        <br/><p> <b>Do not reply to this email as it is an unmonitored email box.</b></p><br/>Thank you."""

        second_rem_msg += """</table> <br/><p>You can set the contract to Expire or Renew the same and create a new contract</p>
        <br/><p> <b>Do not reply to this email as it is an unmonitored email box.</b></p><br/>Thank you."""

        third_rem_msg += """</table> <br/><p>You can set the contract to Expire or Renew the same and create a new contract</p>
        <br/><p><b>Do not reply to this email as it is an unmonitored email box.</b></p><br/>Thank you."""

        fourth_rem_msg += """</table> <br/><p>You can set the contract to Expire or Renew the same and create a new contract</p>
        <br/><p> <b>Do not reply to this email as it is an unmonitored email box.</b></p><br/>Thank you."""


        if due_date_rem == True:
            due_composed_mail = self.env['mail.mail'].sudo().create({
                'email_from': 'it@walplast.com',
                'email_to': str(due_date_email_to).split()[0],
                'subject': due_date_sub,
                'body_html': due_date_msg,
            })
            due_composed_mail.send()

        if first_inter_rem == True:
            first_composed_mail = self.env['mail.mail'].sudo().create({
                'email_from': 'it@walplast.com',
                'email_to': str(first_rem_email_to).split()[0],
                'subject': first_rem_sub,
                'body_html': first_rem_msg,
            })
            first_composed_mail.send()

        if second_inter_rem == True:
            second_composed_mail = self.env['mail.mail'].sudo().create({
                'email_from': 'it@walplast.com',
                'email_to': str(second_rem_email_to).split()[0],
                'email_cc': str(second_rem_email_cc).split()[0],
                'subject': second_rem_sub,
                'body_html': second_rem_msg,
            })
            second_composed_mail.send()

        if third_inter_rem == True:
            third_composed_mail = self.env['mail.mail'].sudo().create({
                'email_from': 'it@walplast.com',
                'email_to': str(third_rem_email_to).split()[0],
                'email_cc': str(third_rem_email_cc).split()[0],
                'subject': third_rem_sub,
                'body_html': third_rem_msg,
            })
            third_composed_mail.send()

        if fourth_inter_rem == True:
            fourth_composed_mail = self.env['mail.mail'].sudo().create({
                'email_from': 'it@walplast.com',
                'email_to': str(fourth_rem_email_to).split()[0],
                'subject': fourth_rem_sub,
                'body_html': fourth_rem_msg,
            })
            fourth_composed_mail.send()



