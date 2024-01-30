from odoo import http
from odoo.http import request
import json
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _
import time
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class EmployeeCouponCNReceivedDashboard(http.Controller):

    # @http.route('/wmvdapi/get_salesperson_distributor', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_salesperson_distributor', methods=["POST"], type='json', auth='public')
    def get_salesperson_distributor(self, user_id=None):
        print("------------/wmvdapi/get_salesperson_distributor -----------", user_id)
        domain = [('user_id', '=', user_id),('active', '=', True),('customer_rank', '>', 0)]
        partner_rec = request.env['res.partner'].sudo().search(domain)

        if partner_rec :
            distributor_count = len(partner_rec)
            partner = []

            for rec in partner_rec:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url_128 = base_url + '/web/image?' + 'model=res.partner&id=' + str(rec.id) + '&field=image'
                distributor_user_id = request.env['res.users'].sudo().search([('partner_id','=',rec.id)], limit=1)

                dist_dashboard = self.salesperson_distributor_dashboard(rec.id, distributor_list=True)
                vals = {
                        'id': rec.id,
                        'distributor_user_id': distributor_user_id.id or '',
                        'name': rec.name,
                        'mobile': rec.mobile or '',
                        'email' : rec.email or '',
                        'salesperson_id' : rec.user_id.id,
                        'salesperson_name' : rec.user_id.name,
                        'image' : image_url_128,
                        'address' : ((rec.street + ', ') if rec.street else '' ) + \
                                    ((rec.street2+ ', ') if rec.street2 else '' )  + \
                                    ((rec.city + ', ') if rec.city else '' ) + \
                                    ((rec.zip + ', ') if rec.zip else '' ) + \
                                    ((rec.state_id.name + ', ') if rec.state_id else '' ) + \
                                    ((rec.country_id.name + ', ') if rec.country_id else '' ),
                    }
                if dist_dashboard:
                    vals['amount'] = dist_dashboard
                else:
                    dist_dashboard=  {
                        "credit_received": 0.0,
                        "payment_pending": 0.0,
                        "credit_pending": 0.0,
                        "self_scanned": 0.0
                    }
                    vals['amount'] = dist_dashboard
                partner.append(vals)

            response = {'count' : distributor_count, 'list': partner}
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error':'No Distributors Found'}


    # @http.route('/wmvdapi/salesperson_distributor_dashboard', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/salesperson_distributor_dashboard', auth='public', methods=["POST"], type="json")
    def salesperson_distributor_dashboard(self, distributor_id, distributor_list=False):
        """ Salesperson Distributor Dashboard """
        print("------------/wmvdapi/salesperson_distributor_dashboard -----------", distributor_id)

        credit_received_domain = [('status', '=', 'paid'), ('distributor_id', '=', distributor_id)]
        credit_pending_domain = [('status', '=', 'pending'), ('distributor_id', '=', distributor_id)]
        self_scanned_domain = [('distributor_id', '=', distributor_id),('retailer_id', '=', distributor_id)]

        payment_paid_domain = [('status', '=', 'paid'),
                                ('distributor_id', '=', distributor_id),
                                ('retailer_id', '!=', distributor_id)]

        cn_received_amount = [sum(x.amount for x in request.env['wp.coupon.credit'].sudo().search(credit_received_domain))]
        cn_pending_amount = [sum(x.amount for x in request.env['wp.coupon.credit'].sudo().search(credit_pending_domain))]
        pmt_paid_amount = [sum(x.amount for x in request.env['wp.coupon.payment'].sudo().search(payment_paid_domain))]
        self_scanned_amount = [sum(x.amount for x in request.env['wp.coupon.payment'].sudo().search(self_scanned_domain))]

        response = {'credit_received' : (cn_received_amount[0] if cn_received_amount else 0.0)  or 0.0,
                    'credit_pending' : (cn_pending_amount[0] if cn_pending_amount else 0.0)  or 0.0,
                    'payment_pending' : (pmt_paid_amount[0] if pmt_paid_amount else 0.0)  or 0.0,
                    'self_scanned' : (self_scanned_amount[0] if self_scanned_amount else 0.0)  or 0.0,
                }

        if distributor_list:
            return response

        return {'success': response, 'error': None}


    # @http.route('/wmvdapi/get_subordinate_list', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_subordinate_list', methods=["POST"], type='json', auth='public')
    def get_subordinate_list(self, user_id=None):
        start = time.time()
        print("------------/wmvdapi/get_subordinate_list -----------", user_id)

        manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).id
        if manager_id:
            response = self.subordinate_list(manager_id,employees=[])

            end = time.time()
            # print "------------- END get_subordinate_list -------", end-start

            if response:
                return {'success': response, 'error': None}
            else:
                return {'success': None, 'error':'No Subordinates Found'}

        else:
            return {'success': None, 'error':'No Subordinates Found'}


    def subordinate_list(self,manager_id=False, employees=[]):
        subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id),('status','!=', 'left'),('user_id','!=',False)])
        if subordinate_ids :
            for rec in subordinate_ids:
                jl = request.env['wp.salesperson.journey'].sudo().search([('user_id', '=', rec.user_id.id),
                    ('date','=',date.today())], limit=1)

                journey = {
                        "id" : jl.id or None,
                        "date": jl.date or '',
                        "started_at" : jl.started_at or '',
                        "ended_at" : jl.ended_at or '',
                }

                vals = {
                    'id': rec.id,
                    'user_id': rec.user_id.id or None,
                    'name': rec.name,
                    'mobile': rec.mobile_phone or "",
                    'email' : rec.work_email or "",
                    'work_location' : rec.work_location or "",
                    'work_state_id' : rec.state_id.id or None,
                    'work_state' : rec.state_id.name or "",
                    'designation': rec.job_id.name or "",
                    'user_type' : rec.user_id.wp_user_type_id.name or "",
                    'manager_id': rec.parent_id.user_id.id or None,
                    'manager': rec.parent_id.user_id.name,
                    "journey": journey,
                }
                employees.append(vals)

                self.subordinate_list(rec.id, employees)

            response = {'count' : len(employees), 'employees': employees}
            return response


    # @http.route('/wmvdapi/get_assigned_distributor_list', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_assigned_distributor_list', methods=["POST"], type='json', auth='public')
    def get_assigned_distributor_list(self, user_id=None, search_query=None):
        start = time.time()
        print("------------/wmvdapi/get_assigned_distributor_list -----------", user_id, search_query)

        manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1)
        if manager_id:
            if search_query:
                response = self.assigned_distributor_list(manager_id.id, user_id, search_query, distributors=[])
            else:
                response = self.assigned_distributor_list(manager_id.id, user_id, distributors=[])


            end = time.time()
            # print "------------- END get_assigned_distributor_list -------", end-start

            if response:
                return {'success': response, 'error': None}
            else:
                return {'success': None, 'error':'No Distributors Found'}

        else:
            return {'success': None, 'error':'No Distributors Found'}


    def assigned_distributor_list(self,manager_id=False, user_id=False, search_query=False,distributors=[]):
        if search_query:
            domain = [('user_id', '=', user_id),
                        ('user_id', '!=', False),
                        ('active', '=', True),
                        ('customer_rank', '>', 0),
                        ('name', 'ilike', search_query)]
        else:
            domain = [('user_id', '=', user_id),
                      ('user_id', '!=', False),
                      ('active', '=', True),
                      ('customer_rank', '>', 0)]

        partner_rec = request.env['res.partner'].sudo().search(domain)

        if partner_rec :

            for rec in partner_rec:
                distributor_user_id = request.env['res.users'].sudo().search([('partner_id','=',rec.id)], limit=1)
                dist_dashboard = self.salesperson_distributor_dashboard(rec.id, distributor_list=True)
                vals = {
                    'id': rec.id or None,
                    'c_bpartner_id':rec.c_bpartner_id or '',
                    'distributor_user_id': distributor_user_id.id or None,
                    'name': rec.name,
                    'mobile': rec.mobile or '',
                    'email' : rec.email or '',
                    'salesperson_id' : rec.user_id.id or None,
                    'salesperson_name' : rec.user_id.name,
                    'state_id' : rec.state_id.id or None,
                    'state' : rec.state_id.name or '',
                    'address' : ((rec.street + ', ') if rec.street else '' ) + \
                                ((rec.street2+ ', ') if rec.street2 else '' )  + \
                                ((rec.city + ', ') if rec.city else '' ) + \
                                ((rec.zip + ', ') if rec.zip else '' ) + \
                                ((rec.state_id.name + ', ') if rec.state_id else '' ) + \
                                ((rec.country_id.name + ', ') if rec.country_id else '' )

                }
                if dist_dashboard:
                    vals['amount'] = dist_dashboard
                else:
                    dist_dashboard=  {
                        "credit_received": 0.0,
                        "payment_pending": 0.0,
                        "credit_pending": 0.0,
                        "self_scanned": 0.0
                    }
                    vals['amount'] = dist_dashboard

                distributors.append(vals)


        subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id)])
        if subordinate_ids :
            for res in subordinate_ids:
                print("aaaaaaaaaaaa--------------------", res.id, res.user_id.id, search_query)
                self.assigned_distributor_list(res.id, res.user_id.id,search_query, distributors)

        response = {'count' : len(distributors), 'distributors': distributors}
        return response



    # @http.route('/wmvdapi/get_state_wise_distributors', methods=["POST"], type='json', auth='user')
    # def get_state_wise_distributors(self, user_id=None, search_kw=None):
    # 	print("------------/wmvdapi/get_state_wise_distributors -----------", user_id, search_kw)
    #
    # 	user = request.env['res.users'].sudo().search([('id','=',user_id),('active','=',True)],limit=1)
    # 	distributors_list = []
    # 	if search_kw:
    # 		domain = [('user_id', '!=', False),
    # 					('active', '=', True),
    # 					('customer', '=', True),
    # 					('name', 'ilike', search_kw),('user_id.state_id','=',user['state_id']['id'])]
    # 	else:
    # 		domain = [('user_id', '!=', False),
    # 				  ('active', '=', True),
    # 				  ('customer', '=', True),('user_id.state_id','=',user['state_id']['id'])]
    #
    # 	partner_rec = request.env['res.partner'].sudo().search(domain)
    #
    # 	# if partner_rec :
    # 	for rec in partner_rec:
    # 		distributor_user_id = request.env['res.users'].sudo().search([('partner_id','=',rec['id'])], limit=1)
    # 		dist_dashboard = self.salesperson_distributor_dashboard(rec['id'], distributor_list=True)
    # 		vals = {
    # 			'id': rec['id'] or None,
    # 			'distributor_user_id': distributor_user_id['id'] or None,
    # 			'name': rec['name'] or '',
    # 			'mobile': rec['mobile'] or '',
    # 			'email' : rec['email'] or '',
    # 			'salesperson_id' : rec['user_id']['id'] or None,
    # 			'salesperson_name' : rec['user_id']['name'] or '',
    # 			'state_id' : rec['state_id']['id'] or None,
    # 			'state' : rec['state_id']['name'] or '',
    # 			'address' : ((rec['street'] + ', ') if rec['street'] else '' ) + \
    # 						((rec['street2'] + ', ') if rec['street2'] else '' )  + \
    # 						((rec['city'] + ', ') if rec['city'] else '' ) + \
    # 						((rec['zip'] + ', ') if rec['zip'] else '' ) + \
    # 						((rec['state_id']['name'] + ', ') if rec['state_id'] else '' ) + \
    # 						((rec['country_id']['name'] + ', ') if rec['country_id'] else '' )
    #
    # 		}
    # 		if dist_dashboard:
    # 			vals['amount'] = dist_dashboard
    # 		else:
    # 			dist_dashboard=  {
    # 				"credit_received": 0.0,
    # 				"payment_pending": 0.0,
    # 				"credit_pending": 0.0,
    # 				"self_scanned": 0.0
    # 			}
    # 			vals['amount'] = dist_dashboard
    #
    # 		distributors_list.append(vals)
    #
    # 	response = {'count': len(distributors_list), 'distributors': distributors_list}
    # 	return response


    # @http.route('/wmvdapi/get_state_wise_distributors', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_state_wise_distributors', methods=["POST"], type='json', auth='public')
    def get_state_wise_distributors(self, user_id=None, search_kw=None):
        print("------------/wmvdapi/get_state_wise_distributors -----------", user_id, search_kw)

        # user = request.env['res.users'].sudo().search([('id', '=', user_id), ('active', '=', True)], limit=1)
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user_id), ('active', '=', True)], limit=1)
        distributors_list = []
        if search_kw:
            domain = [('active', '=', True),
                      ('customer_rank', '>', 0),
                      ('name', 'ilike', search_kw),'|', ('user_id.state_id', 'in', emp.allowed_state_ids.ids), ('user_id.state_id', '=', emp.user_id.state_id.id)]
        else:
            domain = [('active', '=', True),
                      ('customer_rank', '>', 0),'|', ('user_id.state_id', 'in', emp.allowed_state_ids.ids), ('user_id.state_id', '=', emp.user_id.state_id.id)]

        partner_rec = request.env['res.partner'].sudo().search(domain)

        # if partner_rec :
        for rec in partner_rec:
            distributor_user_id = request.env['res.users'].sudo().search([('partner_id', '=', rec.id)], limit=1)
            dist_dashboard = self.salesperson_distributor_dashboard(rec.id, distributor_list=True)
            vals = {
                'id': rec.id or None,
                'distributor_user_id': distributor_user_id.id or None,
                'name': rec.name or '',
                'mobile': rec.mobile or '',
                'email': rec.email or '',
                'salesperson_id': rec.user_id.id or None,
                'salesperson_name': rec.user_id.name or '',
                'state_id': rec.state_id.id or None,
                'state': rec.state_id.name or '',
                'address': ((rec.street + ', ') if rec.street else '') + \
                           ((rec.street2 + ', ') if rec.street2 else '') + \
                           ((rec.city + ', ') if rec.city else '') + \
                           ((rec.zip + ', ') if rec.zip else '') + \
                           ((rec.state_id.name + ', ') if rec.state_id else '') + \
                           ((rec.country_id.name + ', ') if rec.country_id else '')

            }
            if dist_dashboard:
                vals['amount'] = dist_dashboard
            else:
                dist_dashboard = {
                    "credit_received": 0.0,
                    "payment_pending": 0.0,
                    "credit_pending": 0.0,
                    "self_scanned": 0.0
                }
                vals['amount'] = dist_dashboard

            distributors_list.append(vals)

        response = {'count': len(distributors_list), 'distributors': distributors_list}
        return response
