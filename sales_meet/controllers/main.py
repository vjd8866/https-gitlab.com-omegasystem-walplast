import ast
from odoo import http
from odoo.http import request
import json
import requests

class QrCodeController(http.Controller):

    @http.route('/qr/ho/scan', type='http', auth="user", website="true", methods=['GET', 'POST'],csrf=False)
    def qr_scan(self, **post):
        recheck = request.env['barcode.marketing.check'].sudo().create({
            'recheck_bool':True,
            'accepted_count':0,
            'rejected_count':0
        })
        return http.request.render('sales_meet.web_barcode_scan', {'recheck':recheck,
                                                                   'msg':""})

    @http.route('/barcode/scanned', type='http', auth="public", website="true", methods=['GET','POST'], csrf=False)
    def barcode_scan(self, **post):
        barcode = int(post['barcode'])
        rec_id = int(post['recheck'])
        coupon_worth = float(post['coupon_worth']) if post['coupon_worth'] else 0.0
        recheck = request.env['barcode.marketing.check'].sudo().search([('id','=',rec_id)])

        if coupon_worth > 0.0:
            recheck.amount = coupon_worth

        accept_list_qrcode = []
        reject_list_qrcode = []
        if recheck.accepted:
            accept_list_qrcode = ast.literal_eval(recheck.accepted)

        if recheck.rejected:
            reject_list_qrcode = ast.literal_eval(recheck.rejected)

        if barcode in accept_list_qrcode or barcode in reject_list_qrcode :
            message = "twice_scanned"
            # test = json.dumps(message)
            return message

        if recheck.state == 'recheck':
            message = "rechecked"
            return message
        barcode_id = request.env['barcode.marketing.line'].sudo().search([('name', '=', barcode), ('recheck_bool', '=', False)])

        if barcode_id:
            accept_list_qrcode.append(barcode)
            recheck.accepted = accept_list_qrcode
            recheck.accepted_count = recheck.count_accepted = len(accept_list_qrcode)
            message = "accepted"
        else:
            reject_list_qrcode.append(barcode)
            recheck.rejected = reject_list_qrcode
            recheck.rejected_count = len(reject_list_qrcode)
            # message = "Rejected QR: " + str(barcode)
            message = "rejected"
            return message

    @http.route('/qr/scan/submit', type='http', auth="public", website="true", methods=['GET', 'POST'], csrf=False)
    def submit_qr_scan(self,**post):
        rec_id = int(post['recheck'])
        recheck = request.env['barcode.marketing.check'].sudo().search([('id', '=', rec_id)])
        recheck.recheck_records()




#from odoo.addons.base_rest.controllers import main


#class SalesMeetPublicApiController(main.RestController):
#    _root_path = "/sales_meet_api/public/"
#    _collection_name = "sales.meet.public.services"
#    _default_auth = "public"


#class SalesMeetPrivateApiController(main.RestController):
#    _root_path = "/sales_meet_api/private/"
#    _collection_name = "sales.meet.private.services"
#    _default_auth = "user"



# class BankPaymentController(http.Controller):
# 	_cp_path = '/csv'

# 	@http.route('/csv/download/<int:rec_id>/', type='http', auth='none', website=True)
# 	def csvdownload(self, rec_id, **kw):
# 		# print "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr"
# 		return http.request.env['sales_meet.bank_payment']._csv_download({'rec_id': rec_id})

