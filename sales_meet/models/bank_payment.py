#!/usr/bin/env bash
from datetime import datetime, timedelta, date
import dateutil.parser
from odoo import tools, api, fields, models, _, tools, registry, SUPERUSER_ID
import logging
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
import psycopg2
import csv
from io import BytesIO, StringIO
import xlwt
import base64
from collections import Counter
import requests
from werkzeug.urls import url_encode
import os
import math

from zeep.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# idempiere_url="https://erpnew.wmvd.live/ADInterface/services/compositeInterface?wsdl"
headers = {'content-type': 'text/xml'}
todaydate = "{:%d-%b-%y}".format(datetime.now())

DATE_FORMAT = "%Y-%m-%d"

header_fields = ['ReversalDate',
                 'AD_Org_ID[Name]',
                 'C_BankAccount_ID[Value]',
                 'C_DocType_ID[Name]',
                 'IsReceipt',
                 'DateTrx',
                 'DateAcct',
                 'Description',
                 'C_BPartner_ID[Value]',
                 'PayAmt',
                 'C_Currency_ID',
                 'C_ConversionType_ID[Value]',
                 'DiscountAmt',
                 'WriteOffAmt',
                 'IsOverUnderPayment',
                 'OverUnderAmt',
                 'TenderType',
                 'IsOnline',
                 'CreditCardType',
                 'TrxType',
                 'CreditCardExpMM',
                 'CreditCardExpYY',
                 'TaxAmt',
                 'IsVoided',
                 'C_PaymentAllocate>AD_Org_ID[Name]',
                 'C_PaymentAllocate>C_Payment_ID[DocumentNo]',
                 'C_PaymentAllocate>IsActive',
                 'C_PaymentAllocate>C_Invoice_ID[DocumentNo]',
                 'C_PaymentAllocate>Amount',
                 'C_PaymentAllocate>DiscountAmt',
                 'C_PaymentAllocate>WriteOffAmt',
                 'C_PaymentAllocate>OverUnderAmt'
                 ]

header_fields3 = [
    'Sr No.',
    'Client',
    'Org',
    'Date Account',
    'DocumentNo',
    'Code',
    'Beneficiary',
    'Total',
    'Allocated Amt',
    'Unallocated Amt',
    'Due Days',
]

TRANSACTION_TYPE = [('R', 'RTGS'), ('N', 'NEFT'),
                    ('I', 'Funds Transfer'), ('D', 'Demand Draft')]
transaction_type = {'R': 'RTGS', 'N': 'NEFT', 'I': 'Funds Transfer', 'D': 'Demand Draft'}
STATE = [('draft', 'Draft'), ('approved', 'Approved'),
         ('rejected', 'Rejected'), ('hold', 'Holded')]

main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1, vert centre, horiz left; \
        borders: bottom thick, top thick, left thick, right thick')
sp_style = xlwt.easyxf('font: bold on, height 350;')
header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz center, vertical center; \
    borders: bottom thin, top thin, left thin, right thin; \
    pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
base_style_gray = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; \
    pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
base_style_yellow = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; \
    pattern: pattern fine_dots, fore_color white, back_color yellow;')


