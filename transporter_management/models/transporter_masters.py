from odoo import api, fields, models, _
import psycopg2
from datetime import datetime, timedelta, date, time
import logging

_logger = logging.getLogger(__name__)


class TransportersOrderTime(models.Model):
    _name = 'transporter.order.time'

    name = fields.Char("Transporter Order Time", compute='compute_name')
    day_no = fields.Selection(
        [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),
         ('9', '9'), ('10', '10')], string="Days")
    days = fields.Selection([('After', 'After'), ('Before', 'Before'), ('Same Day', 'Same Day')], string="After/Before")
    add_note = fields.Char("Additional Note", default="")

    @api.depends('day_no', 'days', 'add_note')
    def compute_name(self):
        for rec in self:
            if rec.days and rec.day_no:
                if rec.days == 'Same Day':
                    rec.name = str(rec.days) + " "
                else:
                    if rec.day_no == '1':
                        if rec.days == 'After':
                            rec.name = "N+" + str(rec.day_no) + " (Next day) "
                        if rec.days == 'Before':
                            rec.name = "N-" + str(rec.day_no) + " (Previous day) "
                    else:
                        rec.name = "N" + ("-" if rec.days == 'Before' else "+") + str(rec.day_no) + " (" + str(
                            rec.days) + " " + str(rec.day_no) + "days) "
            else:
                rec.name = ''

            if rec.add_note:
                rec.name += rec.add_note

    @api.onchange('days')
    def onchange_same_day(self):
        for rec in self:
            if rec.days == "Same Day":
                rec.day_no = '0'

class TruckType(models.Model):
    _name = 'truck.type'

    name = fields.Float("Truck Types")




class TruckReportingTime(models.Model):
    _name = 'truck.reporting.time'

    name = fields.Char("Truck Reporting Time")


class Transporters(models.Model):
    _name = 'wp.transporter'

    name = fields.Char("Transporter Name")
    code = fields.Char("Code")
    plant = fields.Many2one('wp.plant', "Plant")
    depot_ids = fields.Many2many('transporter.customer', 'customer_depot_rel', string="Depot IDs")
    isactive = fields.Boolean("Active", default=True)


class Plants(models.Model):
    _name = 'wp.plant'

    name = fields.Char("Code")
    plant_name = fields.Char("Name")
    location = fields.Many2one('wp.locations', "Location")


class TPRProduct(models.Model):
    _inherit = 'product.product'

    bp_name = fields.Many2one('transporter.customer', string="Business Partner")


