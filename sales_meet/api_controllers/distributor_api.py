from odoo import http
from odoo.http import request
import json
import time
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"

class CNReceivedDashboard(http.Controller):

    # @http.route('/wmvdapi/distributor_pays_retailer', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/distributor_pays_retailer', auth='public', methods=["POST"], type="json")
    def distributor_pays_retailer(self, payment_id, user_type=False, distributor_id=False, retailer_id=False, payment_mode=False):
        print("------------/wmvdapi/distributor_pays_retailer -----------", payment_id, user_type, distributor_id, retailer_id, payment_mode)
        resp = request.env['barcode.marketing.check'].sudo().create_coupon_credit(payment_id, user_type, distributor_id, retailer_id, payment_mode)
        print("--------------- Response --", resp, type(resp))
        if isinstance(resp, str):
            return {'success': None, 'error': resp}
            
        else:
            return {'success': resp, 'error': None}

    # @http.route('/wmvdapi/distributor_dashboard', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/distributor_dashboard', auth='public', methods=["POST"], type="json")
    def distributor_dashboard(self, distributor_id, user_type):
        """ Distributor Dashboard """
        print("------------/wmvdapi/distributor_dashboard -----------", distributor_id)
        if user_type == 'Distributor':
            cn_received_domain = [('mobile_bool', '=', True),
                  '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                  '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
                  '|',('cn_raised_date', '!=', False),('cn_raised_date2', '!=', False),
                  ('second_flag', '=', True),('barcode_marketing_id','in', (10,11))]

            cn_received_domain1 = [('mobile_bool', '=', True),
                  ('partner_id', '=', distributor_id),
                  ('distributor_paid_bool', '=', True),
                  ('cn_raised_date', '!=', False),('second_flag', '=', False)]



            cn_pending_domain = [('mobile_bool', '=', True),
                  '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                  '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
                  '|',('cn_raised_date', '=', False),('cn_raised_date2', '=', False),
                  ('second_flag', '=', True),('barcode_marketing_id','in', (10,11))]

            cn_pending_domain1 = [('mobile_bool', '=', True),
                  ('partner_id', '=', distributor_id),
                  ('distributor_paid_bool', '=', True),
                  ('cn_raised_date', '=', False),('second_flag', '=', False)]



            paid_retailer_domain = [('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                  '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
                  ('second_flag', '=', True),('barcode_marketing_id','in', (10,11))]

            paid_retailer_domain1 = [('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  ('partner_id', '=', distributor_id),
                  ('distributor_paid_bool', '=', True),('second_flag', '=', False)]



            unpaid_retailer_domain = [('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                  '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False),
                  ('second_flag', '=', True),('barcode_marketing_id','in', (10,11))]

            unpaid_retailer_domain1 = [('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  ('partner_id', '=', distributor_id), ('distributor_paid_bool', '=', False),
                  ('second_flag', '=', False)]

            cn_received_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(cn_received_domain))]
            cn_received_amount1 = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(cn_received_domain1))]

            cn_pending_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(cn_pending_domain))]
            cn_pending_amount1 = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(cn_pending_domain1))]


            paid_retailer_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(paid_retailer_domain))]
            paid_retailer_amount1 = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(paid_retailer_domain1))]

            unpaid_retailer_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(unpaid_retailer_domain))]
            unpaid_retailer_amount1 = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(unpaid_retailer_domain1))]


            response = {'amount_paid' : ( (paid_retailer_amount[0] if paid_retailer_amount else 0) + \
                            (paid_retailer_amount1[0] if paid_retailer_amount1 else 0)) or 0,

                        'amount_yet_to_be_paid': ( (unpaid_retailer_amount[0] if unpaid_retailer_amount else 0) + \
                            (unpaid_retailer_amount1[0] if unpaid_retailer_amount1 else 0)) or 0,


                        'creditnote_received': ( (cn_received_amount[0] if cn_received_amount else 0) + \
                            (cn_received_amount1[0] if cn_received_amount1 else 0)) or 0,

                        'creditnote_yet_to_be_received': ( (cn_pending_amount[0] if cn_pending_amount else 0) + \
                            (cn_pending_amount1[0] if cn_pending_amount1 else 0)) or 0, }

            return {'success': response, 'error': None}

    # @http.route('/wmvdapi/creditnote_received', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/creditnote_received', auth='public', methods=["POST"], type="json")
    def creditnote_received(self, distributor_id):
        """ CN received to Distributor """
        print("------------/wmvdapi/creditnote_received -----------", distributor_id)
        data = {}
        amount_total= cn_received_count = 0
        cn_received_coupons= []

        bml = request.env['barcode.marketing.line']

        # domain = ['|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
        #          ('mobile_bool', '=', True),
        #           '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
        #           '|',('cn_raised_date', '=', False),('cn_raised_date2', '=', False),]

        domain1 = [('barcode_marketing_id','in', (10,11)), ('second_flag', '=', True),
                 ('mobile_bool', '=', True),
                 '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                 '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
                  '|',('cn_raised_date', '!=', False),('cn_raised_date2', '!=', False),]

        domain = [('partner_id', '=', distributor_id),('second_flag', '=', False),
                 ('mobile_bool', '=', True),
                  ('distributor_paid_bool', '=', True),('cn_raised_date', '!=', False)]


        cn_received1 = bml.sudo().search(domain1)

        if cn_received1:
            cn_received_count = len(cn_received1)
            amount_total1 = [sum(x.amount for x in cn_received1 )]
            amount_total = amount_total1[0]

            for res in cn_received1:
                if res.scanned_datetime2:
                    check_in_date = datetime.strptime(str(res.scanned_datetime2), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id2.name, 
                        'distributor_id' : res.partner_id2.id,
                        'user' : res.user_id2.name, 
                        'amount' : res.amount,
                    }
                cn_received_coupons.append((data))

        cn_received = bml.sudo().search(domain)

        if cn_received:
            cn_received_count += len(cn_received)
            amount_total1 = [sum(x.amount for x in cn_received )]
            amount_total += amount_total1[0]

            for res in cn_received:
                if res.updated_datetime:
                    check_in_date = datetime.strptime(str(res.updated_datetime), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data1 = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id.name, 
                        'distributor_id' : res.partner_id.id,
                        'user' : res.user_id.name , 
                        'amount' : res.amount,
                    }
                cn_received_coupons.append((data1))

            # response = {'list': all_scan_coupons}
        response = {'count' : cn_received_count, 
                    'list': cn_received_coupons,
                    'amount_total' : amount_total,}

        return {'success': response, 'error': None}


    # @http.route('/wmvdapi/creditnote_pending', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/creditnote_pending', auth='public', methods=["POST"], type="json")
    def creditnote_pending(self, distributor_id):
        """ CN Pending to Distributor """
        print("------------/wmvdapi/creditnote_pending -----------", distributor_id)
        data = {}
        amount_total= cn_pending_count = 0
        cn_pending_coupons= []

        bml = request.env['barcode.marketing.line']

        # domain = ['|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
        #          ('mobile_bool', '=', True),
        #           '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
        #           '|',('cn_raised_date', '=', False),('cn_raised_date2', '=', False),]

        domain1 = [('barcode_marketing_id','in', (10,11)), ('second_flag', '=', True),
                 ('mobile_bool', '=', True),
                 '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                 '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True),
                  '|',('cn_raised_date', '=', False),('cn_raised_date2', '=', False),]

        domain = [('partner_id', '=', distributor_id),('second_flag', '=', False),
                 ('mobile_bool', '=', True),
                  ('distributor_paid_bool', '=', True),('cn_raised_date', '=', False)]


        cn_pending1 = bml.sudo().search(domain1)

        if cn_pending1:
            cn_pending_count = len(cn_pending1)
            amount_total1 = [sum(x.amount for x in cn_pending1 )]
            amount_total = amount_total1[0]

            for res in cn_pending1:
                if res.scanned_datetime2:
                    check_in_date = datetime.strptime(str(res.scanned_datetime2), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id2.name, 
                        'distributor_id' : res.partner_id2.id,
                        'user' : res.user_id2.name, 
                        'amount' : res.amount,
                    }
                cn_pending_coupons.append((data))

        cn_pending = bml.sudo().search(domain)

        if cn_pending:
            cn_pending_count += len(cn_pending)
            amount_total1 = [sum(x.amount for x in cn_pending )]
            amount_total += amount_total1[0]

            for res in cn_pending:
                if res.updated_datetime:
                    check_in_date = datetime.strptime(str(res.updated_datetime), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data1 = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id.name, 
                        'distributor_id' : res.partner_id.id,
                        'user' : res.user_id.name , 
                        'amount' : res.amount,
                    }
                cn_pending_coupons.append((data1))

            # response = {'list': all_scan_coupons}
        response = {'count' : cn_pending_count, 
                    'list': cn_pending_coupons,
                    'amount_total' : amount_total,}

        return {'success': response, 'error': None}


    # @http.route('/wmvdapi/paid_retailer', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/paid_retailer', auth='public', methods=["POST"], type="json")
    def paid_retailer(self, distributor_id):
        """ Amount Paid TO Retailer """
        print("------------/wmvdapi/paid_retailer -----------", distributor_id)
        data = {}
        data1 = {}
        amount_total= paid_retailer_count = 0
        paid_retailer_coupons= []

        bml = request.env['barcode.marketing.line']

        # domain = ['|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
        #          ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
        #           '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False)]

        domain1 = [('barcode_marketing_id','in', (10,11)), ('second_flag', '=', True),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True), 
                 '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                  '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True)]

        domain = [('partner_id', '=', distributor_id),('second_flag', '=', False),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  ('distributor_paid_bool', '=', True)]

        paid_retailer1 = bml.sudo().search(domain1)

        if paid_retailer1:
            paid_retailer_count = len(paid_retailer1)
            amount_total1 = [sum(x.amount for x in paid_retailer1 )]
            amount_total = amount_total1[0]

            for res in paid_retailer1:
                if res.scanned_datetime2:
                    check_in_date = datetime.strptime(str(res.scanned_datetime2), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id2.name, 
                        'distributor_id' : res.partner_id2.id,
                        'user' : res.user_id2.name, 
                        'amount' : res.amount,
                    }
                paid_retailer_coupons.append((data))

        paid_retailer = bml.sudo().search(domain)

        if paid_retailer:
            paid_retailer_count += len(paid_retailer)
            amount_total1 = [sum(x.amount for x in paid_retailer )]
            amount_total += amount_total1[0]

            for res in paid_retailer:
                if res.updated_datetime:
                    check_in_date = datetime.strptime(str(res.updated_datetime), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data1 = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id.name, 
                        'distributor_id' : res.partner_id.id,
                        'user' : res.user_id.name , 
                        'amount' : res.amount,
                    }
                paid_retailer_coupons.append((data1))

        response = {'count' : paid_retailer_count,
                    'list': paid_retailer_coupons,
                    'amount_total' : amount_total, }
        return {'success': response, 'error': None}



    # @http.route('/wmvdapi/unpaid_retailer', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/unpaid_retailer', auth='public', methods=["POST"], type="json")
    def unpaid_retailer(self, distributor_id):
        """ Amount Paid TO Retailer """
        print("------------/wmvdapi/unpaid_retailer -----------", distributor_id)
        data = {}
        data1 = {}
        amount_total= unpaid_retailer_count = 0
        unpaid_retailer_coupons= []

        bml = request.env['barcode.marketing.line']

        # domain = ['|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
        #          ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
        #           '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False)]

        domain1 = [('barcode_marketing_id','in', (10,11)), ('second_flag', '=', True),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True), 
                 '|',('partner_id', '=', distributor_id),('partner_id2', '=', distributor_id),
                  '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False)]

        domain = [('partner_id', '=', distributor_id),('second_flag', '=', False),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  ('distributor_paid_bool', '=', False)]

        unpaid_retailer1 = bml.sudo().search(domain1)

        if unpaid_retailer1:
            unpaid_retailer_count = len(unpaid_retailer1)
            amount_total1 = [sum(x.amount for x in unpaid_retailer1 )]
            amount_total = amount_total1[0]

            for res in unpaid_retailer1:
                if res.second_flag:
                    check_in_date = datetime.strptime(str(res.scanned_datetime2), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id2.name, 
                        'distributor_id' : res.partner_id2.id,
                        'user' : res.user_id2.name, 
                        'amount' : res.amount,
                    }
                unpaid_retailer_coupons.append((data))

        unpaid_retailer = bml.sudo().search(domain)

        if unpaid_retailer:
            unpaid_retailer_count += len(unpaid_retailer)
            amount_total1 = [sum(x.amount for x in unpaid_retailer )]
            amount_total += amount_total1[0]

            for res in unpaid_retailer:
                if res.updated_datetime:
                    check_in_date = datetime.strptime(str(res.updated_datetime), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data1 = {
                        'id': res.id,
                        'coupon': res.name,
                        'date': updated_datetime,
                        'distributor' : res.partner_id.name, 
                        'distributor_id' : res.partner_id.id,
                        'user' : res.user_id.name , 
                        'amount' : res.amount,
                    }
                unpaid_retailer_coupons.append((data1))

        response = {'count' : unpaid_retailer_count,
                    'list': unpaid_retailer_coupons,
                    'amount_total' : amount_total, }
        return {'success': response, 'error': None}

    # @http.route('/wmvdapi/get_assigned_distributor_list', methods=["POST"], type='json', auth='user')
    # def get_assigned_distributor_list(self, user_id=None):
    #     start = time.time()
    #     print("------------/wmvdapi/get_assigned_distributor_list -----------", user_id)

    #     manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).id
    #     if manager_id:
    #         response = self.assigned_distributor_list(manager_id, user_id, distributors=[])

    #         end = time.time()
    #         # print "------------- END get_assigned_distributor_list -------", end-start

    #         if response:
    #             return {'success': response, 'error': None}
    #         else:
    #             return {'success': None, 'error':'No Distributors Found'}

    #     else:
    #         return {'success': None, 'error':'No Distributors Found'}


    # def assigned_distributor_list(self,manager_id=False, user_id=False,  distributors=[]):
    #     domain = [('user_id', '=', user_id),('user_id', '!=', False),('active', '=', True),('customer', '=', True)]
    #     partner_rec = request.env['res.partner'].sudo().search(domain)   

    #     if partner_rec :

    #         for rec in partner_rec:
    #             vals = {
    #                 'id': rec.id,
    #                 'name': rec.name,
    #                 'mobile': rec.mobile,
    #                 'email' : rec.email,
    #                 'salesperson_id' : rec.user_id.id,
    #                 'salesperson_name' : rec.user_id.name,
    #                 'address' : ((rec.street + ', ') if rec.street else ' ' ) + \
    #                             ((rec.street2+ ', ') if rec.street2 else ' ' )  + \
    #                             ((rec.city + ', ') if rec.city else ' ' ) + \
    #                             ((rec.zip + ', ') if rec.zip else ' ' ) + \
    #                             ((rec.state_id.name + ', ') if rec.state_id else ' ' ) + \
    #                             ((rec.country_id.name + ', ') if rec.country_id else ' ' )

    #             }
    #             distributors.append(vals)

    #     subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id)])
    #     if subordinate_ids :
    #         for res in subordinate_ids:
    #             self.assigned_distributor_list(res.id, res.user_id.id, distributors)

    #     response = {'count' : len(distributors), 'distributors': distributors}
    #     return response