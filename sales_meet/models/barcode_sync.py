

import csv
import re
import base64
import pytz
from odoo import tools, api
from odoo import api, fields, models, _ , registry, SUPERUSER_ID
from odoo.exceptions import UserError, Warning, ValidationError
from datetime import datetime, timedelta, date
import logging
from multiprocessing import Process, Pool
import threading
import time
import xmlrpc.client as xmlrpclib
import erppeek

from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class CouponSynchroServer(models.Model):
    """Class to store the information regarding server."""

    _name = "coupon.synchro.server"
    _description = "Coupon Synchronized server"

    name = fields.Char('Server name', required=True)
    server_url = fields.Char('Server URL', required=True)
    server_port = fields.Integer('Server Port', required=True, default=8069)
    server_db = fields.Char('Server Database', required=True)
    login = fields.Char('User Name', required=True)
    password = fields.Char('Password', required=True)
    obj_ids = fields.One2many('coupon.synchro.obj', 'server_id', string='Models',
                              ondelete='cascade')


class CouponSynchroObj(models.Model):
    _name = "coupon.synchro.obj"
    _description = "Register Class"
    _order = 'id desc'

    name = fields.Char('Name')
    domain = fields.Char('Domain', default='[]')
    server_id = fields.Many2one('coupon.synchro.server', 'Server',
                                ondelete='cascade',  required=True)

    action = fields.Selection([('d', 'Download'), ('u', 'Upload'), ('b','Both')],
                              'Synchronization direction', required=True, default='d')
    sequence = fields.Integer('Sequence')
    active = fields.Boolean('Active', default=True)
    synchronize_date = fields.Datetime('Latest Synchronization')
    coupon_date = fields.Date('Coupon Date')
    sheet_id = fields.Integer('Sheet ID')
    state = fields.Selection([('draft', 'Draft'), ('synced', 'Synced')], default='draft')


    def recheck_synchronize(self):
        start = time.time()

        mainfields = ['id', 'name', 'rechecked_date']
        modelname = 'barcode.marketing.line'

        url = 'http://' + str(self.server_id.server_url) + ':' + str(self.server_id.server_port)
        db, uid, password = self.server_id.server_db, self.server_id.login, self.server_id.password
        client = erppeek.Client(url, db, uid, password)

        proxy = client.model(modelname)

        if self.action == 'd':          
            # value = proxy.read([('rechecked_date','<=',self.coupon_date)],mainfields)
            value = proxy.browse([('rechecked_date','>=',self.coupon_date)]).read(mainfields)
            lines = []
            # print "0000000000000000000000000", len(value)
            for rec in value:
                # print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", rec
                rec['recheck_bool'] = True
                rec_id = rec['id']
                coupon_name = rec['name']

                if 'id' in rec: del rec['id']
                if 'name' in rec: del rec['name']

                # print "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", rec

                self.env[modelname].sudo().search([('name','=',coupon_name)]).write(rec)
                # print "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", lines

        if self.action == 'u':
            value = self.env[modelname].read([('rechecked_date','>=',self.coupon_date)],mainfields)
            for rec in value:
                rec['recheck_bool'] = True
                rec_id = rec['id']
                coupon_name = rec['name']

                proxy.sudo().search([('name','=',coupon_name)]).write(rec)


        self.write({'name': 'CS/R/' + self.action + '/' +str(self.id), 
                    'synchronize_date': datetime.now(),
                    'state':'synced'})

        end = time.time()
        # print "-------------------------------- generate_QR TIME" , end-start



    def synchronize(self):
        start = time.time()

        mainfields = ['date', 'product_name', 'barcode', 'amount', 'name', 'lines_one2many']
        subfields = ['name', 'date' , 'amount', 'product_name']
        modelname = 'barcode.marketing'
        submodelname = 'barcode.marketing.line'

        url = 'http://' + str(self.server_id.server_url) + ':' + str(self.server_id.server_port)
        db, uid, password = self.server_id.server_db, self.server_id.login, self.server_id.password
        client = erppeek.Client(url, db, uid, password)

        proxy = client.model(modelname)
        value = proxy.read([('date','=',self.coupon_date),('id','=',self.sheet_id)],mainfields)

        for rec in value:
            rec['state'] = 'generated'
            rec_list = rec['lines_one2many']

            if 'lines_one2many' in rec: del rec['lines_one2many']

            idnew = self.env[modelname].sudo().create(rec)
            # new_id = idnew.id

            subvaluelist = []
            selected_lines = []
            lines_proxy = client.model(submodelname)
            subvaluelist = lines_proxy.browse(rec_list).read(subfields)

            for rec in subvaluelist:
                selected_lines.append((0, 0, rec))

            idnew.lines_one2many = selected_lines             

        self.synchronize_date = datetime.now()
        self.state = 'synced'
        self.name = 'CS/D/' +str(self.id)
        end = time.time()
        # print "-------------------------------- generate_QR TIME" , end-start


    def update_csv_records(self):
        # print "111111111111111111111111111111"

        barcode_lines = self.env['barcode.marketing.line']
        partner_ids = self.env['res.partner']
        
        filename = "/tmp/barcode_lines.csv"

        # initializing the titles and rows list 
        fields = [] 
        rows = [] 

        # reading csv file 
        with open(filename, 'r') as csvfile: 
            # print "22222222222222222222222222222222222"
            reader_info = []

            delimeter = ','
            reader = csv.reader(csvfile, delimiter=delimeter,lineterminator='\r\n')
            try:
                reader_info.extend(reader)
            except Exception:
                reader_info.extend(reader)
                raise Warning(_("Not a valid file!"))
            keys = reader_info[0]
            # check if keys exist

            # id,name,barcode_marketing_id,flag,date,bp_code,amount,product_name
            if not isinstance(keys, list) or ('id' not in keys or
                                              'name' not in keys or
                                              'flag' not in keys or
                                              'date' not in keys ):
                raise Warning(
                    _("'id' or 'name' or  'flag'  keys not found"))
            del reader_info[0]
            values = {}
            # credit_note.write({'imported': True,})
            count = 0
            
            for i in range(len(reader_info)):
                
                val = {}
                field = reader_info[i]
                values = dict(zip(keys, field))
    
                partner_list = partner_ids.search([('bp_code', '=',values['bp_code'])], limit= 1)
                if partner_list:
                    if  partner_list[0].id:

                        val['partner_id'] = partner_list[0].id
                        # print "666666666666666666" , values['bp_code']
                    else:
                        # print "7777777777777777777777" , values['bp_code']
                        raise Warning(_("Partner not found"))
                
                val['id'] = values['id']
                val['name'] = values['name']
                val['barcode_marketing_id'] = values['barcode_marketing_id']
                
                if values['flag'] == 'f':
                    flag = False
                else:
                    flag = True
                # # print "3333333333333333333333333333333333" , values['flag'] , type(values['flag']) , flag
                val['flag'] = flag
                val['date'] = values['date']
                val['amount'] = values['amount']
                val['product_name'] = values['product_name']
                
                barcode_lines = barcode_lines.sudo().create(val)
                count += 1
                # print "3333333333333333333333333333333333" , barcode_lines, count