class TransporterCustomers(models.Model):
    _name = 'transporter.customer'
    _rec_name = 'bp_code'

    name = fields.Char("Name")
    c_bpartner_id = fields.Char("Idempiere ID")
    bp_code = fields.Char("Partner Code")
    partner_group_id = fields.Many2one('res.partner.group', "Partner Group")
    creditstatus = fields.Selection([
        ('H', 'Credit Hold'),
        ('O', 'Credit OK'),
        ('S', 'Credit Stop'),
        ('W', 'Credit Watch'),
        ('X', 'No Credit Check')], 'Credit Status', default='W', track_visibility='onchange')
    so_creditlimit = fields.Float(string="Credit limit")
    taxid = fields.Char('Tax ID')
    cst_no = fields.Char('CST No')
    tin_no = fields.Char('TIN No')
    gst_no = fields.Char('GST No')
    pan_no = fields.Char('Pan No')
    user_id = fields.Many2one('res.users', "User")
    c_location_id = fields.Char('Location ID')
    c_bpartner_location_id = fields.Char('Address ID')
    ad_client_id = fields.Integer(string="ad_client_id")
    company_id = fields.Many2one('res.company', string="Company")
    phone = fields.Char("Phone")
    mobile = fields.Char("Mobile")
    email = fields.Char("Email")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    zip = fields.Char("Zip Code")
    country_id = fields.Char("Country")
    state_id = fields.Char("State")
    city = fields.Char("City")
    parent_id = fields.Many2one('transporter.customer', "Parent Partner")
    transporter_id = fields.Many2one('wp.transporter', "Transporter")
    isactive = fields.Boolean("Active")

    def process_update_trm_customer_scheduler(self):

        conn_pg = None
        state_id = 596
        config_id = self.env['external.db.configuration'].sudo().search([('state', '=', 'connected')], limit=1)
        if config_id:

            print("#-------------Select --TRY----------------------#")
            try:
                conn_pg = psycopg2.connect(dbname=config_id.database_name, user=config_id.username,
                                           password=config_id.password, host=config_id.ip_address, port=config_id.port)
                pg_cursor = conn_pg.cursor()

                print("lllllllllllllpg_cursor pg_cursorpg_cursorpg_cursorpg_cursorpg_cursor", pg_cursor)

                today = datetime.today()
                # daymonth = today.strftime( "%Y-%m-%d 00:00:00")

                query = " select \
        cb.c_bpartner_id,cb.name,cb.name2,cb.value,cb.c_bp_group_id,cb.socreditstatus, \
        cb.so_creditlimit,cb.taxid,cb.Cst_Tax_No,cb.TinNo,cb.GST_Tax,cb.Pan_No,cb.SalesRep_ID,cb.C_PaymentTerm_ID, \
        cbl.c_bpartner_location_id,cbl.c_location_id,cbl.phone,cbl.phone2,cbl.email, \
        cl.address1,cl.address2,cl.address3,cl.postal,cl.c_country_id,cl.c_region_id,cl.city,cb.ad_client_id,cb.WPP_BPartner_Parent_ID \
        from adempiere.c_bpartner cb  \
        JOIN adempiere.c_bpartner_location cbl ON cbl.c_bpartner_id = cb.c_bpartner_id \
        JOIN adempiere.c_location cl ON cl.c_location_id = cbl.c_location_id \
        where cb.iscustomer = 'Y' and cb.isactive = 'Y' and cl.c_country_id = 208 "

                pg_cursor.execute(query)
                records = pg_cursor.fetchall()

                if len(records) == 0:
                    pass

                portal_c_bpartner_id = [x.c_bpartner_id for x in
                                        self.env['transporter.customer'].search([('bp_code', '!=', False),
                                                                                 ('c_bpartner_id', '!=', False)])]

                for record in records:
                    c_bpartner_id = (str(record[0]).split('.'))[0]
                    company = self.env['res.company'].sudo().search(
                        [('ad_client_id', '=', (str(record[26]).split('.'))[0])])
                    parent = self.env['transporter.customer'].sudo().search(
                        [('c_bpartner_id', '=', (str(record[27]).split('.'))[0])], limit=1)

                    print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK", record[3])
                    if c_bpartner_id not in portal_c_bpartner_id:

                        print("jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj", record[23], record[24], record[4])

                        c_bp_group_id = (str(record[4]).split('.'))[0]
                        c_region_id = (str(record[24]).split('.'))[0]
                        c_country_id = (str(record[23]).split('.'))[0]
                        c_bpartner_location_id = (str(record[14]).split('.'))[0]
                        c_location_id = (str(record[15]).split('.'))[0]

                        partner_group_id = self.env['res.partner.group'].sudo().search(
                            [('c_bp_group_id', '=', c_bp_group_id)]).id
                        user_id = 1

                        # property_payment_term_id = self.env['account.payment.term'].sudo().search(
                        #     [('c_paymentterm_id', '=', record[13])]).id
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
                            # 'property_payment_term_id': property_payment_term_id,
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
                            'company_id': company.id,
                            'parent_id': parent.id,
                            'isactive': True

                        }

                        self.env['transporter.customer'].create(vals_line)
                        print("--------- Partner Created in TRM  ------")

                    if c_bpartner_id in portal_c_bpartner_id:
                        self.env['transporter.customer'].search([('bp_code', '=', record[3])]).write(
                            {'c_bpartner_id': c_bpartner_id,
                             'parent_id': parent.id})

                        print("------------------- c_bpartner_id Updated in TRM  --------------")


            except psycopg2.DatabaseError as e:
                if conn_pg:
                    conn_pg.rollback()
                print('#-------------------Except------------------ %s' % e)

            finally:
                if conn_pg:
                    conn_pg.close()
                    print("#--------------Select --44444444--Finally----------------------#", pg_cursor)

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
                                        self.env['transporter.customer'].search([('bp_code', '!=', False),
                                                                                 ('c_bpartner_id', '!=', False)])]
                for record in records:
                    company = self.env['res.company'].sudo().search(
                        [('ad_client_id', '=', (str(record[14]).split('.'))[0])])
                    c_bpartner_id = (str(record[0]).split('.'))[0]

                    print
                    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK", record[3]
                    if c_bpartner_id not in portal_c_bpartner_id:
                        print
                        "jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj", record[4]

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
                            'company_id': company.id,
                            'isactive': True

                        }

                        self.env['transporter.customer'].create(vals_line)
                        print
                        "--------- Partner Created in CRM  ------"

                    if c_bpartner_id in portal_c_bpartner_id:
                        self.env['transporter.customer'].search([('bp_code', '=', record[3])]).write(
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
