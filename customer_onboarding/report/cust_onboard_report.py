from odoo import models, fields, api,_,tools
from datetime import datetime, timedelta, date
from io import BytesIO
import xlwt
import base64
from odoo.exceptions import UserError , Warning, ValidationError

DATETIME_FORMAT = "%Y-%m-%d"

class CustObReport(models.TransientModel):
    _name = 'cust.ob.report'

    xls_file =fields.Binary("XLS File", readonly=True)
    filename=fields.Char("Customer On-Boarding Report")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')
    from_date = fields.Date("From",default=fields.Date.context_today)
    to_date = fields.Date("To",default=fields.Date.context_today)

    
    def export_cust_ob(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Customer On-Boarding')
        fp = BytesIO()

        main_style = xlwt.easyxf(
            'font: bold on, height 400; align: wrap 1, vert centre, horiz center; borders: bottom thick, top thick, left thick, right thick')
        header_style = xlwt.easyxf(
            'font: bold on, height 220; align: wrap 1,  horiz center; borders: bottom thin, top thin, left thin, right thin')
        base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
        highlight_style = xlwt.easyxf(
            'align: wrap 1; borders: bottom thin, top thin, left thin, right thin;pattern: pattern fine_dots, fore_color white, back_color yellow;')

        worksheet.write_merge(0, 1, 0, 10, 'Customer On-Boarding Report', main_style)

        row_index = 3

        worksheet.col(0).width = 8000
        worksheet.col(1).width = 8000
        worksheet.col(2).width = 8000
        worksheet.col(3).width = 8000
        worksheet.col(4).width = 8000
        worksheet.col(5).width = 8000
        worksheet.col(6).width = 8000
        worksheet.col(7).width = 8000
        worksheet.col(8).width = 8000
        worksheet.col(9).width = 8000
        worksheet.col(10).width = 8000
        worksheet.col(11).width = 8000
        worksheet.col(11).height = 8000
        worksheet.col(12).width = 8000
        worksheet.col(13).width = 8000
        worksheet.col(14).width = 8000
        worksheet.col(15).width = 8000
        worksheet.col(16).width = 8000
        worksheet.col(17).width = 8000
        worksheet.col(18).width = 8000
        worksheet.col(19).width = 8000
        worksheet.col(20).width = 8000
        worksheet.col(21).width = 8000
        worksheet.col(22).width = 8000
        worksheet.col(23).width = 8000
        worksheet.col(24).width = 8000
        worksheet.col(25).width = 8000
        worksheet.col(26).width = 8000
        worksheet.col(27).width = 8000
        worksheet.col(28).width = 8000
        worksheet.col(29).width = 8000
        worksheet.col(30).width = 8000
        worksheet.col(31).width = 8000
        worksheet.col(32).width = 8000
        worksheet.col(33).width = 8000
        worksheet.col(34).width = 8000
        worksheet.col(35).width = 8000
        worksheet.col(36).width = 8000

        # Headers
        header_fields = ['Name','Email','Company','Designation','Contact Person Name','Contact NO.','Date','Street1','Street2','District',
                         'City','State','Country','Zip Code','Costing Submission','FG Sample Submission','Customer Code Creation','Vendor Code Creation',
                         'Virtual Depot Agreement','Physical Depot Agreement','Sales Purchase Agreement','Artwork Preparation by Drychem',
                         'Packing Bag Development','Artwork & Specification Submission by customer','Master Sample Submission to QC','Blackbox Supply by Customer'
                         ,'FG Specification - Customer Product','MRP','Batch Slip Submission to Plant','IJP Approval','FG Code Creation in ERP','Monthly Forecast',
                         'SOP Submission','Premix Availability by Drychem as per Plan','Landed Price Submission to Customer','Purchase Order from Customer','Final Status']
        row_index += 1

        for index, value in enumerate(header_fields):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        domain = []
        if self.from_date and self.to_date:
            domain.append(('date', '>=', self.from_date))
            domain.append(('date', '<=', self.to_date))


        cust_onboardings = self.env['cust.onboard'].sudo().search(domain)

        if (not cust_onboardings):
            raise ValidationError("Record Not Founds")

        if cust_onboardings:
            for rec in cust_onboardings:
                date = datetime.strptime(str(rec.date), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d')

                worksheet.write(row_index, 0, rec.name or "-",header_style if not rec.name else base_style)
                worksheet.write(row_index, 1, rec.email or "-",header_style if not rec.email else base_style)
                worksheet.write(row_index, 2, rec.company_id.name or "-",header_style if not rec.company_id else base_style)
                worksheet.write(row_index, 3, rec.contact_name or "-",header_style if not rec.contact_name else base_style)
                worksheet.write(row_index, 4, rec.designation or "-",header_style if not rec.designation else base_style)
                worksheet.write(row_index, 5, rec.contact_no or "-",header_style if not rec.contact_no else base_style)
                worksheet.write(row_index, 6, date or "-",header_style if not date else base_style)
                worksheet.write(row_index, 7, rec.street1 or "-",header_style if not rec.street1 else base_style)
                worksheet.write(row_index, 8, rec.street2 or "-",header_style if not rec.street2 else base_style)
                worksheet.write(row_index, 9, rec.district_id.name or "-",header_style if not rec.district_id else base_style)
                worksheet.write(row_index, 10, rec.city or "-",header_style if not rec.city else base_style)
                worksheet.write(row_index, 11, rec.state_id.name or "-",header_style if not rec.state_id else base_style)
                worksheet.write(row_index, 12, rec.country_id.name or "-",header_style if not rec.country_id else base_style)
                worksheet.write(row_index, 13, rec.zip_code or "-",header_style if not rec.zip_code else base_style)
                worksheet.write(row_index, 14, rec.costing_sub or "-",header_style if not rec.costing_sub else base_style)
                worksheet.write(row_index, 15, rec.fg_sample_sub or "-",header_style if not rec.fg_sample_sub else base_style)
                worksheet.write(row_index, 16, rec.cust_code_gen or "-",header_style if not rec.cust_code_gen else base_style)
                worksheet.write(row_index, 17, rec.vend_code_gen or "-",header_style if not rec.vend_code_gen else base_style)
                worksheet.write(row_index, 18, rec.virt_dep_aggreement or "-",header_style if not rec.virt_dep_aggreement else base_style)
                worksheet.write(row_index, 19, rec.physic_depo_agreement or "-",header_style if not rec.physic_depo_agreement else base_style)
                worksheet.write(row_index, 20, rec.sale_purchase_agreement or "-",header_style if not rec.sale_purchase_agreement else base_style)
                worksheet.write(row_index, 21, rec.artw_prep or "-",header_style if not rec.artw_prep else base_style)
                worksheet.write(row_index, 22, rec.pack_bag_dev or "-",header_style if not rec.pack_bag_dev else base_style)
                worksheet.write(row_index, 23, rec.art_spec_sub or "-",header_style if not rec.art_spec_sub else base_style)
                worksheet.write(row_index, 24, rec.mast_sample_sub or "-",header_style if not rec.mast_sample_sub else base_style)
                worksheet.write(row_index, 25, rec.bb_supply or "-",header_style if not rec.bb_supply else base_style)
                worksheet.write(row_index, 26, rec.fg_spec or "-",header_style if not rec.fg_spec else base_style)
                worksheet.write(row_index, 27, rec.mrp or "-",header_style if not rec.mrp else base_style)
                worksheet.write(row_index, 28, rec.batch_slip_sub or "-",header_style if not rec.batch_slip_sub else base_style)
                worksheet.write(row_index, 29, rec.ijp_approval or "-",header_style if not rec.ijp_approval else base_style)
                worksheet.write(row_index, 30, rec.fg_code_create or "-",header_style if not rec.fg_code_create else base_style)
                worksheet.write(row_index, 31, rec.monthly_forecast or "-",header_style if not rec.monthly_forecast else base_style)
                worksheet.write(row_index, 32, rec.sop_sub or "-",header_style if not rec.sop_sub else base_style)
                worksheet.write(row_index, 33, rec.prem_available or "-",header_style if not rec.prem_available else base_style)
                worksheet.write(row_index, 34, rec.landed_price_sub or "-",header_style if not rec.landed_price_sub else base_style)
                worksheet.write(row_index, 35, rec.po_cust or "-",header_style if not rec.po_cust else base_style)
                worksheet.write(row_index, 36, rec.final_status or "-",header_style if not rec.final_status else base_style)

                row_index += 1
        workbook.save(fp)

        out = base64.encodestring(fp.getvalue())
        self.write(
            # {'state': 'get', 'report': out, 'name': 'QR Code Details (' + self.date_from + ' / ' + self.date_to + ').xls'})
            {'state': 'get', 'xls_file': out, 'filename': 'Customer On-boarding Report.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cust.ob.report',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }