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
headers = {'Content-Type': 'application/json',}
company_id = 3


class WpLeadController(http.Controller):

    @http.route('/wmvdapi/create_lead', methods=["POST"], type='json', auth='user')
    def create_lead(self, lead_id=None, user_id=None, name=None, partner_group_id=None, street=None, street2=None, 
        city=None, state_id=None, zip=None, country_id=None, contact_name=None, mobile=None, pan_no=None):
        print("------------/wmvdapi/create_lead -----------", user_id)

        partner_group = state = country = ''
        if partner_group_id: partner_group = request.env['res.partner.group'].sudo().search([('id', '=', partner_group_id)], limit=1)

        if state_id: state = request.env['res.country.state'].sudo().search([('id', '=', state_id)], limit=1)

        if country_id: country = request.env['res.country'].sudo().search([('id', '=', country_id)], limit=1)

        users_rec = request.env['res.users'].sudo().search([('id', '=', user_id),('active', '=', True)], limit=1).name

        validate_lead = request.env['crm.lead'].sudo().validate_lead(phone=False, mobile=mobile)
        if validate_lead:
            return {'success': None, 'error': validate_lead}
       
        lead_vals = {
                'name': name,
                'partner_group_id': partner_group.id or None,
                'street': street or '',
                'street2': street2 or '',
                'city': city or '',
                'state_id': state_id or None,
                'zip': zip or '',
                'country_id': country_id or None,
                # 'partner_ids': [(6, 0, [])] or '',
                'contact_name': contact_name or '',
                'mobile': mobile or '',
                'user_id': user_id,
                'pan_no': pan_no or '',
                'mobile_lead_id': lead_id or '',
            }

        lead_rec = request.env['crm.lead'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(lead_vals)

        vals = {
                "id": lead_id or None,
                "portal_id": lead_rec.id or None,
                'name': name or '',
                'partner_group_id': partner_group.id or None,
                'partner_group_name': partner_group.name or '',
                'street': street or '',
                'street2': street2 or '',
                'city': city or '',
                'state_id': state.id or None,
                'state_name': state.name or '',
                'zip': zip or '',
                'country_id': country_id or None,
                'country_name': country.name or '',
                # 'partner_ids': [(6, 0, [])] or '',
                'contact_name': contact_name or '',
                'mobile': mobile or '',
                'user_id': user_id or None,
                "user": users_rec or '',
                'pan_no': pan_no or '',
                
        }

        response = {'lead' : vals}
        return {'success': response, 'error': None}


    @http.route('/wmvdapi/get_user_leads', auth='user', methods=["POST"], type='json')
    def get_user_leads(self, user_id=None):
        print("------------/wmvdapi/get_user_leads -----------")

        lead_rec = request.env['crm.lead'].sudo().search([('user_id', '=', user_id)])
        lead_list = []
        if lead_rec:
            for res in lead_rec:
                vals = {
                    "id": res.mobile_lead_id or '',
                    "portal_id": res.id or None,
                    'name': res.name or '',
                    'partner_group_id': res.partner_group_id.id or None,
                    'partner_group_name': res.partner_group_id.name or '',
                    'street': res.street or '',
                    'street2': res.street2 or '',
                    'city': res.city or '',
                    'state_id': res.state_id.id or None,
                    'state_name': res.state_id.name or '',
                    'zip': res.zip or '',
                    'country_id': res.country_id.id or None,
                    'country_name': res.country_id.name or '',
                    # 'partner_ids': [(6, 0, [])] or '',
                    'contact_name': res.contact_name or '',
                    'mobile': res.mobile or '',
                    'user_id': res.user_id.id or None,
                    "user": res.user_id.name or '',
                    'pan_no': res.pan_no or '',
                
                }
                lead_list.append(vals)

            response = {'count' : len(lead_list), 'list': lead_list}
            return {'success': response, 'error': None}
        else:
            response = {'count' : 0, 'list': []}
            return {'success': response, 'error': None}
            # return {'success': None, 'error':'No Records Found'}


    @http.route('/wmvdapi/get_partner_group', auth='user', methods=["POST"], type='json')
    def get_partner_group(self):
        print("------------/wmvdapi/get_partner_group -----------")
        result = request.env['res.partner.group'].search([('company_id','=', company_id)]).read(mainfields)
        partner_group = {'success': result or {}, 'error': None}
        return partner_group

    @http.route('/wmvdapi/get_country_state', auth='user', methods=["POST"], type='json')
    def get_country_state(self):
        print("------------/wmvdapi/get_country_state -----------")
        result = request.env['res.country.state'].search([]).read(mainfields)
        state = {'success': result or {}, 'error': None}
        return state

    @http.route('/wmvdapi/get_country', auth='user', methods=["POST"], type='json')
    def get_country(self):
        print("------------/wmvdapi/get_country -----------")
        result = request.env['res.country'].search([]).read(mainfields)
        country = {'success': result or {}, 'error': None}
        return country


    @http.route('/wmvdapi/edit_lead', methods=["POST"], type='json', auth='user')
    def edit_lead(self, lead_id=None, user_id=None, vals=None):
        print("------------/wmvdapi/edit_lead -----------", user_id)

        if vals:
            lead = request.env['crm.lead'].sudo().search([('mobile_lead_id', '=', lead_id)])

            if lead:
                for res in vals:
                    print("---------fffffffffff----------", res)
                    if 'mobile' in res:
                        validate_lead = request.env['crm.lead'].sudo().validate_lead(phone=False, mobile=res['mobile'])

                        if validate_lead:
                            return {'success': None, 'error': validate_lead}

                    lead_rec = lead.sudo().write(res)


                    vals2 = {
                        "id": lead_id or None,
                        "portal_id": lead.id or None,
                        'name': lead.name or '',
                        'partner_group_id': lead.partner_group_id.id or None,
                        'partner_group_name': lead.partner_group_id.name or '',
                        'street': lead.street or '',
                        'street2': lead.street2 or '',
                        'city': lead.city or '',
                        'state_id': lead.state_id.id or None,
                        'state_name': lead.state_id.name or '',
                        'zip': lead.zip or '',
                        'country_id': lead.country_id.id or None,
                        'country_name': lead.country_id.name or '',
                        'contact_name': lead.contact_name or '',
                        'mobile': lead.mobile or '',
                        'user_id': lead.user_id.id or None,
                        "user": lead.user_id.name or '',
                        'pan_no': lead.pan_no or '',
                        
                    }

                    response = {'lead' : vals2}
                    return {'success': response, 'error': None}
            else:
                return {'success': None, 'error': "No Such Lead Found"}

    @http.route('/wmvdapi/lead_to_retailer', auth='user', methods=["POST"], type='json')
    def lead_to_retailer(self, user_id, lead_id, distributor_id):
        print("------------/wmvdapi/lead_to_retailer -----------", user_id, lead_id, distributor_id)
        Retailer = request.env['wp.retailer']
        lead_obj = request.env['crm.lead'].sudo().search([('id', '=', lead_id )])

        validate_retailer = Retailer.sudo().validate_retailer(mobile=lead_obj.mobile)
        
        if validate_retailer:
            return {'success': None, 'error': validate_retailer}

        vals = {
            'name': lead_obj.name,
            'salesperson_id': user_id,
            'phone': lead_obj.phone,
            'mobile': lead_obj.mobile,
            'email':lead_obj.email_from,
            'street': lead_obj.street,
            'street2': lead_obj.street2,
            'zip': lead_obj.zip,
            'zone': lead_obj.zone,
            'city': lead_obj.city,
            'country_id': lead_obj.country_id.id,
            'state_id': lead_obj.state_id.id,
            'distributer_id' : distributor_id,
            'lead_id' : lead_obj.id,
            'pan_no' : lead_obj.pan_no,
            'retailer_from_lead': True
        }

        rid = Retailer.create(vals)
        lead_obj.related_retailer = rid.id
        lead_obj.related_distributer = distributor_id

        return {'success': "Retailer Created Successfully", 'error': None}

        # vals = {
        #         'id' : rid.id,
        #         'name' : rid.name,
        #         'code' : rid.code or '',
        #         'distributer_id' : rid.distributer_id.id,
        #         'distributer_name' : rid.distributer_id.name,
        #         'city' : rid.city or '',
        #         'state_id' :  rid.state_id.id if rid.state_id else '',
        #         'state_name' : rid.state_id.name  if rid.state_id else '',
        #         'pan_no' : rid.pan_no or '',
        #         'mobile' : rid.mobile or '',
        #         'phone' : rid.phone or '',
        #         'email' : rid.email or '',
        #         'user_id' : rid.salesperson_id.id or '',
        #         'user_name' : rid.salesperson_id.name or '',

        #         'manager_id' : rid.manager_id.id or '',
        #         'manager_name' : rid.manager_id.name or '',
        #         }
