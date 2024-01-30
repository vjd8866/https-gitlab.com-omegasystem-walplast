from odoo import models, fields, api
import base64
import csv
from io import StringIO
from tempfile import TemporaryFile
from xlrd import open_workbook
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger('filtered.xlsx')

class MapDepot(models.TransientModel):
    _name = 'map.depot'

    file = fields.Binary("Upload File")


    # To Remove
    # def import_partners(self):
    #     partner_env = self.env['res.partner']
    #     wb = open_workbook(file_contents=base64.decodestring(self.file))
    #     partner_list = []
    #     for s in wb.sheets():
    #         for row in range(1, s.nrows):
    #             company_id = self.env['res.company'].sudo().search([('name','=',s.cell(row, 35).value)])
    #             state_id = self.env['res.country.state'].sudo().search([('name','=',s.cell(row, 6).value)])
    #             district_id = self.env['res.state.district'].sudo().search([('name','=',s.cell(row, 4).value),('state_id.id','=',state_id.id)],limit=1)
    #             country_id = self.env['res.country'].sudo().search([('name','=',s.cell(row, 7).value)])
    #             partner_group_id = self.env['res.partner.group'].sudo().search([('name','=',s.cell(row, 10).value),('company_id','=',company_id.id)],limit=1)
    #             user1_id = self.env['wp.c.elementvalue'].sudo().search([('name','=',s.cell(row, 20).value),('company_id','=',company_id.id),('c_element_id','in',('1000005','1000008'))])
    #             user2_id = self.env['wp.c.elementvalue'].sudo().search([('name','=',s.cell(row, 21).value),('company_id','=',company_id.id),('c_element_id','in',('1000013','1000017'))])
    #             user_id = self.env['res.users'].sudo().search([('name','=',s.cell(row, 24).value),('active','=',True)])
    #             manager_id = self.env['res.users'].sudo().search([('name','=',s.cell(row, 25).value),('active','=',True)])
    #             partner_exist = partner_env.sudo().search([('name','=',s.cell(row, 0).value),('company_id','=',company_id.id)])
    #             if not partner_exist:
    #                 _logger.info("######### Partner : ", s.cell(row, 0).value)
    #                 partner_vals = {
    #                     'name': s.cell(row, 0).value,
    #                     'company_type': s.cell(row, 1).value,
    #                     'street': s.cell(row, 2).value or '',
    #                     'street2': s.cell(row, 3).value or '',
    #                     'district_id': district_id.id if district_id else False,
    #                     'city': s.cell(row, 5).value or '',
    #                     'state_id': state_id.id if state_id else False,
    #                     'country_id': country_id.id if country_id else False,
    #                     'zip': s.cell(row, 8).value or '',
    #                     'zone': s.cell(row, 9).value or None,
    #                     'partner_group_id': partner_group_id.id if partner_group_id else False,
    #                     'contact_name': s.cell(row, 11).value or '',
    #                     'aadhar_no': s.cell(row, 12).value or '',
    #                     'pan_no': s.cell(row, 13).value or '',
    #                     'gst_no': s.cell(row, 14).value or '',
    #                     'pricelist': s.cell(row, 15).value or '',
    #                     # 'declaration_received': s.cell(row, 16).value,
    #                     'bp_code': s.cell(row, 16).value or '',
    #                     'phone': s.cell(row, 17).value or '',
    #                     'mobile': s.cell(row, 18).value or '',
    #                     'email': s.cell(row, 19).value or '',
    #                     'user1_id': user1_id.id if user1_id else False ,
    #                     'user2_id': user2_id.id if user2_id else False,
    #                     'creditstatus': s.cell(row, 22).value or None,
    #                     'so_creditlimit': s.cell(row, 23).value or None,
    #                     'user_id': user_id.id if user_id else False,
    #                     'manager_id': manager_id.id if manager_id else False,
    #                     'cst_no': s.cell(row, 26).value or '',
    #                     'tin_no': s.cell(row, 27).value or '',
    #                     'vat_no': s.cell(row, 28).value or '',
    #                     'taxid': s.cell(row, 29).value or '',
    #                     'c_bpartner_id': s.cell(row, 30).value or '',
    #                     'c_location_id': s.cell(row, 31).value or '',
    #                     'c_bpartner_location_id': s.cell(row, 33).value or '',
    #                     # 'bulk_payment_bool': s.cell(row, 34).value ,
    #                     'company_id': company_id.id if company_id else False,
    #                 }
    #                 partner_list.append(partner_vals)
    #     if partner_list:
    #         partner_env.sudo().create(partner_list)

    def map_depot(self):
        # csv_datas = self.file
        fileobj = TemporaryFile('wb+')

        wb = open_workbook(file_contents=base64.decodebytes(self.file))

        for s in wb.sheets():

            for row in range(1, s.nrows):
                depot_code = "APL" + (str(s.cell(row, 2).value).split('.'))[0]
                depot = self.env['transporter.customer'].sudo().search(
                    [('bp_code', '=', depot_code), ('isactive', '=', True)], limit=1)
                transporter = self.env['wp.transporter'].sudo().search(
                    [('code', '=', str((s.cell(row, 1).value))), ('isactive', '=', True)], limit=1)
                # if not depot:
                #     raise UserError(('Depot code %s not found') % depot_code)
                # if not transporter:
                #     raise UserError(('Transporter %s not found') % transporter.name)

                if transporter and depot:
                    depot.transporter_id = transporter.id
                    print("Transporter ", transporter.name, "Updated")

                    if depot.id not in transporter.depot_ids.ids:
                        transporter.depot_ids = [(4, depot.id)]
                        print("Depot ", depot.name, "added to transporter", transporter.name)

                if not transporter:
                    raise ValidationError(("Transporter %s does not exist in the system") % (s.cell(row, 1).value))
                if not depot:
                    raise ValidationError(("Depot %s does not exist in the system") % (depot_code))
