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
searchfields= ['id','name','code','distributer_id','street','street2','city','state_id','zip',
'country_id','pan_no','mobile','phone','email','salesperson_id','manager_id']
headers = {'Content-Type': 'application/json',}
company_id = 3


class WpRetailerController(http.Controller):

    # @http.route('/wmvdapi/get_retailer_list', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_retailer_list', methods=["POST"], type='json', auth='public')
    def get_retailer_list(self, user_id=None):
        start = time.time()
        print("------------/wmvdapi/get_retailer_list -----------", user_id)

        manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1)

        if manager_id:
            response = self.retailer_list(manager_id['id'], user_id,retailers=[])
            # response = self.retailer_list(manager_id['id'], user_id,retailers=[])

            end = time.time()
            # print "------------- END get_retailer_list -------", end-start

            if response:
                return {'success': response, 'error': None}
            else:
                return {'success': None, 'error':'No Retailer Found'}

        else:
            return {'success': None, 'error':'No Retailer Found'}


    def retailer_list(self,manager_id=False, user_id=False,retailers=[]):

        retailers_rec = request.env['wp.retailer'].sudo().search([('salesperson_id', '=', user_id),
                                                                  ('salesperson_id', '!=', False),
                                                                  ('active', '=', True)]).read(searchfields)
        # retailers_rec = request.env['wp.retailer'].sudo().search([('state_id','=',user.state_id.id),('active', '=', True)]).read(searchfields)

        for res in retailers_rec:
            vals = {
                    'id' : res['id'],
                    'name' : res['name'],
                    'code' : res['code'] if res['code'] else '',
                    'distributer_id' : res['distributer_id'][0] if res['distributer_id'] else False,
                    'distributer_name' : res['distributer_id'][1] if res['distributer_id'] else '',

                    'address' :((res['street'] + ', ') if res['street'] else '' ) + \
                                ((res['street2'] + ', ') if res['street2'] else '' )  + \
                                ((res['city'] + ', ') if res['city'] else '' ) + \
                                ((res['zip'] + ', ') if res['zip'] else '' ) + \
                                ((res['state_id'][1] + ', ') if res['state_id'] else '' ) + \
                                ((res['country_id'][1]) if res['country_id'] else '' ),


                    'city' : res['city'] if res['city'] else '',
                    'state_id' : res['state_id'][0] if res['state_id'] else '',
                    'state_name' : res['state_id'][1] if res['state_id'] else '',
                    'pan_no' : res['pan_no'] if res['pan_no'] else '',
                    'mobile' : res['mobile'] if res['mobile'] else '',
                    'phone' : res['phone'] if res['phone'] else '',
                    'email' : res['email'] if res['email'] else '',
                    'user_id' : res['salesperson_id'][0] if res['salesperson_id'] else '',
                    'user_name' : res['salesperson_id'][1] if res['salesperson_id'] else '',

                    'manager_id' : res['manager_id'][0] if res['manager_id'] else '',
                    'manager_name' : res['manager_id'][1] if res['manager_id'] else '',
                    }

            retailers.append(vals)

        subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id)])

        if subordinate_ids :
            for res in subordinate_ids:
                # if res.parent_id == manager_id or res.user_id.partner_id.state_id == state_id:
                self.retailer_list(res['id'], res['user_id']['id'],retailers)

        response = {'count' : len(retailers), 'retailers': retailers}
        return response

    # @http.route('/wmvdapi/get_state_wise_retailer_list', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_state_wise_retailer_list', methods=["POST"], type='json', auth='public')
    def get_state_wise_retailer_list(self, user_id=None,search_kw=None):

        print("------------/wmvdapi/get_state_wise_retailer_list -----------", user_id)
        # user =request.env['res.users'].sudo().search([('id','=',user_id),('active','=',True)])
        emp =request.env['hr.employee'].sudo().search([('user_id','=',user_id),('active','=',True)])
        if not search_kw:
            retailers = request.env['wp.retailer'].sudo().search(['|',('salesperson_id.state_id', 'in', emp.allowed_state_ids.ids),
                                                                  ('salesperson_id.state_id', '=',emp.user_id.state_id.id),
                                                                  ('salesperson_id', '!=', False),
                                                                     ('active', '=', True)])
        else:
            retailers = request.env['wp.retailer'].sudo().search(['|',('salesperson_id.state_id', '=', emp.allowed_state_ids.ids),
                                                                  ('salesperson_id.state_id', '=',emp.user_id.state_id.id),
                                                                  ('salesperson_id', '!=', False),
                                                                  ('active', '=', True),'|','|',('name','ilike',search_kw),('code','ilike',search_kw),
                                                                  ('mobile','ilike',search_kw)])
        retailers_list = []
        for res in retailers:
            vals = {
                    'id' : res['id'] or None,
                    'name' : res['name'] or '',
                    'code' : res['code'] if res['code'] else '',
                    'distributer_id' : res['distributer_id']['id'] or None,
                    'distributer_name' : res['distributer_id']['name'] or '',

                    'address' :((res['street'] + ', ') if res['street'] else '' ) + \
                                ((res['street2'] + ', ') if res['street2'] else '' )  + \
                                ((res['city'] + ', ') if res['city'] else '' ) + \
                                ((res['zip'] + ', ') if res['zip'] else '' ) + \
                                ((res['state_id']['name'] + ', ') if res['state_id'] else '' ) + \
                                ((res['country_id']['name']) if res['country_id'] else '' ),


                    'city' : res['city'] if res['city'] else '',
                    'state_id' : res['state_id']['id'] or None,
                    'state_name' : res['state_id']['name'] or '',
                    'pan_no' : res['pan_no'] if res['pan_no'] else '',
                    'mobile' : res['mobile'] if res['mobile'] else '',
                    'phone' : res['phone'] if res['phone'] else '',
                    'email' : res['email'] if res['email'] else '',
                    'user_id' : res['salesperson_id']['id'] or None,
                    'user_name' : res['salesperson_id']['name'] or '',
                    'manager_id' : res['manager_id']['id'] or None,
                    'manager_name' : res['manager_id']['name'] or '',
                    }

            retailers_list.append(vals)

        response = {'count': len(retailers_list), 'retailers': retailers_list}
        return response
