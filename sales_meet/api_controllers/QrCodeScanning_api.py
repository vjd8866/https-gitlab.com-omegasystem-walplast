from odoo import http
from odoo.http import request
import json
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _
from datetime import datetime, timedelta, date
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"
start_time = datetime.today().strftime( "%Y-%m-%d 00:00:00")
end_time = datetime.today().strftime( "%Y-%m-%d 23:59:59")
current_time = ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
server_time = ( datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
mainfields = ['id','payment_id','scan_id','coupon_id','created_at','amount']

class QrCodeScanning(http.Controller):

    # @http.route('/wmvdapi/push_qrcoupon', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/push_qrcoupon', auth='public', methods=["POST"], type="json")
    def push_coupon(self, coupon, user_id, user_type, distributor_id=False, partner_id=False):
        start = time.time()
        print("------------/wmvdapi/push_qrcoupon -----------", user_id)
        # # print "--------------------" , coupon, distributor_id, user_id, user_type
        resp = request.env['barcode.marketing.check'].sudo().check_mobile_coupon(coupon, user_id, user_type, distributor_id, partner_id)
        # print("--------------- Response --", resp, type(resp))
        if isinstance(resp, str):
            end = time.time()
            # print "--------------------- update_records TIME-----------------" , end - start
            return {'success': None, 'error': resp}
            
        else:
            end = time.time()
            # print "--------------------- update_records TIME-----------------" , end - start
            return {'success': resp, 'error': None}


    # @http.route('/wmvdapi/retailer_dashboard', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/retailer_dashboard', auth='public', methods=["POST"], type="json")
    def retailer_dashboard(self, user_id, user_type):
        """ Retailer Dashboard """
        print("------------/wmvdapi/retailer_dashboard -----------", user_id)
        if user_type == 'Retailer':
            pay_customer_domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
                        ('mobile_bool', '=', True),
                        ('retailer_scanned', '=', True),
                    ]
            received_from_distributor_domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
                        ('mobile_bool', '=', True),
                        ('retailer_scanned', '=', True),
                        '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True)
                    ]

            receive_from_distributor_domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
                        ('mobile_bool', '=', True),
                        ('retailer_scanned', '=', True),
                        '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False),
                    ]

            pay_customer_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(receive_from_distributor_domain))]
            receive_from_distributor_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(receive_from_distributor_domain))]
            received_from_distributor_amount = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(received_from_distributor_domain))]


            response = {'amount_paid' : pay_customer_amount or 0, 
                        'amount_received': receive_from_distributor_amount  or 0, 
                        'amount_yet_to_be_received': received_from_distributor_amount or 0, }

            return {'success': response, 'error': None}

    # @http.route('/wmvdapi/today_scan_coupons', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/today_scan_coupons', auth='public', methods=["POST"], type="json")
    def today_scan_coupons(self, partner_id):
        """ Today Scans By User """
        print("------------/wmvdapi/today_scan_coupons -----------", partner_id)
        data = {}
        today_scan_coupons= []
        domain = [('scan_user_id', '=', partner_id),
                    ('created_at', '>=', start_time),
                    ('created_at', '<=', end_time),
                ]

        coupon_scanned = request.env['wp.coupon.payment.item'].sudo().search(domain)
        if coupon_scanned:
            coupon_scanned_count = len(coupon_scanned)
            print("----------", coupon_scanned_count)

            for res in coupon_scanned:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                if res.payment_id.coupon_credit_id:
                    credit={
                            'created_at': res.payment_id.coupon_credit_id.created_at,
                            'amount' : res.payment_id.coupon_credit_id.amount,
                            'distributor_id': res.payment_id.distributor_id.id,
                            'status': res.payment_id.coupon_credit_id.status,
                            'payment_mode': res.payment_id.payment_mode or '',
                            'id': res.payment_id.coupon_credit_id.id,
                            }
                else:
                    credit=None

                payment = { 'id': res.payment_id.id,
                            'status' : res.payment_id.status,
                            'payment_mode' : res.payment_id.payment_mode or '' ,}

                payment_item = {'id': res.id,}

                data = {
                        'id': res.coupon_id.id,
                        'coupon': res.scan_id,
                        'date': res.created_at,
                        'distributor' : res.payment_id.distributor_id.name, 
                        'distributor_id' : res.payment_id.distributor_id.id, 
                        'user' : res.payment_id.retailer_id.name, 
                        'amount' : res.amount,

                        'status' : res.payment_id.status,
                        'payment' : payment,
                        'payment_item' : payment_item,
                        'credit': credit,
                    }
                today_scan_coupons.append((data))

            response = {'count' : coupon_scanned_count, 'list': today_scan_coupons}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}


    # @http.route('/wmvdapi/all_scan_coupons', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/all_scan_coupons', auth='public', methods=["POST"], type="json")
    def all_scan_coupons(self, partner_id):
        """ All Scans By User """
        print("------------/wmvdapi/all_scan_coupons -----------", partner_id)
        data = {}
        all_scan_coupons= []

        coupon_scanned = request.env['wp.coupon.payment.item'].sudo().search([('scan_user_id', '=', partner_id)])
        if coupon_scanned:
            coupon_scanned_count = len(coupon_scanned)
            print("----------", coupon_scanned_count)

            for res in coupon_scanned:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                if res.payment_id.coupon_credit_id:
                    credit={
                            'created_at': res.payment_id.coupon_credit_id.created_at,
                            'amount' : res.payment_id.coupon_credit_id.amount,
                            'distributor_id': res.payment_id.distributor_id.id,
                            'status': res.payment_id.coupon_credit_id.status,
                            'payment_mode': res.payment_id.payment_mode or '',
                            'id': res.payment_id.coupon_credit_id.id,
                            }
                else:
                    credit=None

                payment = { 'id': res.payment_id.id,
                            'status' : res.payment_id.status,
                            'payment_mode' : res.payment_id.payment_mode  or '' ,}

                payment_item = {'id': res.id,}

                data = {
                        'id': res.coupon_id.id,
                        'coupon': res.scan_id,
                        'date': res.created_at,
                        'distributor' : res.payment_id.distributor_id.name, 
                        'distributor_id' : res.payment_id.distributor_id.id, 
                        'user' : res.payment_id.retailer_id.name, 
                        'amount' : res.amount,

                        'status' : res.payment_id.status,
                        'payment' : payment,
                        'payment_item' : payment_item,
                        'credit': credit,
                    }
                all_scan_coupons.append((data))

            response = {'count' : coupon_scanned_count, 'list': all_scan_coupons}
            return {'success': response, 'error': None}

        else:
            return {'success': None, 'error': None}


    # @http.route('/wmvdapi/get_payment', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/get_payment', auth='public', methods=["POST"], type="json")
    def get_payment(self, partner_id):
        """ Payment Details of Retailer"""
        print("------------/wmvdapi/get_payment -----------", partner_id)
        data = {}
        all_payments= []

        payment_ids = request.env['wp.coupon.payment'].sudo().search(['|',('distributor_id', '=', partner_id),
                                                                            ('retailer_id', '=', partner_id)
                                                                        ])
        if payment_ids:
            payment_id_count = len(payment_ids)
            print("----------", payment_id_count)

            for res in payment_ids:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                data = {
                        'id': res.id,
                        'amount' : res.amount,
                        'created_at': res.created_at,
                        'status' : res.status,
                        'credit_id' : res.coupon_credit_id.id or None,
                        'payment_mode' : res.payment_mode or '',
                        'distributor_id' : res.distributor_id.id,
                        'distributor' : res.distributor_id.name, 
                        'retailer_id' : res.retailer_id.id,
                        'retailer' : res.retailer_id.name,  
                    }
                all_payments.append((data))

            response = {'count' : payment_id_count, 'list': all_payments}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}

    # @http.route('/wmvdapi/get_pending_payment', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/get_pending_payment', auth='public', methods=["POST"], type="json")
    def get_pending_payment(self, partner_id):
        """ Pending Payment Details of Retailer"""
        print("------------/wmvdapi/get_pending_payment -----------", partner_id)
        data = {}
        all_pending_payments= []

        payment_ids = request.env['wp.coupon.payment'].sudo().search(['|',('distributor_id', '=', partner_id),
                                                                            ('retailer_id', '=', partner_id),
                                                                            ('status', '=', 'pending')
                                                                        ])
        if payment_ids:
            payment_id_count = len(payment_ids)
            print("----------", payment_id_count)

            for res in payment_ids.items_one2many:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                data = {
                        'id': res.id,
                        'amount' : res.amount,
                        'created_at': res.created_at,
                        'scan_user' : res.scan_user_id.name,
                        'scan_user_id' : res.scan_user_id.id,
                        'scan_id' : res.scan_id, 
                        'coupon_id' : res.coupon_id.id,
                        'payment_id' : res.payment_id.id,
                        'status': 'pending',
                    }
                all_pending_payments.append((data))

            response = {'count' : payment_id_count, 'list': all_pending_payments}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}


    # @http.route('/wmvdapi/get_payment_by_id', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/get_payment_by_id', auth='public', methods=["POST"], type="json")
    def get_payment_by_id(self, payment_id):
        """ Payment Details of Retailer"""

        print("------------/wmvdapi/get_payment_by_id -----------", payment_id)
        data = {}
        all_payments_by_id= []

        payment_item_ids = request.env['wp.coupon.payment.item'].sudo().search([('payment_id', '=', payment_id)])
        if payment_item_ids:
            payment_item_count = len(payment_item_ids)
            print("----------", payment_item_count)

            for res in payment_item_ids:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                data = {
                        'id': res.id,
                        'amount' : res.amount,
                        'created_at': res.created_at,
                        'scan_user' : res.scan_user_id.name,
                        'scan_user_id' : res.scan_user_id.id,
                        'scan_id' : res.scan_id, 
                        'coupon_id' : res.coupon_id.id,
                        'payment_id' : res.payment_id.id,  
                    }
                all_payments_by_id.append((data))

            response = {'count' : payment_item_count, 'list': all_payments_by_id}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}

    # @http.route('/wmvdapi/get_payment_items', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/get_payment_items', auth='public', methods=["POST"], type="json")
    def get_payment_items(self, partner_id):
        """ Payment item Details of Retailer"""

        print("------------/wmvdapi/get_payment_items -----------", partner_id)
        data = {}
        all_payments_by_id= []

        payment_item_ids = request.env['wp.coupon.payment.item'].sudo().search([('scan_user_id', '=', partner_id)])
        if payment_item_ids:
            payment_item_count = len(payment_item_ids)
            print("----------", payment_item_count)

            for res in payment_item_ids:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                data = {
                        'id': res.id,
                        'amount' : res.amount,
                        'created_at': res.created_at,
                        'scan_user' : res.scan_user_id.name,
                        'scan_user_id' : res.scan_user_id.id,
                        'scan_id' : res.scan_id, 
                        'coupon_id' : res.coupon_id.id,
                        'payment_id' : res.payment_id.id,  
                    }
                all_payments_by_id.append((data))

            response = {'count' : payment_item_count, 'list': all_payments_by_id}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}

    # @http.route('/wmvdapi/get_credit', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/get_credit', auth='public', methods=["POST"], type="json")
    def get_credit(self, distributor_id):
        """ Payment Details of Retailer"""
        print("------------/wmvdapi/get_credit -----------", distributor_id)
        data = {}
        all_credits= []

        credit_ids = request.env['wp.coupon.credit'].sudo().search([('distributor_id', '=', distributor_id)])
        if credit_ids:
            credit_count = len(credit_ids)
            print("----------", credit_count)

            for res in credit_ids:
                check_in_date = datetime.strptime(str(res.created_at), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                data = {
                        'id': res.id,
                        'amount' : res.amount,
                        'created_at': res.created_at,
                        'status' : res.status,
                        'distributor_id' : res.distributor_id.id,
                        'distributor' : res.distributor_id.name, 
                    }
                all_credits.append((data))

            response = {'count' : credit_count, 'list': all_credits}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}



    # @http.route('/wmvdapi/get_distributor', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_distributor', methods=["POST"], type='json', auth='public')
    def get_partner(self, distributor_id=None):
        print("------------/wmvdapi/get_distributor -----------", distributor_id)
        domain = [('id', '=', distributor_id),('active', '=', True)]
        partner_rec = request.env['res.partner'].sudo().search(domain)

        if partner_rec :
            distributor_count = len(partner_rec)
            partner = []

            for rec in partner_rec:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url_128 = base_url + '/web/image?' + 'model=res.partner&id=' + str(rec.id) + '&field=image'
                distributor_user_id = request.env['res.users'].sudo().search([('partner_id','=',rec.id)], limit=1)
                vals = {
                    'id': rec.id,
                    'distributor_user_id': distributor_user_id.id,
                    'name': rec.name,
                    'mobile': rec.mobile,
                    'email' : rec.email,
                    'image' : image_url_128,
                    'address' : ((rec.street + ', ') if rec.street else ' ' ) + \
                                ((rec.street2+ ', ') if rec.street2 else ' ' )  + \
                                ((rec.city + ', ') if rec.city else ' ' ) + \
                                ((rec.zip + ', ') if rec.zip else ' ' ) + \
                                ((rec.state_id.name + ', ') if rec.state_id else ' ' ) + \
                                ((rec.country_id.name + ', ') if rec.country_id else ' ' )

                }
                partner.append(vals)

            response = {'count' : distributor_count, 'list': partner}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error':'Distributor Not Found'}

    # @http.route('/wmvdapi/get_retailer', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/get_retailer', auth='public', methods=["POST"], type="json")
    def get_retailer(self, partner_id):
        """ All Retailers of Distributor """

        domain = [('wp_distributor_id', '=', partner_id),]
        partner_rec = request.env['res.partner'].sudo().search(domain)

        if partner_rec :
            partner = []
            retailer_count = len(partner_rec)
            for rec in partner_rec:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url_128 = base_url + '/web/image?' + 'model=res.partner&id=' + str(rec.id) + '&field=image'
                retailer_user_id = request.env['res.users'].sudo().search([('partner_id','=',rec.id)], limit=1)
                if retailer_user_id:
                    vals = {
                        'id': rec.id or None,
                        'retailer_user_id': retailer_user_id.id or None,
                        'name': rec.name,
                        'mobile': rec.mobile,
                        'email' : rec.email,
                        'image' : image_url_128,
                        'address' : ((rec.street + ', ') if rec.street else ' ' ) + \
                                    ((rec.street2+ ', ') if rec.street2 else ' ' )  + \
                                    ((rec.city + ', ') if rec.city else ' ' ) + \
                                    ((rec.zip + ', ') if rec.zip else ' ' ) + \
                                    ((rec.state_id.name + ', ') if rec.state_id else ' ' ) + \
                                    ((rec.country_id.name + ', ') if rec.country_id else ' ' )

                    }
                    partner.append(vals)

            response = {'count' : retailer_count, 'list': partner}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error':'No Retailers Found'}


    # @http.route('/wmvdapi/received_from_distributor', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/received_from_distributor', auth='public', methods=["POST"], type="json")
    def received_from_distributor(self, user_id):
        """ Amount Received From Distributor """
        print("------------/wmvdapi/received_from_distributor -----------", user_id)
        data = {}
        data1 = {}
        amount_total= distributor_paid_count = 0
        distributor_paid_coupons= []
        paid_coupon_ids1 = []
        paid_coupon_ids = []
        bml = request.env['barcode.marketing.line']


        domain1 = [('barcode_marketing_id','in', (10,11)), ('second_flag', '=', True),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True), 
                 '|',('user_id', '=', user_id),('user_id2', '=', user_id),
                  '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True)]

        domain = [('user_id', '=', user_id),('second_flag', '=', False),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  ('distributor_paid_bool', '=', True)]


        distributor_paid1 = bml.sudo().search(domain1)

        print("----------------distributor_paid1---------", distributor_paid1)

        if distributor_paid1:
            distributor_paid_count = len(distributor_paid1)
            amount_total1 = [sum(x.amount for x in distributor_paid1 )]
            amount_total = amount_total1[0]
            paid_coupon_ids1 = [x.id for x in distributor_paid1]


            print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", amount_total)

            for res in distributor_paid1:
                if res.scanned_datetime2:
                    check_in_date = datetime.strptime(str(res.scanned_datetime2), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data1 = {
                        'id': res.id or None,
                        'coupon': res.name or '',
                        'date': updated_datetime or None,
                        'distributor' : res.partner_id2.name or '',
                        'distributor_id' : res.partner_id2.id or None,
                        'user' : res.user_id2.name or '',
                        'amount' : res.amount or 0.0,
                    }
                distributor_paid_coupons.append((data1))

        distributor_paid = bml.sudo().search(domain)
        print("----------------distributor_paid---------", distributor_paid)

        if distributor_paid:
            distributor_paid_count += len(distributor_paid)
            amount_total1 = [sum(x.amount for x in distributor_paid )]
            amount_total += amount_total1[0]
            paid_coupon_ids = [x.id for x in distributor_paid]

            print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", amount_total)

            for res in distributor_paid:
                if res.updated_datetime:
                    check_in_date = datetime.strptime(str(res.updated_datetime), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data = {
                        'id': res.id or None,
                        'coupon': res.name or '',
                        'date': updated_datetime or None,
                        'distributor' : res.partner_id.name or '',
                        'distributor_id' : res.partner_id.id or None,
                        'user' : res.user_id.name or '',
                        'amount' : res.amount or 0.0,
                    }
                distributor_paid_coupons.append((data))

            total_paid_coupon_ids = paid_coupon_ids1 + paid_coupon_ids

            print("#######-------------------amount_total -----------############", amount_total, distributor_paid_count)

            response = {'count' : distributor_paid_count, 
                        'amount_total' : amount_total, 
                        'list': distributor_paid_coupons,
                        'paid_coupon_ids': total_paid_coupon_ids,}

            return {'success': response, 'error': None}


    # @http.route('/wmvdapi/to_receive_from_distributor', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/to_receive_from_distributor', auth='public', methods=["POST"], type="json")
    def to_receive_from_distributor(self, user_id):
        """ Amount yet to be Received From Distributor """
        print("------------/wmvdapi/to_receive_from_distributor -----------", user_id)
        data = {}
        data1 = {}
        amount_total= distributor_unpaid_count = 0
        distributor_unpaid_coupons= []
        unpaid_coupon_ids1 = []
        unpaid_coupon_ids2 = []
        total_unpaid_coupon_ids = []
        bml = request.env['barcode.marketing.line']


        domain1 = [('barcode_marketing_id','in', (10,11)), ('second_flag', '=', True),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True), 
                 '|',('user_id', '=', user_id),('user_id2', '=', user_id),
                  '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False)]

        domain = [('user_id', '=', user_id),('second_flag', '=', False),
                 ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
                  ('distributor_paid_bool', '=', False)]

        distributor_unpaid1 = bml.sudo().search(domain1)

        print("----------------distributor_unpaid1---------", distributor_unpaid1)

        if distributor_unpaid1:
            distributor_unpaid_count = len(distributor_unpaid1)
            amount_total1 = [sum(x.amount for x in distributor_unpaid1 )]
            amount_total = amount_total1[0]
            unpaid_coupon_ids1 = [x.id for x in distributor_unpaid1]

            for res in distributor_unpaid1:
                if res.scanned_datetime2:
                    check_in_date = datetime.strptime(str(res.scanned_datetime2), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data1 = {
                        'id': res.id or None,
                        'coupon': res.name or '',
                        'date': updated_datetime or None,
                        'distributor' : res.partner_id2.name or '',
                        'distributor_id' : res.partner_id2.id or None,
                        'user' : res.user_id2.name or '',
                        'amount' : res.amount or 0.0,
                    }
                distributor_unpaid_coupons.append((data1))

        distributor_unpaid = bml.sudo().search(domain)

        print("----------------distributor_unpaid---------", distributor_unpaid)

        if distributor_unpaid:
            distributor_unpaid_count += len(distributor_unpaid)
            amount_total1 = [sum(x.amount for x in distributor_unpaid )]
            amount_total += amount_total1[0]
            unpaid_coupon_ids2 = [x.id for x in distributor_unpaid]

            for res in distributor_unpaid:

                if res.updated_datetime:
                    check_in_date = datetime.strptime(str(res.updated_datetime), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
                else:
                    updated_datetime = ''

                data = {
                        'id': res.id or None,
                        'coupon': res.name or '',
                        'date': updated_datetime or None,
                        'distributor' : res.partner_id.name or '',
                        'distributor_id' : res.partner_id.id or None,
                        'user' : res.user_id.name or '',
                        'amount' : res.amount or 0.0,
                    }
                distributor_unpaid_coupons.append((data))

        total_unpaid_coupon_ids = unpaid_coupon_ids1 + unpaid_coupon_ids2

        response = {'count' : distributor_unpaid_count, 
                    'list': distributor_unpaid_coupons,
                    'amount_total' : amount_total, 
                    'unpaid_coupon_ids': total_unpaid_coupon_ids,}

        return {'success': response, 'error': None}


    #
    # def state_wise_distributors(self,user_id=None):
    #     print("------------/wmvdapi/get_state_wise_distributors -----------", user_id)
    #
    #     distributors_list = []
    #     domain = [('active', '=', True),
    #               ('customer', '=', True), ('user_id.state_id', '=', user.state_id.id)]
    #
    #     partner_rec = request.env['res.partner'].sudo().search(domain)
    #
    #     # if partner_rec
    #     return partner_rec

    # @http.route('/wmvdapi/all_distributor_qr_scans', auth='user', methods=["POST"], type="json")
    # def all_distributor_qr_scans(self, user_id):
    #     """ All Scans By User """
    #     print("------------/wmvdapi/all_distributor_qr_scans -----------", user_id)
    #     distributors_list = []
    #     all_scan_coupons = []
    #     manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1)
    #     distributors_rec = self.assigned_distributor_list(manager_id.id, user_id, distributors=[])
    #     # distributors_rec.append(self.state_wise_distributors(user_id))
    #     user = request.env['res.users'].sudo().search([('id','=',user_id)])
    #     for distributor in distributors_rec:
    #         coupon_scanned_count = 0.0
    #         coupan_scanned_amount = 0.0
    #         if distributor.id == 15146:
    #             test = True
    #         coupon_scanned = request.env['wp.coupon.payment.item'].sudo().search([('scan_user_id', '=', distributor.id)])
    #         if coupon_scanned:
    #             coupon_scanned_count = len(coupon_scanned)
    #             print("----------", coupon_scanned_count)
    #
    #             for res in coupon_scanned:
    #                 # check_in_date = datetime.strptime(res.created_at, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 # updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
    #
    #                 if res.payment_id.coupon_credit_id:
    #                     credit = {
    #                         'created_at': res.payment_id.coupon_credit_id.created_at,
    #                         'amount': res.payment_id.coupon_credit_id.amount,
    #                         'distributor_id': res.payment_id.distributor_id.id,
    #                         'status': res.payment_id.coupon_credit_id.status,
    #                         'payment_mode': res.payment_id.payment_mode or '',
    #                         'id': res.payment_id.coupon_credit_id.id,
    #                     }
    #                 else:
    #                     credit = None
    #
    #                 payment = {'id': res.payment_id.id,
    #                            'status': res.payment_id.status,
    #                            'payment_mode': res.payment_id.payment_mode or '', }
    #
    #                 payment_item = {'id': res.id, }
    #                 data = {
    #                     'id': res.coupon_id.id,
    #                     'coupon': res.scan_id,
    #                     'date': res.created_at,
    #                     'distributor': res.payment_id.distributor_id.name,
    #                     'distributor_id': res.payment_id.distributor_id.id,
    #                     'user': res.payment_id.retailer_id.name,
    #                     'amount': res.amount,
    #
    #                     'status': res.payment_id.status,
    #                     'payment': payment,
    #                     'payment_item': payment_item,
    #                     'credit': credit,
    #                 }
    #                 all_scan_coupons.append(data)
    #                 coupan_scanned_amount += res.amount
    #
    #
    #             distributors = {'total_coupon_scanned':coupon_scanned_count,
    #                         'total_scanned_amount':coupan_scanned_amount,
    #                         'salesperson_id':user_id,
    #                         'salesperson_name':user.name,
    #                         'email':user.email,
    #                         'state':user.partner_id.state_id.name,
    #                         'state_id':user.email,
    #                         'address': ((user.partner_id.street + ', ') if user.partner_id.street else '' ) + \
    #                             ((user.partner_id.street2+ ', ') if user.partner_id.street2 else '' )  + \
    #                             ((user.partner_id.city + ', ') if user.partner_id.city else '' ) + \
    #                             ((user.partner_id.zip + ', ') if user.partner_id.zip else '' ) + \
    #                             ((user.partner_id.state_id.name + ', ') if user.partner_id.state_id else '' ) + \
    #                             ((user.partner_id.country_id.name + ', ') if user.partner_id.country_id else '' ),
    #
    #                         'id':distributor.id,
    #                         'name':distributor.name,
    #                         # 'count': coupon_scanned_count,
    #                         'coupons': all_scan_coupons}
    #
    #             distributors_list.append(distributors)
    #     if distributors_list:
    #         response = {'distributors':distributors_list}
    #         return {'success': response, 'error': None}
    #     else:
    #         return {'success': None, 'error': None}

    # @http.route('/wmvdapi/all_distributor_qr_scans', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/all_distributor_qr_scans', auth='public', methods=["POST"], type="json")
    def all_distributor_qr_scans(self, user_id):
        """ All Scans By User """
        print("------------/wmvdapi/all_distributor_qr_scans -----------", user_id)
        distributors_list = []
        all_scan_coupons = []
        manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id), ('active', '=', True)],
                                                              limit=1)
        distributors_rec = self.assigned_distributor_list(manager_id.id, user_id, distributors=[])
        # distributors_rec.append(self.state_wise_distributors(user_id))
        user = request.env['res.users'].sudo().search([('id', '=', user_id),('active','=',True)],limit=1)
        # for distributor in distributors_rec:
        coupon_scanned_count = 0.0
        coupan_scanned_amount = 0.0
        distributor = False
        for rec in distributors_rec:
            coupon_scanned = request.env['wp.coupon.payment.item'].sudo().search([('payment_id.distributor_id','=',rec)])
            # if coupon_scanned:
            coupon_scanned_count = len(coupon_scanned)
            # print("----------", coupon_scanned_count)

            for res in coupon_scanned:
                # check_in_date = datetime.strptime(res.created_at, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                # updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

                if res.payment_id.coupon_credit_id:
                    credit = {
                        'created_at': res.payment_id.coupon_credit_id.created_at or None,
                        'amount': res.payment_id.coupon_credit_id.amount or 0.0,
                        'distributor_id': res.payment_id.distributor_id.id or None,
                        'status': res.payment_id.coupon_credit_id.status or '',
                        'payment_mode': res.payment_id.payment_mode or '',
                        'id': res.payment_id.coupon_credit_id.id or None,
                    }
                else:
                    credit = None

                payment = {'id': res.payment_id.id or None,
                           'status': res.payment_id.status or '',
                           'payment_mode': res.payment_id.payment_mode or '', }

                payment_item = {'id': res.id}
                data = {
                    'id': res.coupon_id.id or None,
                    'coupon': res.scan_id or None,
                    'date': res.created_at or '',
                    'distributor': res.payment_id.distributor_id.name or '',
                    'distributor_id': res.payment_id.distributor_id.id or None,
                    'user': res.payment_id.retailer_id.name or '',
                    'amount': res.amount or 0.0,

                    'status': res.payment_id.status,
                    'payment': payment,
                    'payment_item': payment_item,
                    'credit': credit,
                }
                all_scan_coupons.append(data)
                coupan_scanned_amount += res['amount'] or 0.0
                distributor = res.payment_id.distributor_id

            distributors = {'total_coupon_scanned': coupon_scanned_count,
                            'total_scanned_amount': coupan_scanned_amount,
                            'salesperson_id': user_id or None,
                            'salesperson_name': user.name or '',
                            'email': user.email or '',
                            'state': user.partner_id.state_id.name or '',
                            'state_id': user.email or '',
                            'address': ((user.partner_id.street + ', ') if user.partner_id.street else '') + \
                                       ((user.partner_id.street2 + ', ') if user.partner_id.street2 else '') + \
                                       ((user.partner_id.city + ', ') if user.partner_id.city else '') + \
                                       ((user.partner_id.zip + ', ') if user.partner_id.zip else '') + \
                                       ((
                                                    user.partner_id.state_id.name + ', ') if user.partner_id.state_id else '') + \
                                       ((
                                                    user.partner_id.country_id.name + ', ') if user.partner_id.country_id else ''),

                            'id': distributor.id if distributor else None,
                            'name': distributor.name if distributor else '',
                            # 'count': coupon_scanned_count,
                            'coupons': all_scan_coupons}

            distributors_list.append(distributors)
        if distributors_list:
            response = {'count':len(distributors_list),'distributors': distributors_list}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': None}

    def assigned_distributor_list(self, manager_id=False, user_id=False, distributors=[]):
        # user = request.env['res.users'].sudo().search([('id','=', user_id), ('active', '=', True)], limit=1)

        domain = [('user_id', '=', user_id),
                  ('active', '=', True),
                  ('customer_rank', '>', 0)]
        partner_rec = request.env['res.partner'].sudo().search(domain)

        # if partner_rec:
        for rec in partner_rec:
            if rec.id not in distributors:
                distributors.append(rec.id)

        subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id', '=', manager_id)])
        if subordinate_ids:
            for res in subordinate_ids:
                # print("--------------------", res['id'], res['user_id'][0])
                self.assigned_distributor_list(res.id, res.user_id.id, distributors)

        return distributors

    # @http.route('/wmvdapi/pay_retailer', auth='user', methods=["POST"], type="json")
    # def pay_retailer(self, amount_total, unpaid_coupon_ids):
    #     print("------------/wmvdapi/pay_retailer -----------")
    #     # print "--------------------" , unpaid_coupon_ids, amount_total
    #     domain1 = [('id','in',tuple(unpaid_coupon_ids)),
    #     ('second_flag','=', True),('barcode_marketing_id','in', (10,11)),
    #     ('distributor_paid_bool2','=', False)]

    #     domain2 = [('id','in',tuple(unpaid_coupon_ids)),('second_flag','=', False),('distributor_paid_bool','=', False)]

    #     resp = request.env['barcode.marketing.line'].sudo().search(domain1).write({
    #                             'distributor_paid_bool2': True,
    #                             'distributor_paid_date2': date.today(),
    #                             'scanned_datetime2': datetime.now() ,
    #                             })

    #     resp2 = request.env['barcode.marketing.line'].sudo().search(domain2).write({
    #                             'distributor_paid_bool': True,
    #                             'distributor_paid_date': date.today(),
    #                             'updated_datetime': datetime.now() ,
    #                             })

    #     print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", resp)
    #     print("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", resp2)


    #     response = "Paid %s to Retailer successfully" % (amount_total)
    #     print("--------------- Response --", response)
    #     return {'success': response, 'error': None}, 


    # @http.route('/wmvdapi/received_from_distributor', auth='user', methods=["POST"], type="json")
    # def received_from_distributor(self, user_id):
    #     """ Amount Received From Distributor """
    #     print("------------/wmvdapi/received_from_distributor -----------", user_id)
    #     data = {}
    #     amount_total=0
    #     distributor_paid_coupons= []
    #     domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
    #              ('mobile_bool', '=', True),('retailer_scanned', '=', True),
    #               '|',('distributor_paid_bool', '=', True),('distributor_paid_bool2', '=', True)]

    #     # amount_total = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(domain) )]
    #     # return {'success': amount_total or 0.0, 'error': None}

    #     distributor_paid = request.env['barcode.marketing.line'].sudo().search(domain)

    #     if distributor_paid:
    #         distributor_paid_count = len(distributor_paid)
    #         amount_total = [sum(x.amount for x in distributor_paid )]

    #         for res in distributor_paid:
    #             if res.second_flag:
    #                 check_in_date = datetime.strptime(res.scanned_datetime2, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
    #             else:
    #                 check_in_date = datetime.strptime(res.updated_datetime, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

    #             data = {
    #                     'id': res.id,
    #                     'coupon': res.name,
    #                     'date': updated_datetime,
    #                     'distributor' : res.partner_id.name or res.partner_id2.name, 
    #                     'distributor_id' : res.partner_id.id or res.partner_id2.id,
    #                     'user' : res.user_id.name or res.user_id2.name, 
    #                     'amount' : res.amount,
    #                 }
    #             distributor_paid_coupons.append((data))

    #         response = {'count' : distributor_paid_count, 
    #                     'amount_total' : amount_total, 
    #                     'list': distributor_paid_coupons}

    #         return {'success': response, 'error': None}

    # @http.route('/wmvdapi/to_receive_from_distributor', auth='user', methods=["POST"], type="json")
    # def to_receive_from_distributor(self, user_id):
    #     """ Amount yet to be Received From Distributor """
    #     print("------------/wmvdapi/to_receive_from_distributor -----------", user_id)
    #     data = {}
    #     amount_total=0
    #     distributor_unpaid_coupons= []
    #     domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
    #              ('mobile_bool', '=', True), ('retailer_scanned', '=', True),
    #               '|',('distributor_paid_bool', '=', False),('distributor_paid_bool2', '=', False),]

    #     # amount_total = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(domain))]
    #     # return {'success': amount_total or 0.0, 'error': None}

    #     distributor_unpaid = request.env['barcode.marketing.line'].sudo().search(domain)

    #     if distributor_unpaid:
    #         distributor_unpaid_count = len(distributor_unpaid)
    #         amount_total = [sum(x.amount for x in distributor_unpaid )]
    #         unpaid_coupon_ids = [x.id for x in distributor_unpaid]

    #         for res in distributor_unpaid:
    #             if res.second_flag:
    #                 check_in_date = datetime.strptime(res.scanned_datetime2, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
    #             else:
    #                 check_in_date = datetime.strptime(res.updated_datetime, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

    #             data = {
    #                     'coupon': res.name,
    #                     'date': updated_datetime,
    #                     'distributor' : res.partner_id.name or res.partner_id2.name, 
    #                     'distributor_id' : res.partner_id.id or res.partner_id2.id,
    #                     'user' : res.user_id.name or res.user_id2.name, 
    #                     'amount' : res.amount,
    #                 }
    #             distributor_unpaid_coupons.append((data))

    #         response = {'count' : distributor_unpaid_count, 
    #                     'amount_total' : amount_total, 
    #                     'list': distributor_unpaid_coupons,
    #                     'unpaid_coupon_ids': unpaid_coupon_ids,}
    #         return {'success': response, 'error': None}


    # @http.route('/wmvdapi/today_scan_coupons', auth='user', methods=["POST"], type="json")
    # def today_scan_coupons(self, user_id):
    #     """ Today Scans By User """
    #     print("------------/wmvdapi/today_scan_coupons -----------", user_id)
    #     data = {}
    #     today_scan_coupons= []
    #     domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),'|',
    #                 ('updated_date', '=', date.today()),
    #                 ('scanned_date2', '=', date.today())
    #             ]
    #     coupon_scanned = request.env['barcode.marketing.line'].sudo().search(domain)
    #     if coupon_scanned:
    #         coupon_scanned_count = len(coupon_scanned)
    #         print("----------", coupon_scanned_count)

    #         for res in coupon_scanned:
    #             if res.second_flag:
    #                 check_in_date = datetime.strptime(res.scanned_datetime2, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
    #             else:
    #                 check_in_date = datetime.strptime(res.updated_datetime, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

    #             data = {
    #                     'id': res.id,
    #                     'coupon': res.name,
    #                     'date': updated_datetime,
    #                     'distributor' : res.partner_id.name or res.partner_id2.name, 
    #                     'distributor_id' : res.partner_id.id or res.partner_id2.id, 
    #                     'user' : res.user_id.name or res.user_id2.name, 
    #                     'amount' : res.amount,
    #                 }
    #             today_scan_coupons.append((data))

    #         response = {'count' : coupon_scanned_count, 'list': today_scan_coupons}

    #         return {'success': response, 'error': None}


    # @http.route('/wmvdapi/all_scan_coupons', auth='user', methods=["POST"], type="json")
    # def all_scan_coupons(self, user_id):
    #     """ All Scans By User """
    #     print("------------/wmvdapi/all_scan_coupons -----------", user_id)
    #     data = {}
    #     all_scan_coupons= []
    #     domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id)]
    #     coupon_scanned = request.env['barcode.marketing.line'].sudo().search(domain)

    #     if coupon_scanned:

    #         for res in coupon_scanned:
    #             if res.second_flag:
    #                 check_in_date = datetime.strptime(res.scanned_datetime2, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)
    #             else:
    #                 check_in_date = datetime.strptime(res.updated_datetime, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
    #                 updated_datetime = check_in_date.strftime(DATETIME_FORMAT)

    #             data = {
    #                     'id': res.id,
    #                     'coupon': res.name,
    #                     'date': updated_datetime,
    #                     'distributor' : res.partner_id.name or res.partner_id2.name, 
    #                     'distributor_id' : res.partner_id.id or res.partner_id2.id,
    #                     'user' : res.user_id.name or res.user_id2.name, 
    #                     'amount' : res.amount,
    #                 }
    #             all_scan_coupons.append((data))

    #         response = {'list': all_scan_coupons}
    #         return {'success': response, 'error': None}






#---------------------------------------------------------------------------------------------------------------


    # @http.route('/wmvdapi/pay_customer', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/pay_customer', auth='none', methods=["POST"], type="json")
    def pay_customer(self, user_id):
        """ Amount Paid TO Customer """
        domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
                    ('mobile_bool', '=', True), ('retailer_scanned', '=', True),]

        amount_total = [sum(x.amount for x in request.env['barcode.marketing.line'].sudo().search(domain) )]
        return {'success': amount_total or 0.0, 'error': None}

    # @http.route('/wmvdapi/today_scan_coupons_count', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/today_scan_coupons_count', auth='public', methods=["POST"], type="json")
    def today_scan_coupons_count(self, user_id):
        """ Today Scans Count By User """
        domain = ['|',('user_id', '=', user_id),('user_id2', '=', user_id),
                  '|',('updated_date', '=', date.today()), ('scanned_date2', '=', date.today()) ]

        coupon_scanned = request.env['barcode.marketing.line'].sudo().search_count(domain)
        return {'success': coupon_scanned, 'error': None}


    # @http.route('/wmvdapi/distributor_count', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/distributor_count', auth='public', methods=["POST"], type="json")
    def distributor_count(self, user_id):
        """ Distributor Count By User """
        distributor_count = request.env['wp.retailer'].sudo().search_count([('retailer_user_id', '=', user_id)])
        return {'success': distributor_count, 'error': None}
