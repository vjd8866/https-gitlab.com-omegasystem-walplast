from odoo import models, fields, api,_,tools
from datetime import datetime, timedelta, date
from io import StringIO
import xlwt
import base64
from odoo.exceptions import UserError , Warning, ValidationError

DATETIME_FORMAT = "%Y-%m-%d"

class TprPlan(models.TransientModel):
    _name = 'tpr.plan.report'

    xls_file =fields.Binary("XLS File", readonly=True)
    filename=fields.Char("TPR Plan")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')
    from_date = fields.Date("From",default=fields.Date.context_today)
    to_date = fields.Date("To",default=fields.Date.context_today)
    plant = fields.Many2many('wp.plant',string="Plant")


    def export_tpr_plan(self):
        if self.env.user.sudo().has_group('transporter_management.transporter_user_group') and not self.plant:
            raise ValidationError("Please select atleast one plant !!!")

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('TPR Plan')
        fp = StringIO()

        main_style = xlwt.easyxf(
            'font: bold on, height 400; align: wrap 1, vert centre, horiz center; borders: bottom thick, top thick, left thick, right thick')
        header_style = xlwt.easyxf(
            'font: bold on, height 220; align: wrap 1,  horiz center; borders: bottom thin, top thin, left thin, right thin')
        base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
        highlight_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin;pattern: pattern fine_dots, fore_color white, back_color yellow;')

        worksheet.write_merge(0, 1, 0, 5, 'Transporter Plan Report', main_style)

        row_index = 4

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
        worksheet.col(11).width = 10000
        worksheet.col(11).height = 2000
        worksheet.col(12).width = 8000
        worksheet.col(13).width = 8000
        worksheet.col(14).width = 8000
        worksheet.col(15).width = 8000
        worksheet.col(16).width = 10000

        # Headers
        header_fields = ['Order Type', 'Truck Order ID', 'Plant', 'Sending Location', 'Sr. No.', 'Date', 'Depot Code',
                         'Depot Desc', 'Transporter','Type','Status','Updated Remarks','Remarks','PRODUCT CODE','SKU CODE','Volume','Order Time',
                         'Truck Reporting Time','Reason For Default']

        for index, value in enumerate(header_fields):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        domain=[]
        if self.from_date and self.to_date:
            domain.append(('date','>=',self.from_date))
            domain.append(('date','<=',self.to_date))
        if self.plant:
            plants = [plant.id for plant in self.plant]
            domain.append(('plant.id','in',plants))

        tpr_plans = self.env['transporter.management'].sudo().search(domain)

        if (not tpr_plans):
            raise ValidationError("Record Not Founds")

        if tpr_plans:
            for plan in tpr_plans:
                date = datetime.strptime(plan.date, tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d')

                if plan.order_type == 'Repeat':
                    worksheet.write(row_index, 0, plan.order_type,highlight_style)
                else:
                    worksheet.write(row_index, 0, plan.order_type or "-",header_style if not plan.order_type else base_style)
                worksheet.write(row_index, 1,plan.truck_order_id or "-", header_style if not plan.truck_order_id else base_style)
                worksheet.write(row_index, 2,plan.plant.name or "-", header_style if not plan.plant else base_style)
                worksheet.write(row_index, 3,plan.sending_location or "-", header_style if not plan.sending_location else base_style)
                worksheet.write(row_index, 4,plan.name or "-", header_style if not plan.name else base_style)
                worksheet.write(row_index, 5,str(date) or "-", header_style if not plan.date else base_style)
                worksheet.write(row_index, 6,plan.depot_code.bp_code[3:] or "-", header_style if not plan.date else base_style)
                worksheet.write(row_index, 7,plan.depot_code.name or "-", header_style if not plan.depot_code else base_style)
                worksheet.write(row_index, 8,plan.transporter.name or "-", header_style if not plan.transporter else base_style)
                worksheet.write(row_index, 9,plan.type.name or "-", header_style if not plan.type else base_style)
                worksheet.write(row_index, 10,plan.status or "-", header_style if not plan.status else base_style)
                worksheet.write(row_index, 11,plan.remarks or "-", header_style if not plan.remarks else base_style)
                worksheet.write(row_index, 12,plan.remarks_2 or "-", header_style if not plan.remarks_2 else base_style)

                worksheet.write(row_index, 16, plan.order_time.name or "-", header_style if not plan.order_time else base_style)
                worksheet.write(row_index, 17, plan.truck_reporting_time.name or "-", header_style if not plan.truck_reporting_time else base_style)
                worksheet.write(row_index, 18, plan.reason or "-", header_style if not plan.reason else base_style)

                counter = 0
                for product in plan.products_transport_rel:
                    if counter >0 :
                        worksheet.write(row_index, 0, "-", header_style)
                        worksheet.write(row_index, 1, "-", header_style)
                        worksheet.write(row_index, 2, "-", header_style)
                        worksheet.write(row_index, 3, "-", header_style)
                        worksheet.write(row_index, 4, "-", header_style)
                        worksheet.write(row_index, 5, str(date) or "-", header_style if not plan.date else base_style)
                        worksheet.write(row_index, 6, "-", header_style)
                        worksheet.write(row_index, 7, "-", header_style)
                        worksheet.write(row_index, 8, "-", header_style)
                        worksheet.write(row_index, 9, "-", header_style)
                        worksheet.write(row_index, 10, "-", header_style)
                        worksheet.write(row_index, 11, "-", header_style)
                        worksheet.write(row_index, 12, "-", header_style)

                        worksheet.write(row_index, 15, "-", header_style)
                        worksheet.write(row_index, 16, "-", header_style)
                        worksheet.write(row_index, 17, "-", header_style)
                        worksheet.write(row_index, 18, "-", header_style)

                    worksheet.write(row_index, 13, product.product_id.name or "-", header_style if not product.product_id else base_style)
                    worksheet.write(row_index, 14, product.product_id.uom_id.name or "-", header_style if not product.product_id.uom_id else base_style)
                    worksheet.write(row_index, 15, product.volume or "-", header_style if not product.volume else base_style)
                    counter += 1
                    row_index += 1
                if not plan.products_transport_rel:
                    row_index += 1



        row_index += 1
        workbook.save(fp)

        out = base64.encodestring(fp.getvalue())
        self.write(
            # {'state': 'get', 'report': out, 'name': 'QR Code Details (' + self.date_from + ' / ' + self.date_to + ').xls'})
            {'state': 'get', 'xls_file':out,'filename': 'TPR Report.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tpr.plan.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
        }