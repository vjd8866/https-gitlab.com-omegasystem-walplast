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

class DistributorOnboarding(http.Controller):

    @http.route('/wmvdapi/create_distributor', methods=["POST"], type='json', auth='user')
    def create_distributor(self, distributor_id=None, user_id=None, name=None, partner_group_id=None, street=None, street2=None,
                    city=None, state_id=None, zip=None, country_id=None, contact_name=None, mobile_no=None, pan_no=None,district_id=None,bp_code=None,
                    pricelist=None,partner_id=None,declaration_received=None,phone_no=None,gst_no=None,aadhar_no=None,email=None,bank_name=None,manager_id=None,
                    cheque1=None,amount1=None,cheque2=None,amount2=None,cheque3=None,amount3=None,security_deposit_amount=None ,sd_cheque_no=None ,
                    credit_limit=None ,credit_days=None,owner_name=None,owner_dob=None ,owner_spouse_name=None ,owner_spouse_dob=None,owner_mrg_anvrsry_date=None
                    ,owner_child1_name=None ,owner_child1_dob=None ,owner_child2_name=None ,owner_child2_dob=None ,owner_child3_name=None,owner_child3_dob=None ):

        print("------------/wmvdapi/create_distributor -----------", user_id)

        
        users_rec = request.env['res.users'].sudo().search([('id', '=', user_id), ('active', '=', True)], limit=1).name

        # if validate_lead:
        #     return {'success': None, 'error': validate_lead}

        distributor_vals = {
            'name': name,
            'partner_group_id': partner_group_id or None,
            'street': street or '',
            'street2': street2 or '',
            'city': city or '',
            'state_id': state_id or None,
            'zip': zip or '',
            'country_id': country_id or None,
            'contact_name': contact_name or '',
            'mobile_no': mobile_no or '',
            'user_id': user_id or None,
            'pan_no': pan_no or '',
            'district_id': district_id or None,
            'bp_code': bp_code or '',
            'pricelist': pricelist or '',
            'partner_id': partner_id or None,
            'declaration_received': declaration_received or '',
            'phone_no': phone_no or '',
            'gst_no': gst_no or '',
            'aadhar_no': aadhar_no or '',
            'email': email or '',
            'manager_id': manager_id or None,
            'bank_name': bank_name or '',
            'cheque1': cheque1 or '',
            'amount1': amount1 or '',
            'cheque2':cheque2 or '',
            'amount2':amount2 or '',
            'cheque3':cheque3 or '',
            'amount3':amount3 or '',
            'security_deposit_amount':security_deposit_amount or '',
            'sd_cheque_no':sd_cheque_no or '',
            'credit_limit':credit_limit or '',
            'credit_days':credit_days or '',
            'owner_name':owner_name or '',
            'owner_dob':owner_dob or None,
            'owner_spouse_name':owner_spouse_name or '',
            'owner_spouse_dob':owner_spouse_dob or None,
            'owner_mrg_anvrsry_date':owner_mrg_anvrsry_date or None,
            'owner_child1_name':owner_child1_name or '',
            'owner_child1_dob':owner_child1_dob or None,
            'owner_child2_name':owner_child2_name or '',
            'owner_child2_dob':owner_child2_dob or None,
            'owner_child3_name':owner_child3_name or '',
            'owner_child3_dob':owner_child3_dob or None,
        }

        distributor_rec = request.env['wp.res.partner'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(distributor_vals)

        vals = {
            "id": distributor_id or None,
            "portal_id": distributor_rec.id or None,
            'name': distributor_rec.name or '',
            'partner_group_id': distributor_rec.partner_group_id.id or None,
            'partner_group_name': distributor_rec.partner_group_id.name or '',
            'street': distributor_rec.street or '',
            'street2': distributor_rec.street2 or '',
            'city': distributor_rec.city or '',
            'state_id': distributor_rec.state_id.id or None,
            'state_name': distributor_rec.state_id.name or '',
            'zip': distributor_rec.zip or '',
            'country_id': distributor_rec.country_id.id or None,
            'country_name': distributor_rec.country_id.name or '',
            'contact_name': distributor_rec.contact_name or '',
            'mobile': distributor_rec.mobile_no or '',
            'user_id': user_id or None,
            "user": users_rec or '',
            'pan_no': distributor_rec.pan_no or '',
            'district_id': distributor_rec.district_id.id or None,
            'district_name': distributor_rec.district_id.name or None,
            'bp_code': distributor_rec.bp_code or '',
            'pricelist': distributor_rec.pricelist or '',
            'partner_id': distributor_rec.partner_id or None,
            'declaration_received': distributor_rec.declaration_received or '',
            'phone_no': distributor_rec.phone_no or '',
            'gst_no': distributor_rec.gst_no or '',
            'aadhar_no': distributor_rec.aadhar_no or '',
            'email': distributor_rec.email or '',
            'manager_id': distributor_rec.manager_id.id or None,
            'manager_name':distributor_rec. manager_id.name or '',
            'bank_name': distributor_rec.bank_name or '',
            'cheque1': distributor_rec.cheque1 or '',
            'amount1': distributor_rec.amount1 or '',
            'cheque2': distributor_rec.cheque2 or '',
            'amount2': distributor_rec.amount2 or '',
            'cheque3': distributor_rec.cheque3 or '',
            'amount3': distributor_rec.amount3 or '',
            'security_deposit_amount': distributor_rec.security_deposit_amount or '',
            'sd_cheque_no': distributor_rec.sd_cheque_no or '',
            'credit_limit': distributor_rec.credit_limit or '',
            'credit_days': distributor_rec.credit_days or '',
            'owner_name': distributor_rec.owner_name or '',
            'owner_dob': distributor_rec.owner_dob or '',
            'owner_spouse_name': distributor_rec.owner_spouse_name or '',
            'owner_spouse_dob': distributor_rec.owner_spouse_dob or '',
            'owner_mrg_anvrsry_date': distributor_rec.owner_mrg_anvrsry_date or '',
            'owner_child1_name': distributor_rec.owner_child1_name or '',
            'owner_child1_dob': distributor_rec.owner_child1_dob or '',
            'owner_child2_name': distributor_rec.owner_child2_name or '',
            'owner_child2_dob': distributor_rec.owner_child2_dob or '',
            'owner_child3_name': distributor_rec.owner_child3_name or '',
            'owner_child3_dob': distributor_rec.owner_child3_dob or '',
        }

        response = {'distributor': vals}
        return {'success': response, 'error': None}


    @http.route('/wmvdapi/get_onboarding_distributor_list', methods=["POST"], type='json', auth='user')
    def get_onboarding_distributor_list(self, user_id=None):
        start = time.time()
        distributors=[]
        print("------------/wmvdapi/get_onboarding_distributor_list -----------", user_id)

        partner_rec = request.env['wp.res.partner'].sudo().search([('active', '=', True),('user_id','=',user_id)])

        if partner_rec:
            for partner in partner_rec:
                vals = {'id': partner.id,
                        'name': (str(partner.bp_code + " - ") if partner.bp_code else '') \
                                + (str(partner.name) if partner.name else '') \
                                + (' - ' + str(partner.city) if partner.city else ''),
                        'partner_group_id':partner.partner_group_id.id,
                        'partner_group_name': partner.partner_group_id.name or '',
                        'street': partner.street or '',
                        'street2': partner.street2 or '',
                        'city': partner.city or '',
                        'state_id': partner.state_id.id or None,
                        'state_name': partner.state_id.name or '',
                        'zip': partner.zip or '',
                        'country_id': partner.country_id.id or None,
                        'country_name': partner.country_id.name or '',
                        'contact_name': partner.contact_name or '',
                        'mobile': partner.mobile_no or '',
                        'user_id': partner.user_id.id or None,
                        'pan_no': partner.pan_no or '',
                        'district_id': partner.district_id.id or None,
                        'district_name': partner.district_id.name or '',
                        'bp_code': partner.bp_code or '',
                        'pricelist': partner.pricelist or '',
                        'partner_id': partner.partner_id.id or None,
                        'declaration_received': partner.declaration_received or '',
                        'phone_no': partner.phone_no or '',
                        'gst_no': partner.gst_no or '',
                        'aadhar_no': partner.aadhar_no or '',
                        'email': partner.email or '',
                        'manager_id': partner.manager_id.id or None,
		        'manager_name': partner.manager_id.name or '',
                        'bank_name': partner.bank_name or '',
                        'cheque1': partner.cheque1 or '',
                        'amount1': partner.amount1 or '',
                        'cheque2': partner.cheque2 or '',
                        'amount2': partner.amount2 or '',
                        'cheque3': partner.cheque3 or '',
                        'amount3': partner.amount3 or '',
                        'security_deposit_amount': partner.security_deposit_amount or '',
                        'sd_cheque_no': partner.sd_cheque_no or '',
                        'credit_limit': partner.credit_limit or '',
                        'credit_days': partner.credit_days or '',
                        'owner_name': partner.owner_name or '',
                        'owner_dob': partner.owner_dob or '',
                        'owner_spouse_name': partner.owner_spouse_name or '',
                        'owner_spouse_dob': partner.owner_spouse_dob or '',
                        'owner_mrg_anvrsry_date': partner.owner_mrg_anvrsry_date or '',
                        'owner_child1_name': partner.owner_child1_name or '',
                        'owner_child1_dob': partner.owner_child1_dob or '',
                        'owner_child2_name': partner.owner_child2_name or '',
                        'owner_child2_dob': partner.owner_child2_dob or '',
                        'owner_child3_name': partner.owner_child3_name or '',
                        'owner_child3_dob': partner.owner_child3_dob or '',
                        }
                distributors.append(vals)
        response = {'count' : len(distributors), 'distributors': distributors}

        end = time.time()
        print("------------- END get_onboarding_distributor_list -------", end - start)

        if response:
            return {'success': response, 'error': None}
        else:
            return {'success': None, 'error': 'No Distributors Found'}

        # else:
        #     return {'success': None, 'error': 'No Distributors Found'}

    @http.route('/wmvdapi/get_state_district', auth='user', methods=["POST"], type='json')
    def get_state_district(self):
        print("------------/wmvdapi/get_state_district -----------")
        result = request.env['res.state.district'].search([]).read(mainfields)
        district = {'success': result or {}, 'error': None}

        return district
