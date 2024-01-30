from odoo import http
from odoo.http import request
import os
import json
import time
import base64
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.http import Response


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
mainfields = ['id', 'name']
company_id = 3
# todaydate = date.today()

headers = {'Content-Type': 'application/json',}
# image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static/img'))

class WpExpenseController(http.Controller):

    @http.route('/wmvdapi/create_expense', methods=["POST"], type='json', auth='user')
    def create_expense(self, expense_id=None, user_id=None, product_id=None, claimed_amount=None, 
        meeting_id=None, expense_date=None, description=None, image=None):
        print("------------/wmvdapi/create_expense -----------", user_id)


        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
        # work_location = employee_id.work_location

        product = retailer = partner = stage = activity = ''
        if product_id: product = request.env['product.product'].sudo().search([('id', '=', product_id)])

        if meeting_id: meeting = request.env['calendar.event'].sudo().search([('id', '=', meeting_id)])

        validate_expense = request.env['hr.expense'].sudo().validate_expense(emp_id=employee_id.id, 
                              product_id=product.id,
                              product_name=product.name,
                              expense_date=expense_date,
                              meeting_id=meeting.id,
                              total_amount=claimed_amount )
        
        if validate_expense:
            return {'success': None, 'error': validate_expense}

        users_rec = request.env['res.users'].sudo().search([('id', '=', user_id),('active', '=', True)], limit=1)

        name = request.env['hr.expense'].sudo().name_creation(product_name=product.name, date=expense_date)

        expense_vals = {
                'name' : name or '',
                'product_id': product.id or None,
                'meeting_id': meeting.id or None,
                'employee_id': employee_id.id or None,
                'claimed_amount': claimed_amount,
                'unit_amount': claimed_amount,
                'date': expense_date,
                # 'work_location' : work_location,
                'meeting_address': meeting.reverse_location or '',
                'reference': description or '',
                'mobile_id': expense_id,
                                
            }

        # rec = models.execute_kw(db, uid, password, 'product.template', 'read', [[id]], {'fields': ['id', 'name', 'image']})
        # img_data = rec[0]['image']
        # data_id = rec[0]['id']
        

        expense = request.env['hr.expense'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(expense_vals)

        if image:
            for res in image:

                attachment_id = request.env['ir.attachment'].with_context(mail_auto_subscribe_no_notify=True).sudo().create({
                    'name': name,
                    'type': 'binary',
                    'datas': res, #image, #image.decode('base64'), #base64.b64encode(image),
                    'store_fname': name,
                    'res_model': expense._name,
                    'res_id': expense.id,
                    'extension' : '.png',
                    'mimetype': 'image/png',
                    'index_content': 'image'
                })

        bank_journal_id=  request.env['account.journal'].search([('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)], limit=1)
        journal_id = request.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', company_id)], limit=1)


        print("xxxxxxxxxxxxx", bank_journal_id, journal_id )

        expense_sheet_vals= {
                'name': expense.name or '',
                'expense_line_ids': [(6, 0, [expense.id])],
                'employee_id': expense[0].employee_id.id,
                'total_amount' : expense.unit_amount,
                'expense_meeting_id': expense.meeting_id.id,
                'meeting_date': meeting.expense_date or '',
                'expense_date': expense.date, 
                'expense_submit': True,
                'company_id': company_id,
                'department_id': employee_id.department_id.id,
                'journal_id': journal_id.id,
                'bank_journal_id': bank_journal_id.id,
        }

        expense_sheet = request.env['hr.expense.sheet'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(expense_sheet_vals)

        vals = {
                'id': expense_id or '',
                'portal_id' : expense.id,
                'product_id': product.id or None,
                'product_name': product.name or '',
                'meeting_id': meeting.id or None,
                'meeting_name': meeting.name or '',
                'employee_id': employee_id.id or None,
                'employee_name': employee_id.name or '',
                'claimed_amount': claimed_amount,
                'date': expense_date,
                'user_id': users_rec.id or None,
                'user_name': users_rec.name or '',
                'description': description or '',
        }

        response = {'expense' : vals}
        return {'success': response, 'error': None}


    @http.route('/wmvdapi/get_expense_products', auth='user', methods=["POST"], type='json')
    def get_expense_products(self, grade_id=None):
        print("------------/wmvdapi/get_expense_products -----------")
        if grade_id:
            result = []
            grade_ids = request.env['grade.master'].sudo().search([('id', '=', grade_id)] )
            for res in grade_ids.grade_line_ids:
                vals = {
                        'id': res.name.id,
                        'name':res.name.name,
                        'amount': float(res.value) if res.value else 0.0,
                }
                result.append(vals)
        else:
            result = request.env['product.product'].search([('can_be_expensed', '=', True)]).read(mainfields)

        product = {'success': result or {}, 'error': None}
        return product

    @http.route('/wmvdapi/get_user_visit_list', auth='user', methods=["POST"], type='json')
    def get_user_visit_list(self, user_id=None, date=None):
        start = time.time()
        print("------------/wmvdapi/get_user_visit_list -----------", user_id, date)
        result = request.env['calendar.event'].search([('user_id', '=', user_id),
                                ('meeting_type','=','check-in'),
                                ('expense_date', '=', date),
                                ('name','!=',False),
                                '|',('active','=',False),('active','!=',False)]).read(mainfields)
        end = time.time()
        # print "------------- END get_user_visit_list -------", end-start
        return {'success': result or {}, 'error': None}


    @http.route('/wmvdapi/get_user_expenses', auth='user', methods=["POST"], type='json')
    def get_user_expenses(self, user_id=None, date=None):
        print("------------/wmvdapi/get_user_expenses -----------")
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1).id
        users_rec = request.env['res.users'].sudo().search([('id', '=', user_id),('active', '=', True)], limit=1)

        if date:
            domain = [('employee_id', '=', employee_id),('date','=',date)]
        else:
            domain = [('employee_id', '=', employee_id)]

        expense_rec = request.env['hr.expense'].sudo().search(domain)
        expense_list = []
        if expense_rec:
            for res in expense_rec:
                vals = {
                    'id': res.mobile_id or '',
                    'portal_id' : res.id,
                    'product_id': res.product_id.id or None,
                    'product_name': res.product_id.name or '',
                    'meeting_id': res.meeting_id.id or None,
                    'meeting_name': res.meeting_id.name or '',
                    'employee_id': res.employee_id.id or None,
                    'employee_name': res.employee_id.name or '',
                    'claimed_amount': res.total_amount,
                    'date': res.date,
                    'user_id': users_rec.id or None,
                    'user_name': users_rec.name or '',
                    'description': res.reference or '',
                }
                expense_list.append(vals)

            response = {'count' : len(expense_rec), 'list': expense_list}
            return {'success': response, 'error': None}
        else:
            response = {'count' : 0, 'list': []}
            return {'success': response, 'error': None}
