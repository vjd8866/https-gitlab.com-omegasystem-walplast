import string
from datetime import datetime, timedelta, date, time
from odoo import api, fields, models, _, registry, tools, SUPERUSER_ID
from odoo.exceptions import UserError, Warning, ValidationError
import time
import psycopg2


class UpdateImportProducts(models.Model):
    _name = 'import.erp.product'

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    def update_import_products_from_erp(self):
        conn_pg = None
        config_id = self.env['external.db.configuration'].sudo().search([('state', '=', 'connected')], limit=1)
        if config_id:

            print("#-------------Select --TRY----------------------#")
            try:
                conn_pg = psycopg2.connect(dbname=config_id.database_name, user=config_id.username,
                                           password=config_id.password, host=config_id.ip_address, port=config_id.port)
                pg_cursor = conn_pg.cursor()

                query = " select m_product_id,mp.value,mp.name,sku,m_product_category_id, \
                        (select name from adempiere.M_Product_Category where M_Product_Category_ID= mp.m_product_category_id), \
                            producttype,c_uom_to_id,(select name from adempiere.C_UOM where  C_UOM_ID= mp.c_uom_to_id), \
                            hsn_code,IsWebStoreFeatured,u_productcategory_id,bp.name2,bp.c_bpartner_id,mp.ad_client_id\
                            from adempiere.m_product mp JOIN adempiere.c_bpartner bp ON bp.c_bpartner_id=(select c_bpartner_id from C_BPartner_Product pbp where pbp.M_Product_ID=mp.m_product_id limit 1)  \
                        where mp.IsActive = 'Y'"

                # query = "select m_product_id,mp.value,mp.name,sku,m_product_category_id, (select name from adempiere.M_Product_Category where M_Product_Category_ID= mp.m_product_category_id), \
                #         producttype,c_uom_to_id,(select name from adempiere.C_UOM where  C_UOM_ID= mp.c_uom_to_id), hsn_code,IsWebStoreFeatured,u_productcategory_id,bp.name,bp.c_bpartner_id,bp.value  \
                #         from adempiere.m_product mp JOIN adempiere.c_bpartner bp ON bp.c_bpartner_id=(select c_bpartner_id  \
                #         from C_BPartner_Product pbp where pbp.M_Product_ID=mp.m_product_id)  \
                #         where bp.value like 'Asian' and mp.value like 'FG%' and mp.IsActive = 'Y' and mp.sku is not null and  mp.ad_client_id='1000001'"

                # query = "select m_product_id,mp.value,mp.name,sku,m_product_category_id, (select name from adempiere.M_Product_Category where M_Product_Category_ID= mp.m_product_category_id), \
                #                         producttype,c_uom_to_id,(select name from adempiere.C_UOM where  C_UOM_ID= mp.c_uom_to_id), hsn_code,IsWebStoreFeatured,u_productcategory_id,bp.name,bp.c_bpartner_id,bp.value  \
                #                         from adempiere.m_product mp JOIN adempiere.c_bpartner bp ON bp.c_bpartner_id=(select c_bpartner_id  \
                #                         from C_BPartner_Product pbp where pbp.M_Product_ID=mp.m_product_id)  \
                #                         where mp.IsActive = 'Y' and mp.sku is not null"

                pg_cursor.execute(query)
                records = pg_cursor.fetchall()

                portal_product_list = [x.m_product_id for x in
                                       self.env['product.product'].search([('m_product_id', '!=', False)])]
                for record in records:
                    m_product_id = (str(record[0]).split('.'))[0]
                    c_bpartner_id = (str(record[13]).split('.'))[0]
                    portal_product = self.env['product.product'].sudo().search([('m_product_id', '=', m_product_id)],
                                                                               limit=1)
                    bp = self.env['transporter.customer'].sudo().search(
                        [('c_bpartner_id', '=', c_bpartner_id), ('isactive', '=', True)], limit=1)
                    company = self.env['res.company'].sudo().search(
                        [('ad_client_id', '=', (str(record[14]).split('.'))[0])])

                    if m_product_id not in portal_product_list and record[8]:
                        c_uom_id = self.env['uom.uom'].sudo().search(
                            [('c_uom_id', '=', (str(record[7] or '').split('.'))[0]), ('c_uom_id', '!=', False)])
                        if not c_uom_id:
                            c_uom_id = self.env['uom.uom'].sudo().create({
                                'name': record[8],
                                'category_id': 2,
                                'uom_type': 'reference',
                                'rounding': 0.01000,
                                'c_uom_id': (str(record[7] or '').split('.'))[0]
                            })
                        vals_line = {
                            'm_product_id': m_product_id,
                            'active': True,
                            'value': record[1],
                            'default_code': record[1],
                            'name': record[2],
                            'sku': record[3],
                            'uom_id': c_uom_id.id,
                            'uom_po_id': c_uom_id.id,
                            'hsn_code': record[9],
                            'IsWebStoreFeatured': True if 'Y' in record[10] else False,
                            'u_productcategory_id': record[11],
                            'company_id': company.id,
                            'bp_name': bp.id if bp else False,
                        }

                        product = self.env['product.product'].sudo().create(vals_line)
                        print("----------- Product value: ", record[1], "   -----------------------------")
                        print("----------- Product", product.id, " Created in CRM  -----------------------------")
                    else:
                        portal_product.write(
                            {'IsWebStoreFeatured': True if 'Y' in record[10] else False,
                             'bp_name': bp.id if bp else False})
                        print("----------- Product", portal_product.name, " Updated  -----------------------------")


            except psycopg2.DatabaseError as e:
                if conn_pg: conn_pg.rollback()
                print('#----------------Error %s' % e)

            finally:
                if conn_pg: conn_pg.close()
                print("#--------------Select ----Finally----------------------#")