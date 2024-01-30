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


DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
mainfields = ['id', 'name']
headers = {'Content-Type': 'application/json',}
company_id = 3
state_dict = {
    'draft': 'Draft',
    'done': 'Generated',
    'refused': 'Refused',
    'approved': 'Approved',
    'posted': 'Posted',
    'Closed':'Closed'
}
class WpSamplingController(http.Controller):

    # @http.route('/wmvdapi/create_sampling_requisition', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/create_sampling_requisition', methods=["POST"], type='json', auth='public')
    def create_sampling_requisition(self,sampling_id=None, user_id=None, partner_id=None, date_sample=None,distributer_product_quantity=None,ischeck=None, project_partner_id=None,product_id=None,
                                    lead_id=None,quantity=None, excess_taken=None, excess_quantity=None,total_quantity=None,set_priority=None,sample_attachments=None,applicator_type=None,
                                    contact_person=None,contact_no=None,applicator=None,applicator_no=None,applicator_cost=None,city=None,state_id=None,zone=None,manager_id=None,zsm_id=None,
                                    project_size=None,bags=None,order_quantity=None,order_amt=None,followup_date=None,customer_feedback=None,order_status=None,reverse_location=None,
                                    checkin_lattitude=None,checkin_longitude=None):

        print("------------/wmvdapi/create_sampling_requisition -----------", user_id)

        attachments = []
        user = request.env['res.users'].sudo().search([('id','=',user_id),('active','=',True)])
        partner = request.env['res.partner'].sudo().search([('id','=',partner_id)])
        project_partner = request.env['res.partner'].sudo().search([('id','=',project_partner_id)])
        product = request.env['product.product'].sudo().search([('id','=',product_id)])
        lead = request.env['crm.lead'].sudo().search([('id','=',lead_id)])
        state_id = request.env['res.country.state'].sudo().search([('id','=',state_id)])
        manager = request.env['res.users'].sudo().search([('id','=',manager_id),('active','=',True)])
        zsm = request.env['res.users'].sudo().search([('id','=',zsm_id),('active','=',True)])

        vals={
            'partner_id': partner.id or None,
            'mobile_id': sampling_id or None,
            'date_sample':datetime.strptime(date_sample, "%d/%m/%Y") or None,
            'product_id': product.id or None,
            'distributer_product_quantity': distributer_product_quantity,
            'ischeck': ischeck or None,
            'lead_id': lead.id or None,
            'project_partner_id': project_partner.id or None,
            'quantity': quantity,
            'excess_taken': excess_taken,
            'excess_quantity': excess_quantity,
            'total_quantity': total_quantity,
            'set_priority': set_priority if set_priority else None,
            'applicator_type': applicator_type or None,
            'contact_person': contact_person or '',
            'contact_no': contact_no or '',
            'applicator': applicator or '',
            'applicator_no': applicator_no or '',
            'applicator_cost': applicator_cost,
            'city': city or '',
            'state_id': state_id.id or None,
            'zone': zone,
            'manager_id': manager.id or None,
            'zsm_id': zsm.id or None,
            'project_size': project_size or '',
            'bags': bags,
            'order_quantity': order_quantity,
            'order_amt': order_amt,
            'followup_date': datetime.strptime(followup_date, "%d/%m/%Y") or None,
            'customer_feedback': customer_feedback or '',
            'order_status': order_status or None,
            'user_id':user.id or None,
            'company_id':company_id,
            'reverse_location': reverse_location or '',
            'checkin_lattitude':checkin_lattitude,
            'checkin_longitude':checkin_longitude,
        }
        sampling_requisition = request.env['sample.requisition'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(vals)

        if sample_attachments:
            for res in sample_attachments:
                attachment_id = request.env['ir.attachment'].with_context(
                    mail_auto_subscribe_no_notify=True).sudo().create({
                    'name': sampling_requisition.name,
                    'type': 'binary',
                    'datas': res,  # image, #image.decode('base64'), #base64.b64encode(image),
                    'store_fname': sampling_requisition.name,
                })
                attachments.append(attachment_id.id)
            sampling_requisition.update({
                'sample_attachments': [(6, 0, attachments)],
            })
        status = state_dict[sampling_requisition.state]
        response_vals = {
            'sampling_id':sampling_requisition.mobile_id,
            'portal_id':sampling_requisition.id or None,
            'user_id': user_id or None,
            'partner_id': sampling_requisition.partner_id.id or None,
            'state': status or '',
            'partner_name': sampling_requisition.partner_id.name or '',
            'date_sample': sampling_requisition.date_sample or None,
            'product_id': sampling_requisition.product_id.id or None,
            'product_name': sampling_requisition.product_id.name or '',
            'distributer_product_quantity': sampling_requisition.distributer_product_quantity or 0.0,
            'ischeck': sampling_requisition.ischeck or None,
            'lead_id': sampling_requisition.lead_id.id or None,
            'lead_name': sampling_requisition.lead_id.name or '',
            'project_partner_id': sampling_requisition.project_partner_id.id or None,
            'project_partner_name': sampling_requisition.project_partner_id.name or '',
            'quantity': sampling_requisition.quantity or 0.0,
            'excess_taken': sampling_requisition.excess_taken or None,
            'excess_quantity': sampling_requisition.excess_quantity or 0.0,
            'total_quantity': sampling_requisition.total_quantity or 0.0,
            'set_priority': sampling_requisition.set_priority or None,
            'sample_attachments': sampling_requisition.sample_attachments.ids or None,
            'applicator_type': sampling_requisition.applicator_type or None,
            'contact_person': sampling_requisition.contact_person or '',
            'contact_no': sampling_requisition.contact_no or '',
            'applicator': sampling_requisition.applicator or '',
            'applicator_no': sampling_requisition.applicator_no or '',
            'applicator_cost': sampling_requisition.applicator_cost or 0.0,
            'city': sampling_requisition.city or '',
            'state_id': sampling_requisition.state_id.id or None,
            'state_name': sampling_requisition.state_id.name or '',
            'zone': sampling_requisition.zone or None,
            'manager_id': sampling_requisition.manager_id.id or None,
            'manager_name': sampling_requisition.manager_id.name or '',
            'zsm_id': sampling_requisition.zsm_id.id or None,
            'zsm_name': sampling_requisition.zsm_id.name or '',
            'project_size': sampling_requisition.project_size or None,
            'bags': sampling_requisition.bags or 0,
            'order_quantity': sampling_requisition.order_quantity or None,
            'order_amt': sampling_requisition.order_amt or 0.0,
            'followup_date': sampling_requisition.followup_date or None,
            'customer_feedback': sampling_requisition.customer_feedback or '',
            'order_status': sampling_requisition.order_status or None,
            'reverse_location': sampling_requisition.reverse_location or '',
            'checkin_lattitude': sampling_requisition.checkin_lattitude or 0.0,
            'checkin_longitude': sampling_requisition.checkin_longitude or 0.0,
        }

        response = {'sampling_requisition': response_vals}
        return {'success': response, 'error': None}

    # @http.route('/wmvdapi/get_all_sampling', auth='user', methods=["POST"], type='json')
    @http.route('/wmvdapi/get_all_sampling', auth='public', methods=["POST"], type='json')
    def get_all_sampling(self, user_id=None):
        print("------------/wmvdapi/get_all_sampling -----------")
        sampling_recs = request.env['sample.requisition'].sudo().search([('user_id','=',user_id)])
        sampling_list=[]
        if sampling_recs:
            for rec in sampling_recs:
                status = state_dict[rec.state]

                sampling_list.append({
                    'sampling_id': rec.mobile_id or None,
                    'portal_id': rec.id or None,
                    'user_id': user_id or None,
                    'partner_id': rec.partner_id.id or None,
                    'state': status or '',
                    'partner_name': rec.partner_id.name or '',
                    'date_sample': rec.date_sample or None,
                    'product_id': rec.product_id.id or None,
                    'product_name': rec.product_id.name or '',
                    'distributer_product_quantity': rec.distributer_product_quantity or 0.0,
                    'ischeck': rec.ischeck or None,
                    'lead_id': rec.lead_id.id or None,
                    'lead_name': rec.lead_id.name or '',
                    'project_partner_id': rec.project_partner_id.id or None,
                    'project_partner_name': rec.project_partner_id.name or '',
                    'quantity': rec.quantity or 0.0,
                    'excess_taken': rec.excess_taken ,
                    'excess_quantity': rec.excess_quantity or 0.0,
                    'total_quantity': rec.total_quantity or 0.0,
                    'set_priority': rec.set_priority or None,
                    'sample_attachments': rec.sample_attachments.ids or None,
                    'applicator_type': rec.applicator_type or None,
                    'contact_person': rec.contact_person or '',
                    'contact_no': rec.contact_no or '',
                    'applicator': rec.applicator or '',
                    'applicator_no': rec.applicator_no or '',
                    'applicator_cost': rec.applicator_cost or 0.0,
                    'city': rec.city or '',
                    'state_id': rec.state_id.id or None,
                    'state_name': rec.state_id.name or '',
                    'zone': rec.zone or None,
                    'manager_id': rec.manager_id.id or None,
                    'manager_name': rec.manager_id.name or '',
                    'zsm_id': rec.zsm_id.id or None,
                    'zsm_name': rec.zsm_id.name or '',
                    'project_size': rec.project_size or '',
                    'bags': rec.bags or 0,
                    'order_quantity': rec.order_quantity or 0.0,
                    'order_amt': rec.order_amt or 0.0,
                    'followup_date': rec.followup_date or None,
                    'customer_feedback': rec.customer_feedback or '',
                    'order_status': rec.order_status or None,
                    'reverse_location': rec.reverse_location or '',
                    'checkin_lattitude': rec.checkin_lattitude or 0.0,
                    'checkin_longitude': rec.checkin_longitude or 0.0,
                })

        response = {'sampling_list': sampling_list}
        return {'success': response, 'error': None}

    # @http.route('/wmvdapi/get_product_qty_present', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_product_qty_present', methods=["POST"], type='json', auth='public')
    def get_product_qty_present(self, partner_id=None,product_id=None):
        print("------------/wmvdapi/get_product_qty_present -----------")
        if product_id and partner_id:
            product_lines = request.env['sample.product.line'].sudo().search([('partner_id', '=', partner_id),
                                                                           ('product_id', '=', product_id)])
            product_sum = sum([x.quantity for x in product_lines])

            distributer_product_quantity = {'success': product_sum or 0.0 , 'error': None}

            return distributer_product_quantity

    # @http.route('/wmvdapi/get_onchange_state_zone_details', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_onchange_state_zone_details', methods=["POST"], type='json', auth='public')
    def get_onchange_state_zone_details(self, state_id=None,zone=None):

        domain=[('company_id', '=', company_id)]
        vals = {}
        if zone:
            domain.append(('zone','=',zone))
        if state_id:
            domain.append(('state_id', '=',state_id))

        escalation = request.env['cir.escalation.line'].sudo().search(domain)
        if escalation:
            for esc in escalation:
                vals.update({
                'zsm_id' : esc.zsm_user_id.id or None,
                'zsm_name' : esc.zsm_user_id.name or '',
                'manager_id' : esc.manager_id.id or None,
                'manager_name' : esc.manager_id.name or '',
                'zone' : esc.zone if not zone else zone
                 })

            response = {'escalation_details': vals}
            return {'success': response, 'error': None}

    # @http.route('/wmvdapi/get_sampling_product', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_sampling_product', methods=["POST"], type='json', auth='public')
    def get_sampling_product(self,partner_id=None):
        print("------------/wmvdapi/get_sampling_product -----------")
        # products = []
        message = "No Sampling issued for this Distributor / Retailer. Kindly contact Sales Support Team."
        result = {}
        if partner_id:
            product_id = request.env['sample.product.line'].sudo().search([('partner_id', '=', partner_id)])
            if product_id:
                domain = [('id', 'in', [i.product_id.id for i in product_id]), ('sale_ok', '=', True)]
                result = request.env['product.product'].sudo().search(domain).read(mainfields)
                message = None

        response = {'products':result}

        return {'success': response, 'error':message }

    # @http.route('/wmvdapi/get_assigned_customers', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_assigned_customers', methods=["POST"], type='json', auth='public')
    def get_assigned_customers(self,user_id=None):
        print("------------/wmvdapi/get_assigned_customers -----------")
        result = request.env['res.partner'].sudo().search([('user_id','=',user_id)]).read(mainfields)
        partners = {'success': result or {}, 'error': None}

        return partners

    # @http.route('/wmvdapi/get_manager', methods=["POST"], type='json', auth='user')
    # def get_manager(self):
    #     print("------------/wmvdapi/get_manager -----------")
    #     result = request.env['res.users'].sudo().search([]).read(mainfields)
    #     manager = {'success': result or {}, 'error': None}
    #
    #     return manager
    #
    # @http.route('/wmvdapi/get_zsm', methods=["POST"], type='json', auth='user')
    # def get_zsm(self):
    #     print("------------/wmvdapi/get_zsm -----------")
    #     result = request.env['res.users'].sudo().search([]).read(mainfields)
    #     zsm = {'success': result or {}, 'error': None}

        # return zsm





