

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, timedelta, date , time
import base64
import io
from werkzeug.urls import url_encode
import csv
import time

class WpRetailerImport(models.TransientModel):
    _name = 'wp.retailer.import'
    _description = 'Retailer Import'
    
    retailer_csv_data = fields.Char('Name', size=256 , copy=False)
    retailer_file_name = fields.Binary('Retailer Import', copy=False)  
     

    def action_upload(self):
        start = time.time()
        retailer_obj = self.env['wp.retailer']
        reader_info = []
        data = base64.b64decode(self.retailer_file_name)
        file_input = io.StringIO(data.decode("utf-8"))
        file_input.seek(0)
        reader = csv.reader(file_input, delimiter=',')
        try:
            reader_info.extend(reader)
        except Exception:
            reader_info.extend(reader)
            raise Warning(_("Not a valid file!"))
        keys = reader_info[0]
        # check if keys exist
        if not isinstance(keys, list) or ('Name' not in keys or
                                          'bp_code' not in keys or
                                          'Mobile' not in keys or
                                          'salesperson_id' not in keys or
                                          'manager_id' not in keys):
            raise Warning(_("'Name' or 'bp_code' or 'Mobile' or 'salesperson_id' or 'manager_id' keys not found"))
        del reader_info[0]
        values = {}
        
        for i in range(len(reader_info)):
            field = reader_info[i]
            values = dict(zip(keys, field))

            distributor_ids = self.env['res.partner'].sudo().search([('bp_code', '=',values['bp_code'])], limit= 1)
            if distributor_ids:
                Distributor = distributor_ids.id
            else :
                raise Warning(_( values['bp_code'] + " is not found in any Distributor. Kindly Recheck & update the Sheet"))

            country_ids = self.env['res.country.state'].sudo().search([('id', '=',values['state_id'])], limit= 1)
            if country_ids:
                Country = country_ids.country_id.id
            else :
                raise Warning(_( values['state_id'] + " is not found in any state. Kindly Recheck & update the Sheet"))

            manager_ids = self.env['res.users'].sudo().search([('id', '=', int(values['manager_id']) )], limit= 1)
            if manager_ids:
                Manager = manager_ids.id
            else :
                raise Warning(_( values['manager_id'] + ' - ' + values['Manager'] + " is not found in any Manager. Kindly Recheck & update the Sheet"))

            salesperson_ids = self.env['res.users'].sudo().search([('id', '=', int(values['salesperson_id']) )], limit= 1)
            if salesperson_ids:
                Salesperson = salesperson_ids.id
            else :
                raise Warning(_( values['salesperson_id'] + ' - ' + values['Salesperson'] + " is not found in any Salesperson. Kindly Recheck & update the Sheet"))

            mobile = str(values['Mobile'])
            rids = retailer_obj.sudo().search([('mobile', '=',mobile)])

            if rids:
                if not rids.gst_no and values['GST']:
                    rids.gst_no = values['GST']
                if not rids.street and values['Street']:
                    rids.street = values['Street']
                if not rids.email and values['Email']:
                    rids.email = values['Email']
                if not rids.pan_no and values['PAN']:
                    rids.pan_no = values['PAN']
                if not rids.manager_id and values['manager_id']:
                    rids.manager_id = int(values['manager_id'])
                if not rids.zip and values['PIN']:
                    rids.zip = values['PIN']
                if not rids.cluster_id and values['cluster_id']:
                    rids.cluster_id = int(values['cluster_id'])

                print("------------ Updating ---- Retailer Data", rids.code, rids.name)

            else:
                vals = {
                        'active' : True,
                        'imported' : True,
                        'gst_no' : values['GST'],
                        'street' : values['Street'],
                        'city' : values['City'],
                        'user_id' : self.env.uid,
                        'zip' : values['PIN'],
                        'pan_no' : values['PAN'],
                        'country_id' : Country,
                        'company_id' : self.env.company.id,
                        # 'aadhar_no' : values['Aadhar'],
                        'email' : values['Email'],
                        'street2' : values['Street2'],
                        'date' : date.today(),
                        'name' : values['Name'],
                        # 'phone' : values['Phone'],
                        'mobile' : values['Mobile'],
                        'district_id' : values['district_id'] or False,
                        'state_id' : int(values['state_id']),
                        'distributer_id' : Distributor,
                        'zone' : values['Zone'],
                        'salesperson_id' : int(values['salesperson_id']),
                        'state' : 'draft',
                        'manager_id' : int(values['manager_id']),
                        'cluster_id' : int(values['cluster_id']) if values['cluster_id'] else False,
                }

                retailer = retailer_obj.with_context(mail_auto_subscribe_no_notify=True).sudo().create(vals)
                # print "------------- Creating ----- Retailer " ,retailer.code, retailer.name

        end = time.time()
        # print "------------- END retailers Created -------", end-start
