from odoo import http
from odoo.http import request
from datetime import datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
mainfields = ['id', 'name']
headers = {'Content-Type': 'application/json'}
company_id = 3
status_dict = {
        'draft':'Draft',
        'done':'Submitted',
        'tse_approved':'TSE Approved',
        'lab_approved':'LAB Approved',
        'zsm_approved':'ZSM Approved',
        'product_head_approved':'Product Head Approved',
        'closed':'Closed',
        }
class WpCirController(http.Controller):

    # @http.route('/wmvdapi/create_cir', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/create_cir', methods=["POST"], type='json', auth='public')
    def create_cir(self, cir_id=None, user_id=None,name=None,product_ids=None,complaint_id=None,complaint_extent=None,complaint_received_date=None
                   ,partner_id=None,partner_address=None,lead_id=None,state_id=None,zone=None,partner_group_id=None,batch_no=None,investigator_id=None,
                   manager_id=None,source_id=None,invoice_no=None,invoice_value=None,quantity_supplied=None,invoice_date=None,pod_details=None,courier_details=None,applicator_date=None,
                   salesperson_remark=None,salesuser_cir_attachments=None,salesuser_id=None,filename=None):
        print("------------/wmvdapi/create_cir -----------", user_id)

        product_ids = request.env['product.product'].sudo().search([('id','in',product_ids)])
        complaint_id = request.env['cir.complaint.master'].sudo().search([('id','=',complaint_id)])
        partner_id = request.env['res.partner'].sudo().search([('id','=',partner_id)])
        lead_id = request.env['crm.lead'].sudo().search([('id','=',lead_id)])
        salesuser_id = request.env['res.users'].sudo().search([('id','=',salesuser_id)])
        manager_id = request.env['res.users'].sudo().search([('id','=',manager_id)])
        investigator_id = request.env['res.users'].sudo().search([('id','=',investigator_id)])
        state_id = request.env['res.country.state'].sudo().search([('id','=',state_id)])
        partner_group_id = request.env['res.partner.group'].sudo().search([('id','=',partner_group_id)])
        source_id = request.env['org.master'].sudo().search([('id','=',source_id)])


        # cir_attachments_ids = []
        # tse_cir_attachments_ids = []
        salesuser_cir_attachments_ids = []
        product_response = []
        vals={
            'mobile_id':cir_id,
            'product_id':[(6, 0, product_ids.ids)] or None,
            'complaint_id': complaint_id.id or None,
            'complaint_extent': complaint_extent or None,
            'complaint_received_date': datetime.strptime(complaint_received_date, "%d/%m/%Y") or None,
            'partner_id': partner_id.id or None,
            'partner_address': partner_address or "",
            'lead_id': lead_id.id or None,
            'state_id': state_id.id or None,
            'zone': zone or None,
            'partner_group_id': partner_group_id.id or None,
            'batch_no': batch_no or '',
            'investigator_id': investigator_id.id or None,
            'manager_id': manager_id.id or None,
            'source_id': source_id.id or None,
            'invoice_no': invoice_no or None,
            'invoice_value': invoice_value or None,
            'quantity_supplied': quantity_supplied or None,
            'invoice_date': datetime.strptime(invoice_date, "%d/%m/%Y") or None,
            'pod_details': pod_details or None,
            'courier_details': courier_details or None,
            'applicator_date': datetime.strptime(applicator_date, "%d/%m/%Y") or None,
            'salesperson_remark': salesperson_remark or "",
            'salesuser_id':salesuser_id.id or None,
        }

        cir = request.env['cir.extension'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(vals)
        # if cir_attachments:
        #     # for res in sample_attachments:
        #     attachment_id = request.env['ir.attachment'].with_context(
        #         mail_auto_subscribe_no_notify=True).sudo().create({
        #         'name': cir.name + "cir",
        #         'type': 'binary',
        #         'datas': cir_attachments,  # image, #image.decode('base64'), #base64.b64encode(image),
        #         'store_fname': cir.name,
        #     })
        #     cir_attachments_ids.append(attachment_id.id)
        # cir.sudo().update({
        #     'cir_attachments': [(6, 0, cir_attachments_ids)],
        # })
        #
        # if tse_cir_attachments:
        #     # for res in sample_attachments:
        #     attachment_id = request.env['ir.attachment'].with_context(
        #         mail_auto_subscribe_no_notify=True).sudo().create({
        #         'name': cir.name + "tse_cir",
        #         'type': 'binary',
        #         'datas': tse_cir_attachments,  # image, #image.decode('base64'), #base64.b64encode(image),
        #         'store_fname': cir.name,
        #     })
        #     tse_cir_attachments_ids.append(attachment_id.id)
        # cir.sudo().update({
        #     'tse_cir_attachments': [(6, 0, tse_cir_attachments_ids)],
        # })

        if salesuser_cir_attachments:
            for res in salesuser_cir_attachments:
                attachment_id = request.env['ir.attachment'].with_context(
                    mail_auto_subscribe_no_notify=True).sudo().create({
                    'name': res.get('filename'),
                    'type': 'binary',
                    'datas': res.get('file'),  # image, #image.decode('base64'), #base64.b64encode(image),
                    'store_fname': res.get('filename'),
                })
                salesuser_cir_attachments_ids.append(attachment_id.id)
        cir.sudo().update({
            'salesuser_cir_attachments': [(6, 0, salesuser_cir_attachments_ids)],
        })

        for product in cir.product_id:
            product_response.append({'id':product.id,'name':product.name})
        status = status_dict[cir.state]
        response_vals = {
            'cir_id':cir.mobile_id,
            'portal_id':cir.id,
            'product': product_response,
            'state': status or '',
            'complaint_id': cir.complaint_id.id or None,
            'complaint_name': cir.complaint_id.name or '',
            'complaint_extent': cir.complaint_extent or '',
            'complaint_received_date': cir.complaint_received_date or None,
            'partner_id': cir.partner_id.id or None,
            'partner_name': cir.partner_id.name or '',
            'partner_address': cir.partner_address or "",
            'lead_id': cir.lead_id.id or None,
            'lead_name': cir.lead_id.name or '',
            'state_id': cir.state_id.id or None,
            'state_name': cir.state_id.name or '',
            'zone': cir.zone or None,
            'partner_group_id': cir.partner_group_id.id or None,
            'partner_group_name': cir.partner_group_id.name or '',
            'batch_no': cir.batch_no or '',
            'investigator_id': cir.investigator_id.id or None,
            'investigator_name': cir.investigator_id.name or '',
            'manager_id': cir.manager_id.id or None,
            'manager_name': cir.manager_id.name or '',
            'source_id': cir.source_id.id or None,
            'source_name': cir.source_id.name or '',
            'invoice_no': cir.invoice_no or '',
            'invoice_value': cir.invoice_value or 0.0,
            'quantity_supplied': cir.quantity_supplied or 0.0,
            'invoice_date': cir.invoice_date or None,
            'pod_details': cir.pod_details or '',
            'courier_details': cir.courier_details or '',
            'applicator_date': cir.applicator_date or None,
            'salesperson_remark': cir.salesperson_remark or "",
            'salesuser_cir_attachments':cir.salesuser_cir_attachments.ids,
            'filename':cir.salesuser_cir_attachments.ids,
            'salesuser_id': cir.salesuser_id.id or None,
            'salesuser_name': cir.salesuser_id.name or '',
        }

        response = {'cir': response_vals}
        return {'success': response, 'error': None}

    # @http.route('/wmvdapi/get_all_cir', auth='user', methods=["POST"], type='json')
    @http.route('/wmvdapi/get_all_cir', auth='public', methods=["POST"], type='json')
    def get_all_cir(self, user_id=None):
        print("------------/wmvdapi/get_all_cir -----------")
        recs = request.env['cir.extension'].sudo().search([('salesuser_id','=',user_id)])

        cir_list=[]
        if recs:
            for rec in recs:
                product_response = []
                for product in rec.product_id:
                    product_response.append({'id': product.id, 'name': product.name})
                status = status_dict[rec.state]
                cir_list.append({
                    'cir_id': rec.mobile_id,
                    'name': rec.name or None,
                    'portal_id': rec.id,
                    'product': product_response,
                    'complaint_id': rec.complaint_id.id or None,
                    'state': status or ' ',
                    'complaint_name': rec.complaint_id.name or '',
                    'complaint_extent': rec.complaint_extent or None,
                    'complaint_received_date': rec.complaint_received_date or None,
                    'partner_id': rec.partner_id.id or None,
                    'partner_name': rec.partner_id.name or '',
                    'partner_address': rec.partner_address or "",
                    'lead_id': rec.lead_id.id or None,
                    'lead_name': rec.lead_id.name or '',
                    'state_id': rec.state_id.id or None,
                    'state_name': rec.state_id.name or '',
                    'zone': rec.zone or None,
                    'partner_group_id': rec.partner_group_id.id or None,
                    'partner_group_name': rec.partner_group_id.name or '',
                    'batch_no': rec.batch_no or '',
                    'investigator_id': rec.investigator_id.id or None,
                    'investigator_name': rec.investigator_id.name or '',
                    'manager_id': rec.manager_id.id or None,
                    'manager_name': rec.manager_id.name or '',
                    'source_id': rec.source_id.id or None,
                    'source_name': rec.source_id.name or '',
                    'invoice_no': rec.invoice_no or '',
                    'invoice_value': rec.invoice_value or 0.0,
                    'quantity_supplied': rec.quantity_supplied or 0.0,
                    'invoice_date': rec.invoice_date or None,
                    'pod_details': rec.pod_details or '',
                    'courier_details': rec.courier_details or '',
                    'applicator_date': rec.applicator_date or None,
                    'salesperson_remark': rec.salesperson_remark or "",
                    'salesuser_cir_attachments': rec.salesuser_cir_attachments.ids,
                    'salesuser_id': rec.salesuser_id.id or None,
                    'salesuser_name': rec.salesuser_id.name or '',
                })
        response = {'cir_list': cir_list}
        return {'success': response, 'error': None}

    # @http.route('/wmvdapi/get_products', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_products', methods=["POST"], type='json', auth='public')
    def get_products(self):
        print("------------/wmvdapi/get_products -----------")

        result = request.env['product.product'].sudo().search([]).read(mainfields)
        product = {'success': result or {}, 'error': None}

        return product

    # @http.route('/wmvdapi/get_salesuser', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_salesuser', methods=["POST"], type='json', auth='public')
    def get_salesuser(self):
        print("------------/wmvdapi/get_salesuser -----------")
        result = request.env['res.users'].sudo().search([]).read(mainfields)
        salesuser = {'success': result or {}, 'error': None}

        return salesuser

    # @http.route('/wmvdapi/get_complaint', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_complaint', methods=["POST"], type='json', auth='public')
    def get_complaint(self):
        print("------------/wmvdapi/get_complaint -----------")
        result = request.env['cir.complaint.master'].sudo().search([]).read(['id','name','opt_out'])
        complaint = {'success': result or {}, 'error': None}

        return complaint

    # @http.route('/wmvdapi/get_source_of_supply', methods=["POST"], type='json', auth='user')
    @http.route('/wmvdapi/get_source_of_supply', methods=["POST"], type='json', auth='public')
    def get_source_of_supply(self):
        print("------------/wmvdapi/get_source_of_supply -----------")
        result = request.env['org.master'].sudo().search([]).read(mainfields)
        complaint = {'success': result or {}, 'error': None}

        return complaint