from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import time
import psycopg2
import string
import base64
from werkzeug import url_encode
import logging
from odoo.osv import osv
from time import gmtime, strftime
from datetime import datetime, timedelta, date, time


class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    transporter_id = fields.Many2one('wp.transporter', "Transporter")
    parent_id = fields.Many2one('res.partner', "Parent")


    def process_update_vendor_scheduler_queue(self):

        conn_pg = None
        state_id = 596
        config_id = self.env['external.db.configuration'].sudo().search([('state', '=', 'connected')], limit=1)
        if config_id:

            print
            "#-------------Select --TRY----------------------#"
            try:
                conn_pg = psycopg2.connect(dbname=config_id.database_name, user=config_id.username,
                                           password=config_id.password, host=config_id.ip_address, port=config_id.port)
                pg_cursor = conn_pg.cursor()

                print
                "lllllllllllllpg_cursor pg_cursorpg_cursorpg_cursorpg_cursorpg_cursor", pg_cursor

                today = datetime.today()
                # daymonth = today.strftime( "%Y-%m-%d 00:00:00")

                query = " select \
    cb.c_bpartner_id,cb.name,cb.name2,cb.value,cb.c_bp_group_id,cb.socreditstatus, \
    cb.so_creditlimit,cb.taxid,cb.Cst_Tax_No,cb.TinNo,cb.GST_Tax,cb.Pan_No,cb.SalesRep_ID,cb.C_PaymentTerm_ID, \
    cbl.c_bpartner_location_id,cbl.c_location_id,cbl.phone,cbl.phone2,cbl.email, \
    cl.address1,cl.address2,cl.address3,cl.postal,cl.c_country_id,cl.c_region_id,cl.city,cb.isvendor,cb.WPP_BPartner_Parent_ID,cb.ad_client_id \
    from adempiere.c_bpartner cb  \
    JOIN adempiere.c_bpartner_location cbl ON cbl.c_bpartner_id = cb.c_bpartner_id \
    JOIN adempiere.c_location cl ON cl.c_location_id = cbl.c_location_id \
    where cb.isactive = 'Y' and cb.isvendor = 'Y' and cl.c_country_id = 208 "

                pg_cursor.execute(query)
                records = pg_cursor.fetchall()

                if len(records) == 0:
                    pass

                # portal_bp_code = [x.bp_code for x in self.env['res.partner'].search([('bp_code', '!=', False),
                #                                                                      ('active', '!=', False)])]
                portal_c_bpartner_id = [x.c_bpartner_id for x in
                                        self.env['res.partner'].search([('bp_code', '!=', False),
                                                                        ('c_bpartner_id', '=', False),
                                                                        ('active', '!=', False)])]

                for record in records:
                    c_bpartner_id = (str(record[0]).split('.'))[0]
                    company = self.env['res.company'].sudo().search(
                        [('ad_client_id', '=', (str(record[28]).split('.'))[0])])

                    print
                    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK", record[3]
                    if c_bpartner_id not in portal_c_bpartner_id:

                        print
                        "jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj", record[23], record[24], record[4]
                        state = 'Created'

                        c_bp_group_id = (str(record[4]).split('.'))[0]
                        c_region_id = (str(record[24]).split('.'))[0]
                        c_country_id = (str(record[23]).split('.'))[0]
                        # c_bpartner_id = (str(record[0]).split('.'))[0]
                        c_bpartner_location_id = (str(record[14]).split('.'))[0]
                        c_location_id = (str(record[15]).split('.'))[0]

                        partner_group_id = self.env['res.partner.group'].sudo().search(
                            [('c_bp_group_id', '=', c_bp_group_id)]).id
                        user_id = 1

                        property_payment_term_id = self.env['account.payment.term'].sudo().search(
                            [('c_paymentterm_id', '=', record[13])], limit=1).id
                        country_id = self.env['res.country'].sudo().search([('c_country_id', '=', c_country_id)]).id
                        if record[24]:
                            state_id = self.env['res.country.state'].sudo().search(
                                [('c_region_id', '=', c_region_id)]).id

                        street2 = (str(record[20].encode('utf8'))) if record[20] else '' + \
                                                                                      (',' + str(
                                                                                          record[21].encode('utf8'))) if \
                            record[20] else ''

                        vals_line = {

                            'c_bpartner_id': c_bpartner_id,
                            'name': record[1],
                            'bp_code': record[3],
                            'partner_group_id': partner_group_id,
                            'creditstatus': record[5],
                            'so_creditlimit': record[6],
                            'taxid': record[7],
                            'cst_no': record[8],
                            'tin_no': record[9],
                            'gst_no': record[10],
                            'pan_no': record[11],
                            'user_id': user_id,
                            'property_payment_term_id': property_payment_term_id,
                            'c_bpartner_location_id': c_bpartner_location_id,
                            'c_location_id': c_location_id,
                            'phone': record[16],
                            'mobile': record[17],
                            'email': record[18],
                            'street': record[19],
                            'street2': street2,
                            'zip': record[22],
                            'country_id': country_id,
                            'state_id': state_id,
                            'city': record[25],
                            'state': state,
                            'customer': False,
                            'supplier': True if 'Y' in record[26] else False,
                            'company_id': company.id,
                            'company_type': 'company',

                        }
                        if record[27]:
                            parent_id = self.env['res.partner'].sudo().search([('c_bpartner_id', '=', record[27])],
                                                                              limit=1)
                            vals_line.update({
                                'parent_id': parent_id.id

                            })
                        self.env['res.partner'].create(vals_line)
                        print
                        "--------- Partner Created in CRM  ------"

                    if c_bpartner_id in portal_c_bpartner_id:
                        portal_partner = self.env['res.partner'].search([('bp_code', '=', record[3])])
                        portal_partner.write(
                            {'c_bpartner_id': c_bpartner_id})
                        if record[27]:
                            parent_id = self.env['res.partner'].sudo().search([('c_bpartner_id', '=', record[27])],
                                                                              limit=1)
                            portal_partner.update({
                                'parent_id': parent_id.id

                            })

                        print
                        "------------------- c_bpartner_id Updated in CRM  --------------"


            except psycopg2.DatabaseError as e:
                if conn_pg:
                    conn_pg.rollback()
                print('#-------------------Except------------------ %s' % e)

            finally:
                if conn_pg:
                    conn_pg.close()
                    print
                    "#--------------Select --44444444--Finally----------------------#", pg_cursor


    def import_parent_partners(self):
        conn_pg = None
        state_id = 596
        config_id = self.env['external.db.configuration'].sudo().search([('state', '=', 'connected')], limit=1)
        if config_id:

            print
            "#-------------Select --TRY----------------------#"
            try:
                conn_pg = psycopg2.connect(dbname=config_id.database_name, user=config_id.username,
                                           password=config_id.password, host=config_id.ip_address, port=config_id.port)
                pg_cursor = conn_pg.cursor()

                print
                "lllllllllllllpg_cursor pg_cursorpg_cursorpg_cursorpg_cursorpg_cursor", pg_cursor

                today = datetime.today()

                query = "select cb.c_bpartner_id,cb.name,cb.name2,cb.value,cb.c_bp_group_id,cb.socreditstatus,\
        						cb.so_creditlimit,cb.taxid,cb.Cst_Tax_No,cb.TinNo,cb.GST_Tax,cb.Pan_No,cb.SalesRep_ID,cb.C_PaymentTerm_ID,cb.ad_client_id \
        						from adempiere.c_bpartner cb where cb.iscustomer = 'Y' and cb.isactive = 'Y' and \
        						(select cbp.c_bpartner_id  from c_bpartner cbp where cbp.WPP_BPartner_Parent_ID=cb.c_bpartner_id LIMIT 1) IS NOT NULL"

                pg_cursor.execute(query)
                records = pg_cursor.fetchall()

                if len(records) == 0:
                    pass

                portal_bp_code = []

                portal_c_bpartner_id = [x.c_bpartner_id for x in
                                        self.env['res.partner'].search([('bp_code', '!=', False),
                                                                        ('c_bpartner_id', '!=', False),
                                                                        ('active', '!=', False)])]
                for record in records:
                    company = self.env['res.company'].sudo().search(
                        [('ad_client_id', '=', (str(record[14]).split('.'))[0])])
                    c_bpartner_id = (str(record[0]).split('.'))[0]

                    print
                    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK", record[3]
                    if c_bpartner_id not in portal_c_bpartner_id:
                        print
                        "jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj", record[4]
                        state = 'Created'

                        c_bp_group_id = (str(record[4]).split('.'))[0]
                        # c_region_id = (str(record[24]).split('.'))[0]
                        # c_country_id = (str(record[23]).split('.'))[0]
                        # c_bpartner_location_id = (str(record[14]).split('.'))[0]
                        # c_location_id = (str(record[15]).split('.'))[0]

                        partner_group_id = self.env['res.partner.group'].sudo().search(
                            [('c_bp_group_id', '=', c_bp_group_id)]).id
                        user_id = 1

                        property_payment_term_id = self.env['account.payment.term'].sudo().search(
                            [('c_paymentterm_id', '=', record[13])], limit=1).id

                        vals_line = {

                            'c_bpartner_id': c_bpartner_id,
                            'name': record[1],
                            'bp_code': record[3],
                            'partner_group_id': partner_group_id,
                            'creditstatus': record[5],
                            'so_creditlimit': record[6],
                            'taxid': record[7],
                            'cst_no': record[8],
                            'tin_no': record[9],
                            'gst_no': record[10],
                            'pan_no': record[11],
                            'user_id': user_id,
                            'property_payment_term_id': property_payment_term_id,
                            'state': state,
                            'customer': True,
                            'supplier': False,
                            'company_id': company.id,
                            'company_type': 'company',

                        }

                        self.env['res.partner'].create(vals_line)
                        print
                        "--------- Partner Created in CRM  ------"

                    if c_bpartner_id in portal_c_bpartner_id:
                        self.env['res.partner'].search([('bp_code', '=', record[3])]).write(
                            {'c_bpartner_id': c_bpartner_id})

                        print
                        "------------------- c_bpartner_id Updated in CRM  --------------"


            except psycopg2.DatabaseError as e:
                if conn_pg:
                    conn_pg.rollback()
                print
                '#-------------------Except------------------ %s' % e

            finally:
                if conn_pg:
                    conn_pg.close()
                    print
                    "#--------------Select --44444444--Finally----------------------#", pg_cursor