class bank_payment(models.Model):
    _name = "bank.payment"
    _description = " Payment to Bank"
    _inherit = 'mail.thread'
    _order = 'id desc'

    def _compute_can_edit_name(self):
        self.can_edit_name = self.env.user.has_group('sales_meet.group_sales_meet_hidden')

    def _get_config(self):
        config = self.env['external.db.configuration'].search([('state', '=', 'connected')], limit=1)
        if config:
            config_id = config.id
        else:
            config = self.env['external.db.configuration'].search([('id', '!=', 0)], limit=1)
            config_id = config.id
        return config_id

    def _amount_calc(self, condition=False, amount=False):
        if condition == 'deduct':
            self.amount_total -= amount
        elif condition == 'add':
            self.amount_total += amount

    @api.depends('invoice_filter_one2many.unallocated')
    @api.onchange('invoice_filter_one2many.unallocated')
    def _calculate_all(self):
        for order in self:
            total_unallocated = 0.0
            for line in order.invoice_filter_one2many:
                total_unallocated += line.unallocated
            order.update({'amount_filtered_total': total_unallocated, })

    def _default_ad_org_id(self):
        org = self.env['org.master'].sudo().search([('company_id', '=', self.env.company.id),
                                                    ('default', '=', True)], limit=1)
        if not org: return False
        return org.id

    def _default_bank(self):
        bank = self.env['erp.bank.master'].sudo().search([('company_id', '=', self.env.company.id),
                                                          ('default', '=', True)], limit=1)
        if not bank: return False
        return bank.id

    # def _get_owner(self):
    #     if self.env.user.has_group('sales_meet.group_bank_payment_manager'):
    #         domain = [('company_id', '=', self.env.user.company_id.id)]
    #     else:
    #         domain = [('id', 'in', [usr.id for usr in self.env.user.owner_ids]),
    #                   ('company_id', '=', self.env.user.company_id.id)]
    #     return domain

    def _get_owner(self):
        domain = []
        if not self.env.user.has_group('sales_meet.group_bank_payment_manager'):
            domain = [('id', 'in', [usr.id for usr in self.env.user.owner_ids])]
        return domain

    name = fields.Char('Name', store=True)
    db_name = fields.Char('DB Name')
    config_id = fields.Many2one('external.db.configuration', string='Database', default=_get_config)
    note = fields.Text('Text', copy=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('generated_invoice', 'Invoice Generated'),
                              ('generated_invoice_template', 'Template Generated'),
                              ('submitted_to_manager', 'Submitted to Manager'),
                              ('approved', 'Approved'),
                              ('validated', 'Validated'),
                              ('refused', 'Refused'),
                              ('erp_posted', 'Posted'),
                              ('generated_payment', 'Payment Generated'),
                              ('file_generated', 'File Generated'),
                              ('submitted_to_bank', 'Submitted to Bank')
                              ], string='Status', track_visibility='onchange', default='draft')

    transaction_type = fields.Selection(TRANSACTION_TYPE, string='Transaction Type')
    requester = fields.Char('Requester')
    payment_lines_one2many = fields.One2many('bank.payment.lines', 'payment_id', string="Payments Details")
    payment_selected_one2many = fields.One2many('bank.payment.selected', 'selected_payment_id',
                                                string="Selected Payments Details")

    invoice_lines_one2many = fields.One2many('bank.invoice.lines', 'invoice_id', string="Invoice Details")
    invoice_selected_one2many = fields.One2many('bank.invoice.selected', 'invoice_selected_id',
                                                string="Selected Invoice")
    invoice_filter_one2many = fields.One2many('bank.invoice.filter', 'invoice_filter_id',
                                              string="Selected Invoice", order='beneficiary_name asc, value_date desc')
    invoice_summary_one2many = fields.One2many('bank.invoice.summary', 'vendor_summary_id',
                                               string="Vendor Summary Invoice")

    date = fields.Date(string="Date", default=lambda self: fields.Datetime.now())
    employee_id = fields.Many2one('hr.employee', string="Employee")
    completed = fields.Boolean("Completed", copy=False)
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company.id)
    # ad_org_id = fields.Many2one('org.master', string='Organisation',
    #                             domain="[('company_id','=',company_id)]", default=_default_ad_org_id)
    ad_org_id = fields.Many2one('org.master', string='Organisation',
                                domain=lambda self: [("company_id", "in", self.env.user.company_ids.ids)],
                                default=_default_ad_org_id)

    c_bpartner_id = fields.Char("Partner ID")
    ad_client_id = fields.Char('Client ID')
    user_id = fields.Many2one('res.users', string='User', index=True, default=lambda self: self.env.user)

    delegate_user_id = fields.Many2many('res.users', string='Delegate To')
    custgroup = fields.Char(string="Group")
    hr_payment_data = fields.Char('Rep Name')
    file_name = fields.Binary('Expense Report', readonly=True, copy=False)

    output_file = fields.Binary('Prepared file', filters='.xls', attachment=True, copy=False)
    export_file = fields.Char(string="Export", copy=False)

    pmt_output_file = fields.Binary('Prepared file', filters='.xls', attachment=True, copy=False)
    pmt_export_file = fields.Char(string="Export", copy=False)

    partner_name = fields.Char('Partner')
    hr_payment_data2 = fields.Char('Rep Name2')
    file_name2 = fields.Binary('Due Invoices Report', copy=False)
    inv_rep_bool = fields.Boolean('Inv Rep Generated', default=False, copy=False)
    condition = fields.Selection([
        ('invoice', 'Invoice'),
        ('payment', 'Payment')], string='Condition')
    # erp_bank_id = fields.Many2one('erp.bank.master', string='Bank Account',
    #                               domain="[('company_id','=',company_id)]", default=_default_bank)
    erp_bank_id = fields.Many2one('erp.bank.master', string='Bank Account',
                                  domain=lambda self: [("company_id", "in", self.env.user.company_ids.ids)],
                                  default=_default_bank)

    # default=lambda self: self.env['erp.bank.master'].search([('default', '=', True),
    # ('company_id', '=', self.env.user.company_id.id)], limit=1)
    filter_rep_bool = fields.Boolean('Filter Rep Generated', default=False, copy=False)

    amount_total = fields.Float(string='Total', store=True)
    amount_filtered_total = fields.Float(string='Filtered Total', readonly=True,
                                         compute='_calculate_all', digits=(16, 3), store=True)

    can_edit_name = fields.Boolean(compute='_compute_can_edit_name')
    owner_id = fields.Many2one('erp.representative.approver', string='Owner', domain=_get_owner)
    server_instance = fields.Selection([
        ('Demo', 'Demo'),
        ('Live', 'Live')], string='Server Instance')

    realfilename = fields.Char('File Name')
    bank_upload_date = fields.Date(string="Bank Upload Date", default=lambda self: fields.Datetime.now())

    submitted_to_manager = fields.Datetime(string="Submitted to Manager Date")
    approved_by_manager = fields.Datetime(string="Approved By Manager Date")
    rejected_by_manager = fields.Datetime(string="Rejected By Manager Date")
    payment_processed_date = fields.Datetime(string="Payment Processed Date")
    paymnt_report = fields.Binary("Payment Report")
    report_filename = fields.Char()
    bank = fields.Selection([('hdfc', "HDFC"), ('hsbc', "HSBC")])
    accounting_date = fields.Date("Accounting Date", default=lambda self: fields.Datetime.now())
    approval_note = fields.Text("Approval Note")
    api_resp = fields.Text('API Response')

    def unlink(self):
        for order in self:
            if order.state in (
                    'approved', 'validated', 'erp_posted', 'refused', 'submitted_to_bank', 'submitted_to_manager'):
                if self.env.uid != 1:
                    raise UserError(
                        _('Records in Submitted to manager/Approved/ Rejected/ Posted state cannot be deleted'))
        return super(bank_payment, self).unlink()

    @api.model_create_multi
    def create(self, vals):
        result = super(bank_payment, self).create(vals)
        for res in result.invoice_filter_one2many:
            if res.unallocated > (res.unallocated2 + res.tds_amount) and not res.discard_tds:
                raise ValidationError(" Unallocated Amount cannot be greater in line %s " % (res.beneficiary_name))
        return result

    def write(self, vals):
        result = super(bank_payment, self).write(vals)
        for res in self.invoice_filter_one2many:
            if res.unallocated and not res.discard_tds:
                if res.unallocated > (res.unallocated2 + res.tds_amount):
                    raise ValidationError(" Unallocated Amount cannot be greater")
        return result

    def refresh_form(self):
        return True

    def name_creation(self):
        name = ''
        if self.bank == 'hsbc':
            seq = self.env['ir.sequence'].sudo().next_by_code('bank.payment.hsbc') or '/'
            self.name = name = 'HSBC_' + str(self.company_id.short_name) + '_' + str(seq)
        else:
            seq = self.env['ir.sequence'].sudo().next_by_code('bank.payment.hdfc') or '/'
            self.name = name = 'BP/' + str(self.company_id.short_name) + '/' + str(seq)
        return name

    def select_all(self):
        filter_lines = []
        filtered_lines = [x.documentno for x in self.invoice_filter_one2many]

        for res in self.invoice_selected_one2many:
            if res.documentno not in filtered_lines:
                filter_lines.append((0, 0, {
                    'invoice_filter_id': self.id,
                    'documentno': res.documentno,
                    'value_date': res.value_date,
                    'transaction_amount': res.transaction_amount,
                    'beneficiary_name': res.beneficiary_name,
                    'invoiceno': res.invoiceno,
                    'totalamt': abs(res.totalamt),
                    'allocatedamt': abs(res.allocatedamt),
                    'unallocated': abs(res.unallocated + res.tds_amount),
                    'unallocated2': abs(res.unallocated),
                    'payment_term': res.payment_term,
                    'duedays': res.duedays,
                    'term_duedays': res.term_duedays,
                    'customercode': res.customercode,
                    'ad_org': res.ad_org,
                    'selected_id': res.invoice_selected_id.id,
                    'c_bpartner_id': res.c_bpartner_id,
                    'ad_org_id': res.ad_org_id.id,
                    'c_invoice_id': res.c_invoice_id,
                    'discard_tds': res.discard_tds,
                    'tds_amount': res.tds_amount,
                    'company_id': self.company_id.id,
                    'state': 'draft',
                }))

        self.invoice_filter_one2many = filter_lines
        for res in self.invoice_filter_one2many:
            res.name = 'FI/' + str(res.id)
        self.invoice_selected_one2many.unlink()

    def sync_selected_invoices(self):
        self.invoice_selected_one2many.unlink()
        selected_lines = []
        doc_nos = []
        if self.partner_name:
            for rec in self.invoice_selected_one2many:
                if self.partner_name == rec.beneficiary_name:
                    raise UserError(" Partner already selected")
                else:
                    continue

            for res in self.invoice_lines_one2many:
                if self.partner_name == res.beneficiary_name:
                    if res.documentno not in doc_nos:
                        doc_nos.append(res.documentno)
                        selected_lines.append((0, 0, {
                            'invoice_selected_id': self.id,
                            'documentno': res.documentno,
                            'value_date': res.value_date,
                            'transaction_amount': res.transaction_amount,
                            'beneficiary_name': res.beneficiary_name,
                            'invoiceno': res.invoiceno,
                            'totalamt': res.totalamt,
                            'allocatedamt': res.allocatedamt,
                            'unallocated': res.unallocated,
                            'payment_term': res.payment_term,
                            'duedays': res.duedays,
                            'term_duedays': res.term_duedays,
                            'customercode': res.customercode,
                            'ad_org': res.ad_org,
                            'c_bpartner_id': res.c_bpartner_id,
                            'c_invoice_id': res.c_invoice_id,
                            'ad_org_id': res.ad_org_id.id,
                            'discard_tds': res.discard_tds,
                            'desc': res.desc,
                            'tds_amount': res.tds_amount
                        }))

            self.invoice_selected_one2many = selected_lines

        else:
            raise UserError(" Partner Not Selected")

        self.partner_name = ''
        self.amount_total = 0.0

    def sync_invoices(self):
        conn_pg = None
        invoice_lines = []

        if not self.config_id:
            raise UserError(" DB Connection not set / Disconnected ")

        else:
            try:
                conn_pg = psycopg2.connect(dbname=self.config_id.database_name, user=self.config_id.username,
                                           password=self.config_id.password, host=self.config_id.ip_address,
                                           port=self.config_id.port)
                pg_cursor = conn_pg.cursor()

                ad_client_id = self.company_id.ad_client_id

                if self.owner_id:
                    salesrep_id = self.owner_id.salesrep_id
                    salesrep_name = self.env['res.users'].sudo().search([('id', '=', self.owner_id.owner_id.id)]).name
                    if (salesrep_id and salesrep_id != "-") or salesrep_name:
                        pg_cursor.execute("select * from adempiere.due_inv_for_pmt_27092023 where \
                                            dateacct > '2020-03-31' and ad_client_id=%s and SalesRep_ID=%s",
                                          [self.company_id.ad_client_id,
                                           salesrep_id]) if salesrep_id and salesrep_id != "-" else pg_cursor.execute("select * from adempiere.due_inv_for_pmt_27092023 where \
                                                                            dateacct > '2020-03-31' and ad_client_id=%s and salesrepname=%s",
                                                                                                                      [
                                                                                                                          self.company_id.ad_client_id,
                                                                                                                          salesrep_name])
                    else:
                        pg_cursor.execute(
                            "select * from adempiere.due_inv_for_pmt_27092023 where dateacct > '2020-03-31' and  ad_client_id=%s",
                            [self.company_id.ad_client_id])

                else:
                    pg_cursor.execute(
                        "select * from adempiere.due_inv_for_pmt_27092023 where dateacct > '2020-03-31' and  ad_client_id=%s ",
                        [self.company_id.ad_client_id])

                entry_id = pg_cursor.fetchall()

                if entry_id == []:
                    raise UserError(" No Records Found ")

                for record in entry_id:
                    check_list = self.env['vendor.config'].sudo().search(
                        [('operation', '=', 'add_tds'), ('is_active', '=', True)])
                    beneficiary_name = str(record[9].encode('ascii', 'ignore'))
                    total_amt = abs(record[11])
                    tds_amount = 0
                    discard_tds = False
                    for rec in check_list:
                        if rec.based_on == 'id_based':
                            if str(rec.c_bpartner_id) == (str(record[8]).split('.'))[0]:
                                discard_tds = True
                                total_amt += abs(record[22]) if record[22] else 0.0
                                total_amt = total_amt
                                tds_amount = abs(record[22] or 0.0)
                        else:
                            if rec.name in beneficiary_name:
                                discard_tds = True
                                total_amt += abs(record[22]) if record[22] else 0.0
                                total_amt = total_amt
                                tds_amount = abs(record[22] or 0.0)
                    # raise ValidationError(_(record))
                    due_day = int(record[20])
                    # raise ValidationError(_(type(due_day)))
                    due_date = datetime.strptime(str(record[4]), DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(
                        days=due_day)
                    over_due_days = (datetime.today() - due_date).days
                    invoice_lines.append((0, 0, {
                        'invoice_id': self.id,
                        'ad_org': record[1],
                        'documentno': record[2],
                        'desc': record[3],
                        'value_date': record[4],
                        'invoiceno': record[5],
                        'c_bpartner_id': record[8],
                        'beneficiary_name': record[9],
                        'customercode': record[10],
                        'transaction_amount': total_amt,
                        'totalamt': total_amt,
                        'allocatedamt': record[12],
                        'unallocated': abs(record[13]),
                        'duedays': record[14],
                        'term_duedays': over_due_days,
                        'payment_term': record[19],
                        'c_invoice_id': record[16],
                        'tds_amount': tds_amount,
                        'discard_tds': discard_tds,
                        'ad_org_id': self.ad_org_id.id,
                    }))

                self.invoice_lines_one2many = invoice_lines
                self.state = 'generated_invoice'
                seq = self.env['ir.sequence'].sudo().next_by_code('bank.payment.invoice') or '/'
                self.name = 'DI/' + str(self.company_id.short_name) + '/' + str(seq)

            except psycopg2.DatabaseError as e:
                raise ValidationError("%s" % e)
                # if conn_pg: conn_pg.rollback()
                # print
                # '#-------------------Except ---Error %s' % e

            finally:
                if conn_pg: conn_pg.close()
                print
                "#--------------Select ----Finally----------------------#"

    # Commented due to TDS concept added in this function with new view used to fetch invoice data in above function
    # 
    # def sync_invoices(self):
    #     conn_pg = None
    #     invoice_lines = []
    #
    #     if not self.config_id:
    #         raise UserError(" DB Connection not set / Disconnected ")
    #
    #     else:
    #         try:
    #             print("#-------------Select --TRY----------------------#")
    #             conn_pg = psycopg2.connect(dbname=self.config_id.database_name, user=self.config_id.username,
    #                                        password=self.config_id.password, host=self.config_id.ip_address,
    #                                        port=self.config_id.port)
    #             pg_cursor = conn_pg.cursor()
    #
    #             ad_client_id = self.company_id.ad_client_id
    #
    #             if self.owner_id:
    #                 salesrep_id = self.owner_id.salesrep_id
    #                 salesrep_name = self.env['res.users'].sudo().search([('id', '=', self.owner_id.owner_id.id)]).name
    #                 if salesrep_id and salesrep_id != "-":
    #                     pg_cursor.execute("select * from adempiere.due_invoice_payment_process where \
    #                                                                       dateacct > '2020-03-31' and ad_client_id=%s and SalesRep_ID=%s",[self.company_id.ad_client_id, salesrep_id])
    #                 elif salesrep_name:
    #                     pg_cursor.execute("select * from adempiere.due_invoice_payment_process where \
    #                                                                 dateacct > '2020-03-31' and ad_client_id=%s and salesrepname=%s",
    #                                       [self.company_id.ad_client_id, salesrep_name])
    #                 else:
    #                     pg_cursor.execute("select * from adempiere.due_invoice_payment_process where dateacct > '2020-03-31' and  ad_client_id=%s",
    #                                       [self.company_id.ad_client_id])
    #
    #             else:
    #                 pg_cursor.execute("select * from adempiere.due_invoice_payment_process where dateacct > '2020-03-31' and  ad_client_id=%s ",
    #                                   [self.company_id.ad_client_id])
    #
    #             entry_id = pg_cursor.fetchall()
    #
    #             if entry_id == []:
    #                 raise UserError(" No Records Found ")
    #
    #             for record in entry_id:
    #                 # payment_term = record[18]
    #                 # inv_date = datetime.strptime(record[3], tools.DEFAULT_SERVER_DATETIME_FORMAT)
    #                 # due_date = inv_date + timedelta(days=int(payment_term))
    #                 # today= datetime.today()
    #                 # if today >= due_date - timedelta(days=3):
    #                 # user_ids = self.env['res.users'].sudo().search([("login", "=", record[11])])
    #                 # invoice_line_exist = self.env['bank.invoice.lines'].sudo().search(['|', ('invoiceno', '=', record[4]), ('documentno', '=', record[2])])
    #                 # if not invoice_line_exist:
    #                 invoice_lines.append((0, 0, {
    #                     'invoice_id': self.id,
    #                     'ad_org': record[1],
    #                     'documentno': record[2],
    #                     'desc': record[3],
    #                     'value_date': record[4][:10],
    #                     'invoiceno': record[5],
    #                     'c_bpartner_id': record[8],
    #                     'beneficiary_name': record[9],
    #                     'customercode': record[10],
    #                     'transaction_amount': abs(record[11]),
    #                     'totalamt': abs(record[11]),
    #                     'allocatedamt': record[12],
    #                     'unallocated': abs(record[13]),
    #                     'duedays': record[14],
    #                     'term_duedays': record[15],
    #                     'c_invoice_id': record[16],
    #                     'ad_org_id': self.ad_org_id.id,
    #                 }))
    #
    #             self.invoice_lines_one2many = invoice_lines
    #             self.state = 'generated_invoice'
    #             seq = self.env['ir.sequence'].sudo().next_by_code('bank.payment.invoice') or '/'
    #             self.name = 'DI/' + str(self.company_id.short_name) + '/' + str(seq)
    #
    #         except psycopg2.DatabaseError, e:
    #             if conn_pg: conn_pg.rollback()
    #             print
    #             '#-------------------Except ---Error %s' % e
    #
    #         finally:
    #             if conn_pg: conn_pg.close()
    #             print
    #             "#--------------Select ----Finally----------------------#"

    def update_payschedule_boolean(self, condition=False, entry_type=False):
        if self.config_id:
            try:
                conn_pg = psycopg2.connect(dbname=self.config_id.database_name, user=self.config_id.username,
                                           password=self.config_id.password, host=self.config_id.ip_address,
                                           port=self.config_id.port)
                pg_cursor = conn_pg.cursor()

                if entry_type == 'invoice':

                    doc_number = tuple([(res.documentno).encode('utf-8') for res in self.invoice_filter_one2many])

                    if condition == 1:
                        pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'Y' where ad_client_id=%s and \
                            documentno in %s", (self.company_id.ad_client_id, doc_number))
                    elif condition == 0:
                        pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'N' where ad_client_id=%s and \
                            documentno in %s", (self.company_id.ad_client_id, doc_number))
                    else:
                        pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'N' where ad_client_id=%s and \
                            documentno in %s", (self.company_id.ad_client_id, doc_number))

                    print("============== Update Invoice =====================", condition, entry_type, doc_number)

                elif entry_type == 'payment':
                    doc_number = tuple([(res.documentno).encode('utf-8') for res in self.payment_selected_one2many])

                    if condition == 1:
                        pg_cursor.execute("update adempiere.C_Payment set IsOnline = 'Y' where ad_client_id=%s and \
                            documentno in %s", (self.company_id.ad_client_id, doc_number))
                    else:
                        pg_cursor.execute("update adempiere.C_Payment set IsOnline = 'N' where ad_client_id=%s and \
                            documentno in %s", (self.company_id.ad_client_id, doc_number))

                    print("============== Update Payments =====================", condition, entry_type, doc_number)

                entry_id = conn_pg.commit()

            except psycopg2.DatabaseError as e:
                if conn_pg: conn_pg.rollback()
                print
                '-----------------------------Error %s' % e

            finally:
                if conn_pg: conn_pg.close()
                print
                "#---------------Update ----Finally----------------------#"

    def update_isselfservice_boolean(self, condition=False, documentno=False):
        if self.config_id:
            try:
                conn_pg = psycopg2.connect(dbname=self.config_id.database_name, user=self.config_id.username,
                                           password=self.config_id.password, host=self.config_id.ip_address,
                                           port=self.config_id.port)
                pg_cursor = conn_pg.cursor()

                doc_number = (documentno).encode('utf-8')

                if condition == 1:
                    pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'Y' where ad_client_id=%s and \
                        documentno = %s", (self.company_id.ad_client_id, doc_number))
                elif condition == 0:
                    pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'N' where ad_client_id=%s and \
                        documentno = %s", (self.company_id.ad_client_id, doc_number))
                else:
                    pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'N' where ad_client_id=%s and \
                        documentno = %s", (self.company_id.ad_client_id, doc_number))

                print("============== Update Invoice =====================", condition, doc_number)

                entry_id = conn_pg.commit()

            except psycopg2.DatabaseError as e:
                if conn_pg: conn_pg.rollback()
                print
                '-----------------------------Error %s' % e

            finally:
                if conn_pg: conn_pg.close()
                print
                "#---------------Update ----Finally----------------------#"

    def generate_filter_invoice_report(self):
        filter_invoice_report = 1
        self.general_invoice_report(filter_invoice_report)
        if self.state in ('generated_invoice', 'draft'): self.state = 'generated_invoice_template'
        self.filter_rep_bool = True

    def revert_payment_entries(self):
        condition = 0
        self.sudo().update_payschedule_boolean(condition, entry_type='payment')

    def generate_invoice_report(self):
        self.general_invoice_report()
        self.inv_rep_bool = True

    def general_invoice_report(self, filter_invoice_report=False):
        self.ensure_one()

        if filter_invoice_report == 1:
            name = 'Filter Invoices Report' + '(' + str(date.today()) + ')'
            invoice_filter = self.invoice_filter_one2many
        else:
            name = 'Invoices Report' + '(' + str(date.today()) + ')'
            invoice_filter = self.invoice_lines_one2many

        status = payment_no = second_heading = approval_status = ''
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet(name)
        fp = BytesIO()
        row_index = 0

        worksheet.col(0).width = 2000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 3000
        worksheet.col(6).width = 12000
        worksheet.col(7).width = 3000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 5000
        worksheet.col(10).width = 3000

        for index, value in enumerate(header_fields3):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        count = 0

        if len(invoice_filter) < 1:
            raise ValidationError(_('No Records Selected'))

        for res in invoice_filter:
            if res:
                count += 1

                worksheet.write(row_index, 0, count, base_style)
                worksheet.write(row_index, 1, self.company_id.name, base_style)
                worksheet.write(row_index, 2, res.ad_org, base_style)
                worksheet.write(row_index, 3, res.value_date, base_style)
                worksheet.write(row_index, 4, res.documentno, base_style)
                worksheet.write(row_index, 5, res.customercode, base_style)
                worksheet.write(row_index, 6, res.beneficiary_name, base_style)
                worksheet.write(row_index, 7, str(abs(res.totalamt)), base_style)
                worksheet.write(row_index, 8, str(abs(res.allocatedamt)), base_style)
                worksheet.write(row_index, 9, str(abs(res.unallocated)), base_style)
                worksheet.write(row_index, 10, res.duedays, base_style)

                row_index += 1

        row_index += 1
        workbook.save(fp)

        out = base64.encodebytes(fp.getvalue())

        if filter_invoice_report == 1:
            self.write({'output_file': out, 'export_file': name + '.xls'})
        else:
            self.write({'file_name2': out, 'hr_payment_data2': name + '.xls'})

    def refuse_approval_request(self, remarks=False, user_id=False):
        owner_refuse = self.env['res.users'].sudo().search([("id", "=", self.owner_id.owner_id.id)])
        print("owner_refuse-------------", owner_refuse, self.env.uid)
        owner = self.env['erp.representative.matrix'].sudo().search([
            ("approver_id", "=", self.owner_id.id),
            ("min_amt", "<=", self.amount_filtered_total),
            ("max_amt", ">=", self.amount_filtered_total)], limit=1)
        if not owner:
            owner_approval = self.owner_id.owner_id
        else:
            owner_approval = owner.user_id
        user_mail = self.env['res.users'].sudo().search([("id", "=", self.user_id.id)])
        if owner_approval.has_group('sales_meet.group_bank_payment_manager'):

            if not (remarks or self.note):
                raise ValidationError(_('Kindly Update the Remarks and then Reject'))

            if self.note:
                self.sudo().write({'state': 'refused'})
            else:
                self.sudo().write({'state': 'refused', 'note': remarks or self.note})

            subject = "[Refused] Approval on %s" % (self.name)
            full_body = (_("Approval on Document %s has been refused by \
                %s.<br/><ul class=o_timeline_tracking_value_list></ul>") % (self.name, owner_refuse.name))

            email_from = owner_refuse.email
            payment_mail = "payments@walplast.com"
            email_to_user = self.user_id.email
            email_to = email_to_user + ',' + payment_mail
            condition = 0
            self.sudo().send_generic_mail(subject, full_body, email_from, email_to)
            self.sudo().update_payschedule_boolean(condition, entry_type='invoice')
            self.rejected_by_manager = datetime.now()
        else:
            raise ValidationError(_('Only Owner / Bank Payment Manager can Reject the Due Invoices'))

    def approve_approval_request(self, remarks=False, user_id=False):
        _logger.info("#########------------------- Partner :%s ", self.owner_id)
        owner = self.env['erp.representative.matrix'].sudo().search([
            ("approver_id", "=", self.owner_id.id),
            ("min_amt", "<=", self.amount_filtered_total),
            ("max_amt", ">=", self.amount_filtered_total)], limit=1)
        if not owner:
            owner_approval = self.owner_id.owner_id
        else:
        # owner_approval = self.env['res.users'].sudo().search([("id", "=", self.owner_id.owner_id.id)])
            owner_approval = owner.user_id
        user_mail = self.env['res.users'].sudo().search([("id", "=", self.user_id.id)])
        if owner_approval.has_group('sales_meet.group_bank_payment_manager'):
            if not (remarks or self.note):
                raise ValidationError(_('Kindly Update the Remarks and then Approve'))

            if self.note:
                self.sudo().write({'state': 'approved'})
            else:
                self.sudo().write({'state': 'approved', 'note': remarks or self.note})

            approver = 0
            condition = 1
            email_from = owner_approval.login
            payment_mail = "payments@walplast.com"
            email_to_user = user_mail.login
            email_to = email_to_user + ',' + payment_mail
            subject = "[Approved] Request for %s" % (self.name)
            initial_body = """ 
                <h3>Hi %s,</h3>
                <h3>The request for document %s is approved by %s dated %s</h3>
                <h3>You can Post the Invoices to create Payment in ERP. </h3>
            """ % (user_mail.name, self.name, owner_approval.name, todaydate)

            self.sudo().send_general_mail(initial_body, subject, approver, email_from, email_to)
            self.sudo().update_payschedule_boolean(condition, entry_type='invoice')
            self.approved_by_manager = datetime.now()
        else:
            raise ValidationError(_('Only Owner / Bank Payment Manager can Approve the Due Invoices'))

    def send_approval_mail(self):
        if not self.owner_id:
            raise ValidationError(_('Kindly Select Owner for requesting Approval for the Due Invoices'))

        approver = 1
        email_from = self.user_id.email
        # owner = False

        if self.owner_id.hierarchy_bool:
            owner = self.env['erp.representative.matrix'].sudo().search([
                ("approver_id", "=", self.owner_id.id),
                ("min_amt", "<=", self.amount_filtered_total),
                ("max_amt", ">=", self.amount_filtered_total)], limit=1)

            # owner_id = self.env['res.users'].sudo().search([("id", "=", self.owner_id.owner_id.id)])
            email_to = owner.user_id.login
        else:
            # owner = self.env['res.users'].sudo().search([("id", "=", self.owner_id.owner_id.id)])
            owner = self.env['res.users'].sudo().search([("id", "=", self.owner_id.owner_id.id)])
            email_to = owner.login
        # raise ValidationError(_(email_to))
        subject = "Request for Due Invoices Approval - %s - %s - %s" % (self.name, self.user_id.name, todaydate)
        initial_body = """ 
        <h3>Hi %s,</h3>
            <h3>The following Invoices are outstanding / unallocated and requires an approval from your end.</h3>
            <h3>Kindly take necessary action by clicking the buttons below:</h3>
        """ % (owner.name if owner else '')
        self.send_general_mail(initial_body, subject, approver, email_from, email_to)
        self.state = 'submitted_to_manager'
        self.submitted_to_manager = datetime.now()
        # conn_pg = psycopg2.connect(dbname=self.config_id.database_name, user=self.config_id.username,
        #                            password=self.config_id.password, host=self.config_id.ip_address,
        #                            port=self.config_id.port)
        # pg_cursor = conn_pg.cursor()
        # doc_number = tuple([(res.documentno).encode('utf-8') for res in self.invoice_filter_one2many])
        # pg_cursor.execute("update adempiere.C_Invoice set IsSelfService = 'Y' where ad_client_id=%s and \
        #                         documentno in %s", (self.company_id.ad_client_id, doc_number))
        # conn_pg.commit()

    # @api.multi
    def send_general_mail(self, initial_body=False, subject=False, approver=False, email_from=False, email_to=False):
        second_body = body = line_html = """ """
        main_id = self.id
        owner_general = self.env['res.users'].sudo().search([("id", "=", self.owner_id.owner_id.id)])

        ###################Code to avoid duplication in bank payment approval ############################
        entries_to_remove = ''
        inv_duplication_states = ['draft', 'generated_invoice', 'generated_invoice_template', 'refused']
        # code to uncomment
        # for invoice in self.invoice_filter_one2many:
        #     sent_for_approval = self.env['bank.invoice.filter'].sudo().search([("invoice_filter_id", "!=", self.id),('documentno','=',invoice.documentno),('invoice_filter_id.state','not in',inv_duplication_states),
        #                                                                        ('invoice_filter_id.company_id','=',self.company_id.id)])
        #     if sent_for_approval:
        #         for duplicate_doc in sent_for_approval:
        #             if duplicate_doc.documentno == invoice.documentno:
        #                 entries_to_remove += str(duplicate_doc.documentno) + "( " + str(duplicate_doc.invoice_filter_id.name) + " : " + str(duplicate_doc.invoice_filter_id.state) + " )" + " ,"
        #         invoice.unlink()
        #
        # if entries_to_remove:
        #     self.write({'approval_note':"Following are removed from approval request, kindly resend the request with updated filtered invoice: " + entries_to_remove})
        #  End of code to uncomment

        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'warning.msg.wiz',
        #         'target': 'new',
        #         'context': {
        #             'default_name': entries_to_remove,
        #         }
        #     }
        ###################################################################################################

        invoice_filter_line = self.invoice_filter_one2many.search([("invoice_filter_id", "=", self.id)],
                                                                  order='beneficiary_name asc, value_date desc')

        # code to uncomment

        # if len(invoice_filter_line) < 1:
        #     if entries_to_remove:
        #         raise ValidationError(_(self.approval_note))
        #     else:
        #         raise ValidationError(_('No Records Selected'))
        #  End of code to uncomment

        for l in invoice_filter_line:
            start_date = datetime.strptime(str(((l.value_date).split())[0]),
                                           tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%y')

            line_html += """
                <tr>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                    <td style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">%s</td>
                </tr>
                """ % (start_date, l.invoiceno, l.documentno, l.customercode, l.beneficiary_name, \
                       l.totalamt, l.allocatedamt, l.unallocated, l.desc or '', l.payment_term, l.duedays,
                       l.term_duedays)

            # totalcn += l.totalamt

        main_date = datetime.strptime(((str(self.date).split())[0]),
                                      tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%y')

        body = """
                <table >
                    <tr>  <th style=" text-align: left;padding: 8px;">Doc No</td><td> : %s</td></tr>
                    <tr>  <th style=" text-align: left;padding: 8px;">Date</td><td> : %s</td></tr>
                    <tr>  <th style=" text-align: left;padding: 8px;">Bank Account</td>  <td> : %s</td></tr>
                    <tr>  <th style=" text-align: left;padding: 8px;">Organisation</td>  <td> : %s</td></tr>
                    <tr>  <th style=" text-align: left;padding: 8px;">Owner</td>  <td> : %s</td></tr>
                    <tr>  <th style=" text-align: left;padding: 8px;">Requester</td>  <td> : %s</td></tr>
                    <tr>  <th style=" text-align: left;padding: 8px;">Company</td>  <td> : %s</td></tr>
                </table>
                <br/>

                <table border="1">
                    <tbody>
                        <tr class="text-center table_mail">
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Invoice Date</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Invoice No</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Document No</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Code</th>             
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Vendor Partner</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Total Amt</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Part Payment</th>             
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Balance</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Description</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Payment Term</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Due Days</th>
                            <th style="border: 1px solid black; padding-left: 5px; padding-right: 5px;">Overdue Days</th>
                        </tr>
                        %s
                    </tbody>
                </table>
                <br/><br/>

            """ % (self.name, main_date, self.erp_bank_id.name or '', self.ad_org_id.name or '',
                   owner_general.name, self.user_id.name or '', self.company_id.name, line_html)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        imd = self.env['ir.model.data']

        approve_url = base_url + '/approvals?%s' % (url_encode({
            'model': self._name,
            'approval_id': main_id,
            'res_id': main_id,
            'user_id': owner_general.id,
            'action': 'approve_approval_request',
        }))
        reject_url = base_url + '/approvals?%s' % (url_encode({
            'model': self._name,
            'approval_id': main_id,
            'res_id': main_id,
            'user_id': owner_general.id,
            'action': 'refuse_approval_request',
        }))

        report_check = base_url + '/web#%s' % (url_encode({
            'model': self._name,
            'view_type': 'form',
            'id': main_id,
            'view_id': imd.xmlid_to_res_id('sales_meet.view_invoice_payment_form')
        }))

        if approver == 1:

            second_body = """<br/>
                <table class="table" style="border-collapse: collapse; border-spacing: 0px;">
                    <tbody>
                        <tr class="text-center">
                            <td>
                                <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                    font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                    text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                    text-align: center; vertical-align: middle; cursor: pointer; 
                                    white-space: nowrap; background-image: none; background-color: #337ab7; 
                                    border: 1px solid #337ab7; margin-right: 10px;">Approve All</a>
                            </td>
                            <td>
                                <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                    font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                    text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                    text-align: center; vertical-align: middle; cursor: pointer; 
                                    white-space: nowrap; background-image: none; background-color: #337ab7; 
                                    border: 1px solid #337ab7; margin-right: 10px;">Reject All</a>
                            </td>

                            <td>
                                <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                    font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                    text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                    text-align: center; vertical-align: middle; cursor: pointer; 
                                    white-space: nowrap; background-image: none; background-color: #337ab7; 
                                    border: 1px solid #337ab7; margin-right: 10px;">Check All</a>
                            </td>

                        </tr>
                    </tbody>
                </table>
                """ % (approve_url, reject_url, report_check)

        else:

            second_body = """<br/>
                <table class="table" style="border-collapse: collapse; border-spacing: 0px;">
                    <tbody>
                        <tr class="text-center">
                            <td>
                                <a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
                                    font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
                                    text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
                                    text-align: center; vertical-align: middle; cursor: pointer; 
                                    white-space: nowrap; background-image: none; background-color: #337ab7; 
                                    border: 1px solid #337ab7; margin-right: 10px;">Check Approval</a>
                            </td>
                        </tr>
                    </tbody>
                </table>
                """ % (report_check)

        full_body = initial_body + body + second_body

        self.send_generic_mail(subject, full_body, email_from, email_to)

    def send_generic_mail(self, subject=False, full_body=False, email_from=False, email_to=False):
        composed_mail = self.env['mail.mail'].sudo().create({
            'model': self._name,
            'res_id': self.id,
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': full_body,
        })

        composed_mail.send()
        print("---------Mail Sent to ---------", email_to, "---------Mail Sent From ---------", email_from)

    def set_to_posted(self):
        self.state = 'erp_posted'

    def set_to_submitted(self):
        condition = 1
        self.sudo().update_payschedule_boolean(condition, entry_type='payment')
        self.state = 'submitted_to_bank'

    def set_to_validated(self):
        self.state = 'validated'

    def validate_invoices(self):
        self.accounting_date = date.today()
        self.invoice_summary_one2many.sudo().unlink()
        conn_pg = None
        wpp_trans_charged = wpp_trans_pmt_rcvd = wpp_trans_pmt_bal = wpp_trans_charges = ''
        config_id = self.env['external.db.configuration'].sudo().search([('state', '=', 'connected')], limit=1)

        if config_id:
            try:
                filtered_list = []
                filter_dict = {}
                vals = []
                # filter_id =[]

                invoice_filter = self.invoice_filter_one2many.search([("invoice_filter_id", "=", self.id)])

                if len(invoice_filter) < 1:
                    raise ValidationError(_('No Records Selected'))

                for rec in self.invoice_filter_one2many:
                    # filtered_list.append((rec.beneficiary_name,(rec.id, rec.unallocated)))
                    filtered_list.append(rec.beneficiary_name)

                filtered_list3 = dict(Counter(filtered_list))

                for beneficiary_name, value in filtered_list3.items():
                    total_amount = total_unallocated_amount = total_allocatedamt = 0
                    filter_id = []

                    for record in self.invoice_filter_one2many:
                        if beneficiary_name == record.beneficiary_name:
                            if value > 1:
                                total_unallocated_amount += record.unallocated
                                total_amount += record.totalamt
                                total_allocatedamt += record.allocatedamt
                                filter_id.append(record.id)
                            else:
                                total_unallocated_amount = record.unallocated
                                total_allocatedamt = record.allocatedamt
                                total_amount = record.totalamt
                                filter_id = [record.id]

                            # customercode = record.customercode
                            c_bpartner_id = (str(record.c_bpartner_id).split('.'))[0]
                            beneficiary_name = beneficiary_name
                            beneficiary_code = record.customercode

                            # filter_id = record.id

                    new_list = (c_bpartner_id, abs(total_amount), abs(total_unallocated_amount),
                                beneficiary_name, beneficiary_code, filter_id, abs(total_allocatedamt))

                    vals.append(new_list)

                print(vals)
                # pdb.set_trace()
                isactive = "isactive =  'Y' "
                ad_client_id = self.company_id.ad_client_id
                main_query = " select TotalOpenBalance from adempiere.c_bpartner "
                conn_pg = psycopg2.connect(dbname=config_id.database_name, user=config_id.username,
                                           password=config_id.password, host=config_id.ip_address, port=config_id.port)
                pg_cursor = conn_pg.cursor()

                unvalidated = 0
                for res in vals:
                    documentno_log = ''
                    end_query = "Where C_BPartner_ID = '%s' and ad_client_id = %s " % (res[0], ad_client_id)
                    query_grn = main_query + end_query
                    pg_cursor.execute(query_grn)
                    record_query = pg_cursor.fetchall()

                    if abs(round(res[1])) <= abs(round(record_query[0][0])):
                        pass
                    else:
                        documentno_log = "Entry Not Validated as Total Open Balance (%s)\
                        of Vendor is less than the Total Invoice Amount (%s)" % (res[1], record_query[0][0])
                        self.invoice_filter_one2many.search([('id', 'in', res[5])]).write(
                            {'log': documentno_log})

                        unvalidated += 1
                        # raise ValidationError(_('Invoice No Not Found '))

                    vals_line = {
                        'vendor_summary_id': self.id,
                        'transaction_amount': record_query[0][0],
                        'beneficiary_code': res[4],
                        'beneficiary_name': res[3],
                        'totalamt': abs(res[1]),
                        'allocatedamt': abs(res[6]),
                        'unallocated': abs(res[2]),
                        'unallocated2': abs(res[2]),
                        'ad_org': self.ad_org_id.name,
                        'c_bpartner_id': res[0],
                        'ad_org_id': self.ad_org_id.id,
                        'open_balance': abs(round(record_query[0][0])),
                        'filtered_line_ids': [(6, 0, res[5])],  # res[5],
                        'company_id': self.company_id.id,
                        'log': documentno_log,
                        # 'c_invoice_id': self.c_invoice_id,
                    }
                    print("aaaaaaaaaaaaaaaaaaaaaaaa", vals_line, res[0], res[1], record_query[0][0], res[5])

                    vendor_summary = self.invoice_summary_one2many.sudo().create(vals_line)
                    vendor_summary.name = "VSI/" + str(vendor_summary.id)

                    entry_id = conn_pg.commit()

                if unvalidated == 0:
                    self.state = 'validated'

            except psycopg2.DatabaseError as e:
                if conn_pg: conn_pg.rollback()
                print
                'Error %s' % e

            finally:
                if conn_pg: conn_pg.close()
                print
                "#---------------Update Lines----Finally----------------------#"

    def generate_payment_webservice(self, filter_ids=None, single_entry=False):
        print("generate_payment_webservice====-------------------------")
        if filter_ids and single_entry == True:
            invoice_filter = self.invoice_filter_one2many.sudo().search([("id", "in", filter_ids)])
        else:
            invoice_filter = self.invoice_filter_one2many.sudo().search([("invoice_filter_id", "=", self.id),
                                                                         ('state', '!=', 'approved')])

        # print "aAAAAAAAAAAAAAAAAAAAAA", invoice_filter

        if len(invoice_filter) < 1:
            raise ValidationError(_('No Records Selected'))

        user_ids = self.env['wp.erp.credentials'].sudo().search(
            [("wp_user_id", "=", self.env.uid), ("company_id", "=", self.company_id.id)])
        print("user_ids-------", user_ids)
        if len(user_ids) < 1:
            raise ValidationError(_("User's ERP Credentials not found. Kindly Contact IT Helpdesk"))

        filtered_list = []
        filter_dict = {}
        vals = []
        documentno = ''

        daymonth = datetime.strptime(str(self.accounting_date),
                                     tools.DEFAULT_SERVER_DATE_FORMAT).strftime("%Y-%m-%d 00:00:00")
        C_BankAccount_ID = self.erp_bank_id.c_bankaccount_id

        if self.company_id.ad_client_id == '1000000':
            C_DocType_ID = 1000009
        elif self.company_id.ad_client_id == '1000001':
            C_DocType_ID = 1000056
        elif self.company_id.ad_client_id == '1000002':
            C_DocType_ID = 1000103
        elif self.company_id.ad_client_id == '1000003':
            C_DocType_ID = 1000150
        elif self.company_id.ad_client_id == '1000022':
            C_DocType_ID = 1000787
        elif self.company_id.ad_client_id == '1000021':
            C_DocType_ID = 1000697

        else:
            raise UserError(" Select proper company ")

        filtered_list = [rec.beneficiary_name for rec in invoice_filter]
        filtered_list3 = dict(Counter(filtered_list))

        for beneficiary_name, value in filtered_list3.items():
            total_amount = tds_amount = 0
            payment_description = ''

            for record in self.invoice_filter_one2many:
                if beneficiary_name == record.beneficiary_name:
                    tds_amount += record.tds_amount
                    if value > 1:
                        total_amount += record.unallocated
                        documentno = ''
                        payment_description += record.invoiceno + ', '
                    else:
                        total_amount = record.unallocated
                        documentno = record.documentno
                        payment_description = record.invoiceno

                    ad_org = record.ad_org_id.ad_org_id
                    date_filter = record.invoice_filter_id.date
                    customercode = record.customercode
                    c_bpartner_id = (str(record.c_bpartner_id).split('.'))[0]
                    beneficiary_name = record.beneficiary_name
                    filter_id = record.id
                    check_no = transaction_type[record.transaction_type] if record.transaction_type else 'NEFT'
                    acct_no = record.beneficiary_account_number or ''
                    ifsc = record.ifsc_code or ''

            new_list = (
                ad_org, customercode, documentno, abs(total_amount), c_bpartner_id, filter_id, payment_description,
                check_no,
                acct_no, beneficiary_name, ifsc, 'Y' if tds_amount > 0 else 'N', 0.0)

            vals.append(new_list)

        upper_body = """<?xml version="1.0" encoding="UTF-8"?>
         <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:_0="http://idempiere.org/ADInterface/1_0">
           <soapenv:Header/>
           <soapenv:Body>
              <_0:compositeOperation>
                 <!--Optional:-->
                 <_0:CompositeRequest>
                    <_0:ADLoginRequest>
                       <_0:user>%s</_0:user>
                       <_0:pass>%s</_0:pass>
                       <_0:ClientID>%s</_0:ClientID>
                       <_0:RoleID>%s</_0:RoleID>
                       <_0:OrgID>0</_0:OrgID>
                       <_0:WarehouseID>0</_0:WarehouseID>
                       <_0:stage>0</_0:stage>
                    </_0:ADLoginRequest>
                    <_0:serviceType>CreateCompletePayment</_0:serviceType>
                    """ % (user_ids.erp_user, user_ids.erp_pass, self.company_id.ad_client_id, user_ids.erp_roleid)

        lower_body = """    
                          <_0:operation preCommit="true" postCommit="true">
                          <_0:TargetPort>setDocAction</_0:TargetPort>
                          <_0:ModelSetDocAction>
                             <_0:serviceType>CompletePayment</_0:serviceType>
                             <_0:tableName>C_Payment</_0:tableName>
                             <_0:recordID>0</_0:recordID>
                             <_0:recordIDVariable>@C_Payment.C_Payment_ID</_0:recordIDVariable>
                             <_0:docAction>CO</_0:docAction>
                          </_0:ModelSetDocAction>
                       </_0:operation>
                    </_0:operations>
                 </_0:CompositeRequest>
              </_0:compositeOperation>
           </soapenv:Body>
        </soapenv:Envelope>"""

        for res in vals:
            line_body = body = payment_body = documentno_log = """ """

            paymt_description = res[9] + " - Payment Against - " + res[6] if res[6] else ''
            payment_body = """<_0:operations>
                               <_0:operation preCommit="false" postCommit="false">
                                  <_0:TargetPort>createData</_0:TargetPort>
                                  <_0:ModelCRUD>
                                     <_0:serviceType>CreatePayment</_0:serviceType>
                                     <_0:TableName>C_Payment</_0:TableName>
                                     <_0:DataRow>
                                        <!--Zero or more repetitions:-->
                                        <_0:field column="AD_Org_ID">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="C_BankAccount_ID">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="C_DocType_ID">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="DateTrx">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="DateAcct">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="C_Invoice_ID">
                                           <_0:val/>
                                        </_0:field>
                                        <_0:field column="C_BPartner_ID">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="PayAmt">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="Description">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="ByWebservice">
                                           <_0:val>Y</_0:val>
                                        </_0:field>
                                        <_0:field column="IsOverUnderPayment">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="OverUnderAmt">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="CheckNo">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="AccountNo">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="A_Name">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="Micr">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="C_Currency_ID">
                                           <_0:val>304</_0:val>
                                        </_0:field>
                                     </_0:DataRow>
                                  </_0:ModelCRUD>
                               </_0:operation>

                                     """ % (self.ad_org_id.ad_org_id, C_BankAccount_ID, C_DocType_ID,
                                            daymonth, daymonth, res[4], res[3], paymt_description, res[11], 0.0, res[7],
                                            res[8],
                                            res[9], res[10])

            filterline_ids = []
            for line_rec in invoice_filter:
                filterline_ids.append(line_rec.id)
                if line_rec.customercode == res[1]:
                    total_amount = abs(line_rec.unallocated)
                    line_body += """
                                  <_0:operation preCommit="false" postCommit="false">
                                  <_0:TargetPort>createData</_0:TargetPort>
                                  <_0:ModelCRUD>
                                     <_0:serviceType>PaymentAllocationLines</_0:serviceType>
                                     <_0:TableName>C_PaymentAllocate</_0:TableName>
                                     <RecordID>0</RecordID>
                                     <Action>createData</Action>
                                     <_0:DataRow>
                                        <!--Zero or more repetitions:-->
                                        <_0:field column="AD_Org_ID">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="C_Invoice_ID">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="Amount">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="InvoiceAmt">
                                           <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="OverUnderAmt">
                                            <_0:val>%s</_0:val>
                                        </_0:field>
                                        <_0:field column="C_Charge_ID">
                                            <_0:val/>
                                        </_0:field>
                                         <_0:field column="C_Payment_ID">
                                           <_0:val>@C_Payment.C_Payment_ID</_0:val>
                                        </_0:field>
                                        </_0:DataRow>
                                    </_0:ModelCRUD>
                                    </_0:operation>
                                  """ % (self.ad_org_id.ad_org_id, (str(line_rec.c_invoice_id).split('.'))[0],
                                         total_amount, line_rec.unallocated2, line_rec.unallocated2 - total_amount)

            body = upper_body + payment_body + line_body + lower_body
            ################################### Report Part ########################################
            message_to_write = """Request: \n""" + str(body)
            # message_to_write = """Request"""
            #########################################################################################
            idempiere_url = self.config_id.idempiere_url_dns or self.config_id.idempiere_url

            response = requests.post(idempiere_url, data=body, headers=headers)
            # raise Warning(_(response.content))
            ################################### Report Part ########################################
            message_to_write += """\n\n\n Response: \n""" + str(response.content)
            fp = StringIO()
            fp.write(message_to_write)
            out = fp.getvalue()
            self.paymnt_report = out
            self.api_resp = out
            self.report_filename = str(self.name) + "_" + daymonth + ".txt"
            #########################################################################################

            # print (response.content, type(response.content)

            log = str(response.content)
            if log.find('DocumentNo') is not -1:
                # if single_entry == False:
                #     self.state = 'erp_posted'
                documentno_log = log.split('column="DocumentNo" value="')[1].split('"></outputField>')[0]

            if log.find('IsRolledBack') is not -1:
                documentno_log = log.split('<Error>')[1].split('</Error>')[0]
                raise ValidationError("Error Occured %s \n Request : %s" % (documentno_log, message_to_write))

            if log.find('Invalid') is not -1:
                documentno_log = log.split('<faultstring>')[1].split('</faultstring>')[0]
                raise ValidationError("Error Occured %s \n Request : %s" % (documentno_log, message_to_write))

            write_data = self.invoice_filter_one2many.search([('id', 'in', filterline_ids)]).write(
                {'log': documentno_log, 'state': 'approved'})
            remain_data = self.invoice_filter_one2many.search([('state', '!=', 'approved')])
            if not remain_data:
                self.state = 'erp_posted'
            # write_data = self.invoice_filter_one2many.search([('id', '=', res[5])]).write(
            # {'log': documentno_log,'state': 'approved'})

            self.invoice_lines_one2many.unlink()
            self.payment_processed_date = datetime.now()

            if filter_ids and single_entry == True:
                print("--------- documentno_log -----", documentno_log)
                return documentno_log

    def sync_payments(self):
        conn_pg = None
        payment_lines = []
        if not self.config_id:
            raise UserError(" DB Connection not set / Disconnected ")
        else:
            try:
                print
                "#-------------Select --TRY----------------------#"

                ad_client_id = self.company_id.ad_client_id
                c_bankaccount_id = self.erp_bank_id.c_bankaccount_id
                ad_org_id = self.ad_org_id.ad_org_id
                print("self.config_id.password---------", self.config_id.password)
                conn_pg = psycopg2.connect(dbname=self.config_id.database_name, user=self.config_id.username,
                                           password=self.config_id.password, host=self.config_id.ip_address,
                                           port=self.config_id.port)
                pg_cursor = conn_pg.cursor()

                pg_cursor.execute("select \
                    cp.c_payment_ID, \
                    cp.documentno, \
                    cp.dateacct::date, \
                    cp.payamt, \
                    cb.name, \
                    cp.description, \
                    (select a_name  from adempiere.C_BP_BankAccount cba where cba.C_BPartner_ID = cb.C_BPartner_ID limit 1)  , \
                    (select a_email  from adempiere.C_BP_BankAccount cba where cba.C_BPartner_ID = cb.C_BPartner_ID limit 1)  , \
                    (select x_ifc_code  from adempiere.C_BP_BankAccount cba where cba.C_BPartner_ID = cb.C_BPartner_ID limit 1)  , \
                    (select x_drawee_location  from adempiere.C_BP_BankAccount cba where cba.C_BPartner_ID = cb.C_BPartner_ID limit 1)  , \
                    (select X_BeneBankBranchName  from adempiere.C_BP_BankAccount cba where cba.C_BPartner_ID = cb.C_BPartner_ID limit 1)  , \
                    (select accountno  from adempiere.C_BP_BankAccount cba where cba.C_BPartner_ID = cb.C_BPartner_ID limit 1)  , \
                    (select name from adempiere.AD_User au where au.AD_User_ID = cb.SalesRep_ID ),\
                    (select EMail from adempiere.C_BPartner_Location cbl where cbl.C_BPartner_ID = cb.C_BPartner_ID limit 1) , \
                    (select EMail from adempiere.AD_User au where au.AD_User_ID = cb.SalesRep_ID ), \
                    (Select Name from adempiere.AD_Org where AD_Org_ID=cp.AD_Org_ID) as Org, \
                    cb.value,cp.C_BPartner_ID \
                from adempiere.c_payment cp \
                JOIN adempiere.C_BPartner cb ON cb.C_BPartner_ID = cp.C_BPartner_ID \
                WHERE \
                    cp.docstatus in ('CO') and \
                    ( cp.dateacct::date = %s::date  ) and \
                    cp.isreceipt = 'N'  and \
                    cp.IsOnline = 'N'  and \
                    cp.c_bankaccount_id = %s and \
                    cp.ad_org_id = %s and \
                    cp.ad_client_id = %s", (self.date, c_bankaccount_id, ad_org_id, ad_client_id))

                entry_id = pg_cursor.fetchall()
                if entry_id == []:
                    raise UserError(" No Records Found ")
                if self.payment_lines_one2many:
                    for rec in entry_id:
                        c_payment_id = (str(rec[0]).split('.'))[0]
                        for line in self.payment_lines_one2many:
                            if line.c_payment_id == c_payment_id and line.documentno == rec[1]:
                                line.owner = rec[8]
                                line.owner_email = rec[10]
                                line.beneficiary_account_number = rec[11]
                                line.transaction_amount = rec[3]
                                line.beneficiary_name = rec[6] if rec[6] else rec[4]
                                line.description = rec[5][:20] if rec[5] else ''
                                line.value_date = rec[2]
                                line.ifsc_code = rec[8]
                                line.bank_name = rec[10][:25] if rec[10] else ''
                                line.beneficiary_email_id = rec[7] if rec[7] else rec[13]
                                line.ad_org = rec[15]
                                line.customer_reference_number = rec[16]
                                line.c_bpartner_id = rec[17]

                if not self.payment_lines_one2many:
                    for record in entry_id:
                        user_ids = self.env['res.users'].search([("login", "=", record[10])])
                        if float(record[3]) > 2500000:
                            transaction_type = 'R'
                        else:
                            transaction_type = 'N'

                        payment_lines.append((0, 0, {
                            'payment_id': self.id,
                            'documentno': record[1],
                            'c_payment_id': (str(record[0]).split('.'))[0],
                            'owner': record[8],
                            'owner_email': record[10],
                            'transaction_type': transaction_type,
                            'user_id': user_ids.id,
                            'beneficiary_account_number': record[11],
                            'transaction_amount': record[3],
                            'beneficiary_name': record[6] if record[6] else record[4],
                            'description': record[5][:20] if record[5] else '',
                            'value_date': record[2],
                            'ifsc_code': record[8],
                            'bank_name': record[10][:25] if record[10] else '',
                            'beneficiary_email_id': record[7] if record[7] else record[13],
                            'ad_org': record[15],
                            'customer_reference_number': record[16],
                            'c_bpartner_id': record[17]

                        }))
                        # self.env['bank.payment.lines'].sudo().create(vals_line)
                    self.payment_lines_one2many = payment_lines
                    self.state = 'generated_payment'
                    self.name_creation()


            except psycopg2.DatabaseError as e:
                if conn_pg:
                    raise UserError(_('Error %s' % e))
                    conn_pg.rollback()
                print
                '#----------------Error %s' % e

            finally:
                if conn_pg: conn_pg.close()
                print
                "#--------------Select ----Finally----------------------#"

    def update_to_icici(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet1')
        fp = StringIO()

        main_style = xlwt.easyxf(
            'font: bold on, height 400; align: wrap 1, vert centre, horiz center; borders: bottom thick, top thick, left thick, right thick')
        header_style = xlwt.easyxf(
            'font: bold on, height 220; align: wrap 1,  horiz center; borders: bottom thin, top thin, left thin, right thin')
        base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
        highlight_style = xlwt.easyxf(
            'align: wrap 1; borders: bottom thin, top thin, left thin, right thin;pattern: pattern fine_dots, fore_color white, back_color yellow;')

        row_index = 0

        worksheet.col(0).width = 8000
        worksheet.col(1).width = 8000
        worksheet.col(2).width = 8000
        worksheet.col(3).width = 8000
        worksheet.col(4).width = 8000
        worksheet.col(5).width = 8000
        worksheet.col(6).width = 8000
        worksheet.col(7).width = 8000
        worksheet.col(8).width = 8000
        worksheet.col(9).width = 8000
        worksheet.col(10).width = 8000
        worksheet.col(11).width = 10000
        worksheet.col(11).height = 2000
        worksheet.col(12).width = 8000
        worksheet.col(13).width = 8000
        worksheet.col(14).width = 8000
        worksheet.col(15).width = 8000
        worksheet.col(16).width = 10000
        worksheet.col(17).width = 10000
        worksheet.col(18).width = 10000
        worksheet.col(19).width = 10000
        worksheet.col(20).width = 10000
        worksheet.col(21).width = 10000

        # Headers
        header_fields = ['Debit Ac No', 'Beneficiary Ac No', 'Beneficiary Name', 'Amt', 'Pay Mod', 'Date', 'IFSC',
                         'Payable Location', 'Print Location', 'Bene Mobile No.', 'Bene Email ID', 'Bene add1',
                         'Bene add2', 'Bene add3',
                         'Bene add4', 'Add Details 1', 'Add Details 2', 'Add Details 3', 'Add Details 4',
                         'Add Details 5', 'Remarks']

        for index, value in enumerate(header_fields):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        payment_lines = self.payment_selected_one2many.sudo().search(
            [('selected_payment_id', '=', self.id), ('state', '=', 'approved')])

        if (not payment_lines):
            raise ValidationError("Record Not Founds")

        for line in payment_lines:
            worksheet.write(row_index, 1, line.truck_order_id or "-",
                            header_style if not line.truck_order_id else base_style)
            row_index += 1

        workbook.save(fp)

        out = base64.encodebytes(fp.getvalue())
        # self.write(
        #     # {'state': 'get', 'report': out, 'name': 'QR Code Details (' + self.date_from + ' / ' + self.date_to + ').xls'})
        #     {'state': 'get', 'xls_file': out, 'filename': 'TPR Report.xls'})
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'tpr.plan.report',
        #     'view_mode': 'form',
        #     'view_type': 'form',
        #     'res_id': self.id,
        #     'target': 'new',
        # }

    def update_to_hsbc(self):
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # # ssh.connect(hostname='ecom-sftp.fguk-pprd.hsbc.com', username='PC000021163_25760',
        # #             port=10022,key_filename='/home/walplast2/id_rsa',pkey=paramiko.RSAKey.from_private_key_file("/home/walplast2/id_rsa"))
        # ssh.connect(hostname='ecom-sftp.fguk-pprd.hsbc.com', username='PC000021163_25980',
        #             port=10022, key_filename="/home/ni3/Desktop/id_rsa")
        #
        # stdin, stdout, stderr = ssh.exec_command('ls')
        # if stdout.readlines():
        #     raise ValidationError(_(stdout.readlines()))
        #
        # print stdout.readlines()
        # ssh.close()
        self.name_creation()
        payment_lines = self.payment_selected_one2many.sudo().search(
            [('selected_payment_id', '=', self.id), ('state', '=', 'approved')])
        if len(payment_lines) < 1:
            raise ValidationError(_('No Records Selected'))
        company = self.company_id
        total_amount = 0.0
        today_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        batch_reference = 'HSBC/' + str(self.company_id.short_name) + "/" + today_datetime
        value_date = date.today()
        line_body = """"""
        for line in payment_lines:
            total_amount += line.transaction_amount
            # value_date = line.value_date
            line_body += """<CdtTrfTxInf>
                            <PmtId>
                                <InstrId>%s</InstrId>
                                <EndToEndId>%s</EndToEndId>
                            </PmtId>
                            <Amt>
                                <InstdAmt Ccy="INR">%s</InstdAmt>
                            </Amt>
                            <ChrgBr>DEBT</ChrgBr>
                            <CdtrAgt>
                                <FinInstnId>
                                    <ClrSysMmbId>
                                        <MmbId>%s</MmbId>
                                    </ClrSysMmbId>
                                    <PstlAdr>
                                        <Ctry>IN</Ctry>
                                    </PstlAdr>
                                </FinInstnId>
                            </CdtrAgt>
                            <Cdtr>
                                <Nm>%s</Nm>
                                <PstlAdr>
                                    <Ctry>IN</Ctry>
                                </PstlAdr>
                            </Cdtr>
                            <CdtrAcct>
                                <Id>
                                    <Othr>
                                        <Id>%s</Id>
                                    </Othr>
                                </Id>
                            </CdtrAcct>
                            <RltdRmtInf>
                                <RmtLctnMtd>EMAL</RmtLctnMtd>
                                <RmtLctnElctrncAdr>%s</RmtLctnElctrncAdr>
                                <RmtLctnPstlAdr>
                                    <Nm>%s</Nm>
                                    <Adr>
                                        <Ctry>IN</Ctry>
                                    </Adr>
                                </RmtLctnPstlAdr>
                            </RltdRmtInf>
                            <RmtInf>
                                <Ustrd></Ustrd>
                                <Ustrd></Ustrd>
                                <Strd>
                                    <RfrdDocInf>
                                        <Tp>
                                            <CdOrPrtry>
                                            <Prtry></Prtry>
                                            </CdOrPrtry>
                                        </Tp>
                                        <Nb>%s</Nb>
                                        <RltdDt>%s</RltdDt>
                                    </RfrdDocInf>
                                    <RfrdDocAmt>
                                        <DuePyblAmt Ccy="INR">%s</DuePyblAmt>
                                    </RfrdDocAmt>
                                    <CdtrRefInf>
                                        <Tp>
                                            <CdOrPrtry>
                                                <Prtry></Prtry>
                                            </CdOrPrtry>
                                        </Tp>
                                        <Ref></Ref>
                                    </CdtrRefInf>
                                    <AddtlRmtInf>%s</AddtlRmtInf>
                                </Strd>
                            </RmtInf>
                        </CdtTrfTxInf>""" % (
                line.customer_reference_number or '', line.documentno or '', line.transaction_amount,
                line.ifsc_code or '',
                line.beneficiary_name or '', line.beneficiary_account_number,
                line.beneficiary_email_id or "payments@walplast.com", line.beneficiary_name or '',
                line.customer_reference_number or '', line.value_date, line.transaction_amount, line.description)

        if total_amount > 200000:
            transaction_type = 'URNS'
        else:
            transaction_type = 'URGP'

        upper_body = """<?xml version="1.0" encoding="UTF-8"?>
                        <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                            <CstmrCdtTrfInitn>
                                <GrpHdr>
                                    <MsgId>%s</MsgId>
                                    <CreDtTm>%s</CreDtTm>
                                    <Authstn>
                                        <Cd>ILEV</Cd>
                                    </Authstn>
                                    <NbOfTxs>%s</NbOfTxs>
                                    <CtrlSum>%s</CtrlSum>
                                    <InitgPty>
                                        <Id>
                                            <OrgId>
                                                <Othr>
                                                    <Id>%s</Id>
                                                </Othr>
                                            </OrgId>
                                        </Id>
                                    </InitgPty>
                                </GrpHdr>
                                <PmtInf>
                                    <PmtInfId>%s</PmtInfId>
                                    <PmtMtd>TRF</PmtMtd>
                                    <PmtTpInf>
                                        <SvcLvl>
                                            <Cd>%s</Cd>
                                        </SvcLvl>
                                    </PmtTpInf>
                                    <ReqdExctnDt>%s</ReqdExctnDt>
                                    <Dbtr>
                                        <Nm>%s</Nm>
                                        <PstlAdr>
                                            <StrtNm>%s</StrtNm>
                                            <PstCd>%s</PstCd>
                                            <TwnNm>%s</TwnNm>
                                            <CtrySubDvsn>%s</CtrySubDvsn>
                                            <Ctry>IN</Ctry>
                                        </PstlAdr>
                                    </Dbtr>
                                    <DbtrAcct>
                                        <Id>
                                            <Othr>
                                                <Id>%s</Id>
                                            </Othr>
                                        </Id>
                                        <Ccy>INR</Ccy>
                                    </DbtrAcct>
                                    <DbtrAgt>
                                        <FinInstnId>
                                            <BIC>HSBCINBB</BIC>
                                            <PstlAdr>
                                                <Ctry>IN</Ctry>
                                            </PstlAdr>
                                        </FinInstnId>
                                    </DbtrAgt>""" % (
            self.name, today_datetime, len(payment_lines), total_amount, "006-304638", batch_reference,
            transaction_type,
            value_date, company.name,
            str(company.city if company.city else '') + str(company.state_id.name if company.state_id else ''),
            company.zip if company.zip else '',
            company.city if company.city else '', company.state_id.code if company.state_id else '', "006304638001")

        lower_body = """</PmtInf>
                    </CstmrCdtTrfInitn>
                </Document>"""

        body = upper_body + line_body + lower_body
        # filename = '/media/BACKUP/hsbc/' + self.name + '.xml'
        filename = self.name + '.xml'
        ####################File Encryption#########################################
        # pub_key, _ = pgpy.PGPKey.from_file("/home/ni3/Desktop/hsbc_bis_preprd_pgp_pub_key202302")
        # priv_key, _ = pgpy.PGPKey.from_file("/home/ni3/Desktop/id_rsa")

        #
        # # Construct a PGPMessage from a string:
        # message = pgpy.PGPMessage.new(body)
        # encrypted_message = pub_key.encrypt(message)
        # encrypted_message |= priv_key.sign(encrypted_message)
        # encrypted_message = str(encrypted_message)
        # filename = '/home/ni3/Desktop/' + self.name + '.pgp'

        # with open(filename, 'wb') as f:
        #     f.write(body)

        fp = StringIO()
        fp.write(body)
        out = base64.encodebytes(fp.getvalue())
        self.paymnt_report = out
        self.report_filename = filename
        self.state = 'file_generated'

        # gpg = gnupg.GPG(gnupghome="/root/.gnupg/")
        # gpg.encoding = 'utf-8'
        #
        # with open(filename, 'rb') as f:
        #     status = gpg.encrypt_file(f,['helpdesk@walplast.com'],output=filename)

    def update_to_bank(self):
        item_list = []
        today = datetime.now()

        upload_daymonth = datetime.strptime(self.bank_upload_date, DATE_FORMAT)
        create_daymonth = datetime.strptime(self.date, DATE_FORMAT)
        upload_month = upload_daymonth.strftime("%m")
        upload_day = upload_daymonth.strftime("%d")
        create_day = create_daymonth.strftime("%d")
        upload_year = upload_daymonth.strftime("%Y")
        pay_date = datetime.strptime(self.bank_upload_date, DATE_FORMAT).strftime("%d/%m/%Y")

        # file_extension = self.env['bank.payment'].search([("date", "=", self.bank_upload_date)])
        file_extension = self.env['bank.payment'].search([("bank_upload_date", "=", self.bank_upload_date)])
        ext = str(len(file_extension) + 700).zfill(3)

        # payment_lines = self.payment_lines_one2many.sudo().search([('payment_id', '=', self.id),('state', '=', 'approved')])
        payment_lines = self.payment_selected_one2many.sudo().search(
            [('selected_payment_id', '=', self.id), ('state', '=', 'approved')])

        if len(payment_lines) < 1:
            raise ValidationError(_('No Records Selected'))

        for rec in payment_lines:

            if not (rec.beneficiary_account_number and rec.ifsc_code):
                raise ValidationError(" Kindly Enter Bank Account No / IFSC Code or Delete the Payment Line")

            if not (rec.beneficiary_account_number or rec.ifsc_code):
                raise ValidationError(" Kindly Enter Bank Account No / IFSC Code or Delete the Payment Line")

            if rec.ifsc_code and str(rec.ifsc_code[:4]) == 'HDFC':
                transaction_type = 'I'
            elif rec.transaction_amount > 200000:
                transaction_type = 'R'
            else:
                transaction_type = 'N'

            item_list.append([transaction_type,
                              rec.beneficiary_code if rec.beneficiary_code else ext,
                              rec.beneficiary_account_number if rec.beneficiary_account_number else '',
                              rec.transaction_amount if rec.transaction_amount else '',
                              (rec.beneficiary_name).encode('utf-8') if rec.beneficiary_name else '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              (rec.description).encode('utf-8') if rec.description else '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              '',
                              pay_date,
                              '',
                              rec.ifsc_code if rec.ifsc_code else '',
                              (rec.bank_name).encode('utf-8') if rec.bank_name else '',
                              '',
                              (rec.beneficiary_email_id).encode('utf-8') if rec.beneficiary_email_id else '',
                              ])

        # if self.server_instance == 'Live':
        #     fileName="/tmp/" + self.company_id.bank_code  +  str(day)+str(month)+"." + str(ext)
        #     realfilename = "/" + self.company_id.bank_code + str(day)+str(month)+"." + str(ext)

        # else:
        #     fileName="/tmp/TEST_RRBI_RRBI"+str(day)+str(month)+"." + str(ext)
        #     realfilename = "/TEST_RRBI_RRBI"+str(day)+str(month)+"." + str(ext)

        fileName = "/tmp/" + self.company_id.bank_code + str(upload_day) + str(upload_month) + "." + str(ext)
        self.realfilename = realfilename = "/" + self.company_id.bank_code + str(upload_day) + str(
            upload_month) + "." + str(ext)

        with open(fileName, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            for val in item_list:
                writer.writerow(val)

        mount = os.path.isdir("/media/BACKUP/notmounted")
        print
        "Mount Not Found", mount

        destination = '/media/BACKUP/'
        # os.system('sudo  umount -f -a -t cifs -l /media/BACKUP')
        # sudo umount /media/BACKUP

        # p = Popen(['cp','-p','--preserve',fileName,destination])
        # p.wait()

        # shutil.copy(fileName, destination+realfilename)
        # shutil.copyfile(fileName, '/media/BACKUP/', *, follow_symlinks=True)
        if mount == True:
            print
            "#----------------------------Mount -Connected--Successfully -------------------------------"
            # os.system('sudo mount -t cifs -o username=bankuser,password=Bank@2004 //192.168.40.7/users/Public/BankPayments/tobank /media/BACKUP/' )
            # os.system('sudo mount -t cifs -o username=bankuser,password=Bank@2004,domain=miraj //192.168.40.7/f/bankautomation/tobank /media/BACKUP/' )
            # os.system('sudo mount -t cifs -o username=bankuser,password=Bank@2004,domain=miraj //192.168.40.7/f /media/BACKUP/' )
            # os.system('sudo mount -t cifs -o username=bankuser,password=Bk@$%4002,domain=drychem //192.168.40.7/HDFC/upload/hdfcforward/Walplast/src /media/BACKUP/' )
            os.system(
                'sudo mount -t cifs -o username=bankuser,password=Bk@$%4002 //192.168.40.7/Walplast/src /media/BACKUP/')

        try:
            os.system('sudo cp -f ' + fileName + ' /media/BACKUP/ ')
            print
            "File Transfering......................................."
            condition = 1

            self.sudo().update_payschedule_boolean(condition, entry_type='payment')


        except:
            print
            "This is an error message!"
            raise UserError(" File Not Copied. Contact IT Dept")

        finally:
            print
            "File Transfered Successfully"
            self.state = 'submitted_to_bank'

    def payment_report(self):
        self.ensure_one()

        payment_filter = self.payment_selected_one2many
        if len(payment_filter) < 1:
            raise ValidationError(_('No Records Found'))

        status = payment_no = second_heading = approval_status = ''
        name = 'Filtered Payments' + '(' + str(date.today()) + ')' + self.name

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet(name)
        fp = BytesIO()
        row_index = count = 0

        worksheet.col(0).width = 2000
        worksheet.col(1).width = 7000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 12000
        worksheet.col(6).width = 3000
        worksheet.col(7).width = 12000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 9000
        worksheet.col(10).width = 5000
        worksheet.col(11).width = 9000
        worksheet.col(12).width = 12000
        worksheet.col(13).width = 12000
        worksheet.col(14).width = 5000

        header_fields = [
            'Sr No.',
            'Client',
            'Org',
            'Date Account',
            'DocumentNo',
            'Description',
            'Code',
            'Beneficiary',
            'Total',
            'Beneficiary Account Number',
            'IFSC Code',
            'Bank',
            'Beneficiary Email',
            'Bank File Name'
        ]

        for index, value in enumerate(header_fields):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        for res in payment_filter:
            if res:
                count += 1

                worksheet.write(row_index, 0, count, base_style)
                worksheet.write(row_index, 1, self.company_id.name, base_style)
                worksheet.write(row_index, 2, res.ad_org, base_style)
                worksheet.write(row_index, 3, res.value_date, base_style)
                worksheet.write(row_index, 4, res.documentno, base_style)
                worksheet.write(row_index, 5, res.description, base_style)
                worksheet.write(row_index, 6, res.customer_reference_number, base_style)
                worksheet.write(row_index, 7, res.beneficiary_name, base_style)
                worksheet.write(row_index, 8, str(abs(res.transaction_amount)), base_style)
                worksheet.write(row_index, 9, res.beneficiary_account_number or '', base_style)
                worksheet.write(row_index, 10, res.ifsc_code or '', base_style)
                worksheet.write(row_index, 11, res.bank_name or '', base_style)
                worksheet.write(row_index, 12, res.beneficiary_email_id or '', base_style)
                worksheet.write(row_index, 13, res.selected_payment_id.realfilename or '', base_style)

                row_index += 1

        row_index += 1
        workbook.save(fp)
        out = base64.encodebytes(fp.getvalue())
        self.write({'pmt_output_file': out, 'pmt_export_file': name + '.xls'})

    def submit_manager(self):
        if self.date:
            self.state = 'submitted_to_manager'
            for records in self.invoice_lines_one2many:
                records.submit_manager_line()

        return True

    def delegate_user(self):
        if self.delegate_user_id:

            for res in self.delegate_user_id:
                for rec in self.invoice_lines_one2many:
                    if rec.user_id.id == self.env.user.id:
                        rec.delegate_user_id = self.delegate_user_id

        self.delegate_user_id = ''

        return True

    def select_all_payment_lines(self):
        for rec in self.payment_lines_one2many:
            rec.approve_payment()


class bank_payment_lines(models.Model):
    _name = "bank.payment.lines"
    _description = "Payment lines"

    name = fields.Char('Name')
    payment_id = fields.Many2one('bank.payment', string='Payment')
    transaction_type = fields.Selection(TRANSACTION_TYPE, string='Transaction Type')
    beneficiary_code = fields.Char('Beneficiary Code')
    beneficiary_account_number = fields.Char('Beneficiary Account Number')
    transaction_amount = fields.Float('Transaction Amount')
    beneficiary_name = fields.Char('Beneficiary Name')
    customer_reference_number = fields.Char('Customer Reference Number')
    value_date = fields.Char('Date')
    ifsc_code = fields.Char('IFSC Code')
    beneficiary_email_id = fields.Char('Beneficiary Email Id')
    payment_term = fields.Char('Payment Term')
    owner = fields.Char('Owner')
    owner_email = fields.Char('Owner Email')
    description = fields.Char('Description')
    documentno = fields.Char('Document No')
    check_invoice = fields.Boolean('Check')
    user_id = fields.Many2one('res.users', string='Owner')
    bank_name = fields.Char('Bank')
    ad_org = fields.Char(string="Org")
    opt_out_validation = fields.Boolean('Opt Out')
    state = fields.Selection(STATE, string='Status', track_visibility='onchange')
    c_payment_id = fields.Char("ERP Payment ID")
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company.id)
    c_bpartner_id = fields.Char("C_BPartner_ID")

    def approve_payment(self):
        if self.state == 'approved':
            self.state = 'draft'
            self.env['bank.payment.selected'].sudo().search([("lines_id", "=", self.id)]).unlink()
            self.env['bank.payment.selected'].sudo().search([("documentno", "=", self.documentno)]).unlink()

        else:
            if len(self.env['bank.payment.selected'].sudo().search(
                    [("selected_payment_id", "=", self.payment_id.id)])) < 1:

                vals_line = {
                    'selected_payment_id': self.payment_id.id,
                    'documentno': self.documentno,
                    'c_payment_id': self.c_payment_id,
                    'owner': self.owner,
                    'owner_email': self.owner_email,
                    'transaction_type': self.transaction_type,
                    'user_id': self.user_id.id,
                    'beneficiary_account_number': self.beneficiary_account_number,
                    'transaction_amount': self.transaction_amount,
                    'beneficiary_name': self.beneficiary_name,
                    'description': (self.beneficiary_name)[:20],  # self.description,
                    'value_date': self.value_date,
                    'ifsc_code': self.ifsc_code,
                    'bank_name': self.bank_name,
                    'beneficiary_email_id': self.beneficiary_email_id,
                    'ad_org': self.ad_org,
                    'state': 'approved',
                    'customer_reference_number': self.customer_reference_number,
                    'c_bpartner_id': self.c_bpartner_id,
                }

            else:
                for res in self.env['bank.payment.selected'].sudo().search(
                        [("selected_payment_id", "=", self.payment_id.id)]):
                    if res.documentno != self.documentno:

                        vals_line = {
                            'selected_payment_id': self.payment_id.id,
                            'documentno': self.documentno,
                            'c_payment_id': self.c_payment_id,
                            'owner': self.owner,
                            'owner_email': self.owner_email,
                            'transaction_type': self.transaction_type,
                            'user_id': self.user_id.id,
                            'beneficiary_account_number': self.beneficiary_account_number,
                            'transaction_amount': self.transaction_amount,
                            'beneficiary_name': self.beneficiary_name,
                            'description': (self.beneficiary_name)[:20],  # self.description,
                            'value_date': self.value_date,
                            'ifsc_code': self.ifsc_code,
                            'bank_name': self.bank_name,
                            'beneficiary_email_id': self.beneficiary_email_id,
                            'ad_org': self.ad_org,
                            'state': 'approved',
                            'customer_reference_number': self.customer_reference_number,
                            'c_bpartner_id': self.c_bpartner_id,
                        }
                    else:
                        raise ValidationError("Payment Already Present in 'Selected Payments' ")
            filter_id = self.payment_id.payment_selected_one2many.create(vals_line)
            filter_id.name = 'SP/' + str(filter_id.id)
            self.state = 'approved'


class bank_payment_selected(models.Model):
    _name = "bank.payment.selected"
    _description = "Selected Payment lines"

    name = fields.Char('Name')
    selected_payment_id = fields.Many2one('bank.payment', string='Payment')

    transaction_type = fields.Selection(TRANSACTION_TYPE, string='Transaction Type')
    beneficiary_code = fields.Char('Beneficiary Code')
    beneficiary_account_number = fields.Char('Beneficiary Account Number')
    transaction_amount = fields.Float('Transaction Amount')
    beneficiary_name = fields.Char('Beneficiary Name')
    customer_reference_number = fields.Char('Customer Reference Number')
    value_date = fields.Char('Date')
    ifsc_code = fields.Char('IFSC Code')
    beneficiary_email_id = fields.Char('Beneficiary Email Id')
    payment_term = fields.Char('Payment Term')
    owner = fields.Char('Owner')
    owner_email = fields.Char('Owner Email')
    description = fields.Char('Description')
    documentno = fields.Char('Document No')
    check_invoice = fields.Boolean('Check')
    user_id = fields.Many2one('res.users', string='Owner')
    bank_name = fields.Char('Bank')
    ad_org = fields.Char(string="Org")
    lines_id = fields.Integer(string="Lines ID")
    opt_out_validation = fields.Boolean('Opt Out')
    state = fields.Selection(STATE, string='Status', track_visibility='onchange')
    c_payment_id = fields.Char("ERP Payment ID")
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company.id)
    c_bpartner_id = fields.Char("C_BPartner_ID")
    log = fields.Char("Log")


class bank_invoice_selected(models.Model):
    _name = "bank.invoice.selected"
    _description = "Invoice selected"

    name = fields.Char('Name')
    invoice_selected_id = fields.Many2one('bank.payment', string='Selected Invoices')
    transaction_type = fields.Selection(TRANSACTION_TYPE, string='Transaction Type')
    beneficiary_code = fields.Char('Beneficiary Code')
    beneficiary_account_number = fields.Char('Beneficiary Account Number')
    transaction_amount = fields.Float('Transaction Amount')
    beneficiary_name = fields.Char('Beneficiary Name')
    customer_reference_number = fields.Char('Customer Reference Number')
    value_date = fields.Char('Date')
    ifsc_code = fields.Char('IFSC Code')
    beneficiary_email_id = fields.Char('Beneficiary Email Id')
    payment_term = fields.Char('Payment Term')
    owner = fields.Char('Owner')
    owner_email = fields.Char('Owner Email')
    description = fields.Char('Description')
    documentno = fields.Char('Document No')
    check_invoice = fields.Boolean(string="", nolabel="1")
    user_id = fields.Many2one('res.users', string='Owner')
    state = fields.Selection(STATE, string='Status', track_visibility='onchange')

    delegate_user_id = fields.Many2many('res.users', 'bank_invoice_selected_res_users_rel',
                                        string='Delegate To')
    delay_date = fields.Date('Delay Date')
    customercode = fields.Char(string="Code")
    totalamt = fields.Float(string="Total")
    allocatedamt = fields.Float(string="Allocated Amt")
    unallocated = fields.Float(string="Unallocated Amt")
    duedays = fields.Integer(string="Due Days")
    term_duedays = fields.Integer(string="Due Days(Inv date + Payment Term)")
    invoiceno = fields.Char(string="Inv No")
    ad_org = fields.Char(string="Org")
    c_bpartner_id = fields.Char("Partner ID")
    c_invoice_id = fields.Char("ERP Invoice ID")
    ad_org_id = fields.Many2one('org.master', string='Organisation')
    desc = fields.Char("Description")
    discard_tds = fields.Boolean()
    tds_amount = fields.Float("TDS")

    def approve_invoice(self):
        condition = ''
        unallocated = abs(self.unallocated)
        allowed_amount = self.transaction_amount
        log = ''
        vendor_config = self.env['vendor.config'].sudo().search(
            [('operation', '=', 'block_amount'), ('c_bpartner_id', '=', self.c_bpartner_id)
                , ('is_active', '=', True)])
        if vendor_config:
            if (self.transaction_amount - vendor_config.amount) > 0:
                allowed_amount = vendor_config.amount - self.transaction_amount
                log += str(vendor_config.amount) + " amount is blocked, hence" + str(
                    allowed_amount) + " is allowed"

        if self.state == 'approved':
            self.state = 'draft'
            self.env['bank.invoice.filter'].sudo().search([("selected_id", "=", self.id)]).unlink()
            self.env['bank.invoice.filter'].sudo().search([("documentno", "=", self.documentno)]).unlink()
            condition = 'deduct'
            self.invoice_selected_id._amount_calc(condition, unallocated)
        else:
            condition = 'add'
            self.invoice_selected_id._amount_calc(condition, unallocated)

            if len(self.env['bank.invoice.filter'].search(
                    [("invoice_filter_id", "=", self.invoice_selected_id.id)])) < 1:

                vals_line = {
                    'invoice_filter_id': self.invoice_selected_id.id,
                    'documentno': self.documentno,
                    'value_date': self.value_date,
                    'transaction_amount': allowed_amount,
                    'beneficiary_name': self.beneficiary_name,
                    'invoiceno': self.invoiceno,
                    'totalamt': abs(self.totalamt),
                    'allocatedamt': abs(self.allocatedamt),
                    'unallocated': abs(self.unallocated + self.tds_amount),
                    'unallocated2': abs(self.unallocated),
                    'duedays': self.duedays,
                    'payment_term': self.payment_term,
                    'term_duedays': self.term_duedays,
                    'customercode': self.customercode,
                    'ad_org': self.ad_org,
                    'selected_id': self.id,
                    'c_bpartner_id': self.c_bpartner_id,
                    'ad_org_id': self.invoice_selected_id.ad_org_id.id,
                    'c_invoice_id': self.c_invoice_id,
                    'company_id': self.invoice_selected_id.company_id.id,
                    'desc': self.desc,
                    'discard_tds': self.discard_tds,
                    'tds_amount': self.tds_amount,
                    'amount_log': log
                }

            else:

                for res in self.env['bank.invoice.filter'].search(
                        [("invoice_filter_id", "=", self.invoice_selected_id.id)]):
                    if res.documentno != self.documentno:

                        vals_line = {
                            'invoice_filter_id': self.invoice_selected_id.id,
                            'documentno': self.documentno,
                            'value_date': self.value_date,
                            'transaction_amount': allowed_amount,
                            'beneficiary_name': self.beneficiary_name,
                            'invoiceno': self.invoiceno,
                            'totalamt': abs(self.totalamt),
                            'allocatedamt': abs(self.allocatedamt),
                            'unallocated': abs(self.unallocated + self.tds_amount),
                            'unallocated2': abs(self.unallocated),
                            'duedays': self.duedays,
                            'payment_term': self.payment_term,
                            'term_duedays': self.term_duedays,
                            'customercode': self.customercode,
                            'ad_org': self.ad_org,
                            'lines_id': self.id,
                            'c_bpartner_id': self.c_bpartner_id,
                            'ad_org_id': self.invoice_selected_id.ad_org_id.id,
                            'c_invoice_id': self.c_invoice_id,
                            'company_id': self.invoice_selected_id.company_id.id,
                            'desc': self.desc,
                            'discard_tds': self.discard_tds,
                            'tds_amount': self.tds_amount,
                            'amount_log': log
                        }
                    else:
                        raise ValidationError("Invoice Already Present in 'Filtered Invoices' ")

            filter_id = self.invoice_selected_id.invoice_filter_one2many.create(vals_line)
            # self.invoice_selected_id.invoice_filter_one2many = invoice_lines
            filter_id.name = 'FI/' + str(filter_id.id)
            self.state = 'approved'


class bank_invoice_filter(models.Model):
    _name = "bank.invoice.filter"
    _description = "Filtered Invoice"

    name = fields.Char('Name')
    invoice_filter_id = fields.Many2one('bank.payment', string='Filter Invoices')
    transaction_type = fields.Selection(TRANSACTION_TYPE, string='Transaction Type')
    beneficiary_code = fields.Char('Beneficiary Code')
    beneficiary_account_number = fields.Char('Beneficiary Account Number')
    transaction_amount = fields.Float('Transaction Amount')
    beneficiary_name = fields.Char('Beneficiary Name')
    customer_reference_number = fields.Char('Customer Reference Number')
    value_date = fields.Char('Date')
    ifsc_code = fields.Char('IFSC Code')
    beneficiary_email_id = fields.Char('Beneficiary Email Id')
    payment_term = fields.Char('Payment Term')
    owner = fields.Char('Owner')
    owner_email = fields.Char('Owner Email')
    description = fields.Char('Description')
    documentno = fields.Char('Document No')
    check_invoice = fields.Boolean(string="", nolabel="1")
    user_id = fields.Many2one('res.users', string='Owner')
    state = fields.Selection(STATE, string='Status', track_visibility='onchange')

    # delegate_user_id = fields.Many2many('res.users', 'bank_invoice_filter_res_users_rel',  string='Delegate To')
    delay_date = fields.Date('Delay Date')
    customercode = fields.Char(string="Code")
    totalamt = fields.Float(string="Total")
    allocatedamt = fields.Float(string="Allocated Amt")
    unallocated = fields.Float(string="Unallocated Amt")
    duedays = fields.Integer(string="Due Days (Inv Date)")
    term_duedays = fields.Integer(string="Due Days(Inv date + Payment Term)")
    invoiceno = fields.Char(string="Inv No")
    ad_org = fields.Char(string="Org")
    selected_id = fields.Integer(string="Selected ID")
    lines_id = fields.Integer(string="Lines ID")
    company_id = fields.Many2one('res.company')
    ad_org_id = fields.Many2one('org.master', string='Organisation')
    c_bpartner_id = fields.Char("Partner ID")
    log = fields.Text("Log")
    c_invoice_id = fields.Char("ERP Invoice ID")
    unallocated2 = fields.Float(string="Unallocated")
    invoice_date = fields.Date("Invoice Date")
    desc = fields.Char("Description")
    amount_log = fields.Char("Amount log")
    discard_tds = fields.Boolean()
    tds_amount = fields.Float("TDS")

    @api.onchange('unallocated')
    def onchange_unallocated(self):
        if self.unallocated and not self.discard_tds:
            if self.unallocated > self.unallocated2:
                raise ValidationError(" Unallocated Amount cannot be greater than Allocated Amount")

    def update_isselfservice_boolean(self):
        if self.invoice_filter_id.state != 'erp_posted':
            self.invoice_filter_id.update_isselfservice_boolean(condition=0, documentno=self.documentno)
        else:
            raise ValidationError(" Entry is Already Posted. Cannot Dissapprove the Invoice")


class bank_invoice_lines(models.Model):
    _name = "bank.invoice.lines"
    _description = "Invoice lines"

    name = fields.Char('Name')
    invoice_id = fields.Many2one('bank.payment', string='Invoices')
    transaction_type = fields.Selection(TRANSACTION_TYPE, string='Transaction Type')
    beneficiary_code = fields.Char('Beneficiary Code')
    beneficiary_account_number = fields.Char('Beneficiary Account Number')
    transaction_amount = fields.Float('Transaction Amount')
    beneficiary_name = fields.Char('Beneficiary Name')
    customer_reference_number = fields.Char('Customer Reference Number')
    value_date = fields.Char('Date')
    ifsc_code = fields.Char('IFSC Code')
    beneficiary_email_id = fields.Char('Beneficiary Email Id')
    payment_term = fields.Char('Payment Term')
    owner = fields.Char('Owner')
    owner_email = fields.Char('Owner Email')
    description = fields.Char('Description')
    documentno = fields.Char('Document No')
    check_invoice = fields.Boolean(string="", nolabel="1")
    user_id = fields.Many2one('res.users', string='Owner')
    state = fields.Selection(STATE, string='Status', track_visibility='onchange')

    delegate_user_id = fields.Many2many('res.users', 'bank_invoice_lines_res_users_rel', string='Delegate To')
    delay_date = fields.Date('Delay Date')
    customercode = fields.Char(string="Code")
    totalamt = fields.Float(string="Total")
    allocatedamt = fields.Float(string="Allocated Amt")
    unallocated = fields.Float(string="Unallocated Amt")
    duedays = fields.Integer(string="Due Days")
    term_duedays = fields.Integer(string="Due Days(Inv date + Payment Term)")
    over_duedays = fields.Integer(string="OverDue Days")
    invoiceno = fields.Char(string="Inv No")
    ad_org = fields.Char(string="Org")
    c_bpartner_id = fields.Char("Partner ID")
    c_invoice_id = fields.Char("ERP Invoice ID")
    ad_org_id = fields.Many2one('org.master', string='Organisation')
    desc = fields.Char("Description")
    tds_amount = fields.Float("TDS")
    discard_tds = fields.Boolean()

    def submit_manager_line(self):

        for records in self:
            if records.owner_email:
                template_id = \
                    self.env['ir.model.data'].get_object_reference('external_db_connect', 'confirm_invoice_action')[1]
                email_template_obj = self.env['mail.template'].browse(template_id)
                if template_id:
                    values = email_template_obj.generate_email(self.id, fields=None)
                    values['email_from'] = records.invoice_id.user_id.login
                    values['email_to'] = records.owner_email
                    values['res_id'] = False
                    mail_mail_obj = self.env['mail.mail']
                    msg_id = mail_mail_obj.sudo().create(values)
                    self.mail_date = datetime.now()
                    if msg_id:
                        msg_id.sudo().send()

        return True

    def approve_invoice(self):
        allowed_amount = self.transaction_amount
        log = ''
        vendor_config = self.env['vendor.config'].sudo().search(
            [('operation', '=', 'block_amount'), ('c_bpartner_id', '=', self.c_bpartner_id)
                , ('is_active', '=', True)])
        if vendor_config:
            if (self.transaction_amount - vendor_config.amount) > 0:
                allowed_amount = vendor_config.amount - self.transaction_amount
                log += str(vendor_config.amount) + " amount is blocked, hence" + str(allowed_amount) + " is allowed"

        if self.state == 'approved':
            self.state = 'draft'
            self.check_invoice = False
            self.env['bank.invoice.filter'].sudo().search([("lines_id", "=", self.id)]).unlink()
            self.env['bank.invoice.filter'].sudo().search([("documentno", "=", self.documentno)]).unlink()

        else:
            if len(self.env['bank.invoice.filter'].search([("invoice_filter_id", "=", self.invoice_id.id)])) < 1:

                vals_line = {
                    'invoice_filter_id': self.invoice_id.id,
                    'documentno': self.documentno,
                    'value_date': self.value_date,
                    'transaction_amount': allowed_amount,
                    'beneficiary_name': self.beneficiary_name,
                    'invoiceno': self.invoiceno,
                    'totalamt': abs(self.totalamt),
                    'allocatedamt': abs(self.allocatedamt),
                    'unallocated': abs(self.unallocated + self.tds_amount),
                    'unallocated2': abs(self.unallocated),
                    'duedays': self.duedays,
                    'payment_term': self.payment_term,
                    'term_duedays': self.term_duedays,
                    'customercode': self.customercode,
                    'ad_org': self.ad_org,
                    'lines_id': self.id,
                    'c_bpartner_id': self.c_bpartner_id,
                    'ad_org_id': self.invoice_id.ad_org_id.id,
                    'c_invoice_id': self.c_invoice_id,
                    'state': 'draft',
                    'tds_amount': self.tds_amount,
                    'company_id': self.invoice_id.company_id.id,
                    'desc': self.desc,
                    'amount_log': log
                }

            else:
                for res in self.env['bank.invoice.filter'].search([("invoice_filter_id", "=", self.invoice_id.id)]):
                    if res.documentno != self.documentno:

                        vals_line = {
                            'invoice_filter_id': self.invoice_id.id,
                            'documentno': self.documentno,
                            'value_date': self.value_date,
                            'transaction_amount': allowed_amount,
                            'beneficiary_name': self.beneficiary_name,
                            'invoiceno': self.invoiceno,
                            'totalamt': abs(self.totalamt),
                            'allocatedamt': abs(self.allocatedamt),
                            'unallocated': abs(self.unallocated + self.tds_amount),
                            'unallocated2': abs(self.unallocated),
                            'duedays': self.duedays,
                            'payment_term': self.payment_term,
                            'term_duedays': self.term_duedays,
                            'customercode': self.customercode,
                            'ad_org': self.ad_org,
                            'lines_id': self.id,
                            'c_bpartner_id': self.c_bpartner_id,
                            'ad_org_id': self.invoice_id.ad_org_id.id,
                            'c_invoice_id': self.c_invoice_id,
                            'state': 'draft',
                            'tds_amount': self.tds_amount,
                            'company_id': self.invoice_id.company_id.id,
                            'desc': self.desc,
                            'amount_log': log
                        }
                    else:
                        raise ValidationError("Invoice Already Present in 'Filtered Invoices' ")
            filter_id = self.invoice_id.invoice_filter_one2many.create(vals_line)
            filter_id.name = 'FI/' + str(filter_id.id)
            self.state = 'approved'
            self.check_invoice = True


class bank_invoice_summary(models.Model):
    _name = "bank.invoice.summary"
    _description = "Vendor Summary Invoice"

    name = fields.Char('Name')
    vendor_summary_id = fields.Many2one('bank.payment', string='Summary Invoices')
    beneficiary_code = fields.Char('Beneficiary Code')
    beneficiary_name = fields.Char('Beneficiary Name')
    transaction_amount = fields.Float('Transaction Amount')

    owner = fields.Char('Owner')
    check_invoice = fields.Boolean(string="", nolabel="1")
    user_id = fields.Many2one('res.users', string='Owner')
    state = fields.Selection(STATE, string='Status', track_visibility='onchange')

    totalamt = fields.Float(string="Total")
    allocatedamt = fields.Float(string="Allocated Amt")
    unallocated = fields.Float(string="Unallocated Amt")
    ad_org = fields.Char(string="Org")

    company_id = fields.Many2one('res.company')
    ad_org_id = fields.Many2one('org.master', string='Organisation')
    c_bpartner_id = fields.Char("Partner ID")
    log = fields.Text("Log")
    unallocated2 = fields.Float(string="Unallocated")
    open_balance = fields.Float(string="Open Balance")

    filtered_line_ids = fields.Many2many('bank.invoice.filter', string='Filtered Lines')

    def generate_payment_webservice(self):
        if self.state != 'approved' and self.vendor_summary_id.state == "validated":
            filter_line_ids = []
            for res in self.filtered_line_ids:
                if res.state != 'approved':
                    filter_line_ids.append(res.id)

            if len(filter_line_ids) < 1:
                raise ValidationError(_('Payment Has been Already Created in the Filtered Invoices. Kindly Check.'))

            if abs(round(self.open_balance)) >= abs(round(self.totalamt)) and self.filtered_line_ids:
                response = self.vendor_summary_id.generate_payment_webservice(filter_ids=filter_line_ids,
                                                                              single_entry=True)
                self.state = 'approved'
                self.log = response
            else:
                documentno_log = "Entry Not Validated as Total Open Balance (%s)\
                            of Vendor is less than the Total Invoice Amount (%s)" % (self.open_balance, self.totalamt)
                raise ValidationError(documentno_log)
        else:
            raise ValidationError("Record is in Approved State")


class wizard_reject(models.TransientModel):
    _name = 'wizard.reject'

    @api.model
    def _default_invoice_id(self):
        if 'default_invoice_id' in self._context:
            return self._context['default_invoice_id']
        if self._context.get('active_model') == 'bank.invoice.lines':
            return self._context.get('active_id')
        return False

    def delay_invoice(self):

        create_date = dateutil.parser.parse(self.create_date).date()
        delay_days = int(self.delay_days)
        delay_date = create_date + timedelta(days=delay_days)
        if self.invoice_id.user_id.id == self.env.uid or \
                self.invoice_id.user_id.employee_id.parent_id.user_id.id == self.env.uid or \
                self.env.uid in [x.id for x in self.invoice_id.delegate_user_id]:
            if self.invoice_id:
                self.invoice_id.delay_date = delay_date
                self.invoice_id.state = 'rejected'

        else:
            raise UserError("Not Authorised")

    delay_days = fields.Char('Delay By Days')
    invoice_id = fields.Many2one('bank.invoice.lines', default=_default_invoice_id)


class ErpBankMaster(models.Model):
    _name = "erp.bank.master"
    _description = "Bank Master"

    c_bankaccount_id = fields.Char('Bankaccount Id')
    ad_client_id = fields.Char('Client Id')
    ad_org_id = fields.Char('Org Id')
    active = fields.Boolean('Active')
    c_bank_id = fields.Char('C_Bank_Id')
    bankaccounttype = fields.Selection([
        ('D', 'Card'),
        ('B', 'Cash'),
        ('C', 'Checking'),
        ('S', 'Savings')],
        string='Bankaccounttype')
    accountno = fields.Char('Accountno')
    currentbalance = fields.Float('Currentbalance')
    creditlimit = fields.Float('Creditlimit')
    default = fields.Boolean('Default')
    bank = fields.Selection([('hsbc', 'HSBC'), ('hdfc', 'HDFC')], string='Bank')
    hdfc_default = fields.Boolean('HDFC Default')
    # hsbc_default = fields.Boolean('HSBC Default')
    name = fields.Char('Name')
    value = fields.Char('Value')
    company_id = fields.Many2one('res.company', string='Company')
    ad_org = fields.Many2one('org.master', string='Organisation', domain="[('company_id','=',company_id)]")

    def process_update_erp_c_bankaccount_queue(self):
        print("process_update_erp_c_bankaccount_queue-----------------------------------")
        conn_pg = None
        config_id = self.env['external.db.configuration'].sudo().search([('state', '=', 'connected')], limit=1)
        if config_id:

            print
            "#-------------Select --TRY----------------------#"
            try:
                conn_pg = psycopg2.connect(dbname=config_id.database_name, user=config_id.username,
                                           password=config_id.password, host=config_id.ip_address, port=config_id.port)
                pg_cursor = conn_pg.cursor()

                query = "select c_bankaccount_id,ad_client_id,ad_org_id,c_bank_id,bankaccounttype,accountno,name,value \
                        from adempiere.C_BankAccount where isactive = 'Y'   "

                pg_cursor.execute(query)
                records = pg_cursor.fetchall()

                if len(records) > 0:
                    portal_c_bankaccount_id = [x.c_bankaccount_id for x in self.env['erp.bank.master'].search([])]

                    for record in records:
                        c_bankaccount_id = (str(record[0]).split('.'))[0]

                        if c_bankaccount_id not in portal_c_bankaccount_id:
                            ad_client_id = (str(record[1]).split('.'))[0]
                            company_id = self.env['res.company'].search([('ad_client_id', '=', ad_client_id)], limit=1)

                            vals_line = {
                                'active': True,
                                'c_bankaccount_id': c_bankaccount_id,
                                'ad_client_id': ad_client_id,
                                'ad_org_id': (str(record[2]).split('.'))[0],
                                'c_bank_id': (str(record[3]).split('.'))[0],
                                'bankaccounttype': record[4],
                                'accountno': (str(record[5]).split('.'))[0],
                                'name': record[6],
                                'value': record[7],
                                'company_id': company_id.id,
                            }

                            self.env['erp.bank.master'].create(vals_line)
                            print
                            "----------- Bank Created in CRM  --------", record[6]


            except psycopg2.DatabaseError as e:
                if conn_pg:
                    conn_pg.rollback()
                print
                '#----------- Error %s' % e

            finally:
                if conn_pg: conn_pg.close()
                print
                "#--------------Select --44444444--Finally----------------------#", pg_cursor


class ErpRepresentativeApprover(models.Model):
    _name = "erp.representative.approver"
    _order = "sequence"

    name = fields.Char(string='Name')
    owner_id = fields.Many2one('res.users', string='Representative')
    sequence = fields.Integer(string='Representative Sequence')
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company.id)
    salesrep_id = fields.Char('Representative ID')
    hierarchy_bool = fields.Boolean(string='Hierarchy Present?')
    line_ids = fields.One2many('erp.representative.matrix', 'approver_id', string="Lines")

    @api.onchange('owner_id', 'company_id')
    def onchange_owner_id(self):
        if self.owner_id: self.name = self.owner_id.name + ' - ' + self.company_id.short_name

    @api.model
    def create(self, vals):
        result = super(ErpRepresentativeApprover, self).create(vals)
        result.sequence = self.env['erp.representative.approver'].search([])[-1].sequence + 1
        return result

    def unlink(self):
        for order in self:
            if self.env.uid != 1 or not self.user_has_groups('sales_meet.group_it_user'):
                raise UserError(_('Only IT User can delete records'))
        return super(ErpRepresentativeApprover, self).unlink()


class ErpRepresentativeMatrix(models.Model):
    _name = "erp.representative.matrix"
    _description = "Representative Matrix"

    name = fields.Char(string='Matrix')
    approver_id = fields.Many2one('erp.representative.approver', string="Approver")
    user_id = fields.Many2one('res.users', string='User', copy=False, index=True)
    min_amt = fields.Float(string="Min", digits=(16, 3))
    max_amt = fields.Float(string="Max", digits=(16, 3))
