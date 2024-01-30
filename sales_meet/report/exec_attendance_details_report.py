

from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime, timedelta , date
import time
from io import BytesIO
import xlwt
import re
import base64
import pytz
import calendar
import json
import odoo.http as http
from odoo.http import request
from odoo.addons.web.controllers.main import ExcelExport
import dateutil.parser

from odoo import models, fields, api, _ , tools
from odoo.exceptions import UserError , Warning, ValidationError


format_date = '%Y-%m-%d'

class exec_attendance_details_report(models.TransientModel):
    _name = 'exec.attendance.details.report'
    _description = "Exec Attendance Details Report"


    name = fields.Char(string="ExecAttendanceDetailsReport")
    date_from = fields.Date(string='Start Date', required=True, default=datetime.today())
    date_to = fields.Date(string="End Date", required=True, default=datetime.today())

    attachment_id = fields.Many2one( 'ir.attachment', string="Attachment", ondelete='cascade')
    datas = fields.Binary(string="XLS Report", related="attachment_id.datas")
    user_id = fields.Many2one( 'res.users', string="User")
    user_ids = fields.Many2many('res.users', 'exec_attendance_details_report_res_user_rel', string='Users')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    select_all = fields.Boolean("All User" , default=False )
    hierarchy_bool = fields.Boolean(string="Hierarchy")
    all_records = fields.Boolean(string="All Records")
    company_id = fields.Many2one('res.company', 'Company', 
        default=lambda self: self.env['res.company']._company_default_get('exec.attendance.details.report'))

  
    @api.constrains('date_from','date_to')
    @api.depends('date_from','date_to')
    def date_range_check(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("Start Date should be before or be the same as End Date."))
        return True



    def print_report(self):
        start = time.time()
        print("----------Start ----------------", start)
        self.ensure_one()
        domain = []
        intervals = []
        status = ''
        if not self.attachment_id:
            rep_name = "Exec Attendance Details Report"
            date_from = datetime.strptime(str(self.date_from), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
            date_to = datetime.strptime(str(self.date_to), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
            if self.date_from == self.date_to:
                rep_name = "Exec Attendance Details Report(%s)" % (date_from,)
            else:
                rep_name = "Exec Attendance Details Report(%s|%s)" % (date_from, date_to)
            self.name = rep_name + '.xls'

            workbook = xlwt.Workbook(encoding='utf-8')
            worksheet = workbook.add_sheet('Attendance Details', cell_overwrite_ok=True)
            fp = BytesIO()

            main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1; borders: bottom thick, top thick, left thick, right thick; pattern: pattern fine_dots, fore_color white, back_color light_green;')
            sp_style = xlwt.easyxf('font: bold on, height 350;')
            header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz center; borders: bottom thin, top thin, left thin, right thin ; pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
            base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
            base_style_gray = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
            base_style_yellow = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; pattern: pattern fine_dots, fore_color white, back_color yellow;')
            base_style_green = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; pattern: pattern fine_dots, fore_color white, back_color green;')
            base_style_orange = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; pattern: pattern fine_dots, fore_color white, back_color orange;')

            date_from = dateutil.parser.parse(str(self.date_from)).date()
            date_to = dateutil.parser.parse(str(self.date_to)).date()
            day_date_from = int(date_from.strftime('%d'))
            day_date_to = int(date_to.strftime('%d'))

            delta = date_to - date_from
            delta_days = int(delta.days)

            if date_to.month != date_from.month:
                raise ValidationError(_("The entered Date interval has 2 different months. Kindly use the date interval between Same month."))


            if delta_days >= 8:
                raise ValidationError(_("Date Interval cannot be more than 7 days"))

            total_days = delta_days + 1
           
            worksheet.write_merge(0, 1, 0, total_days, rep_name ,main_style)
            row_index = 2

            column_index = 1
            month_days = total_days

            # print("aaaaaaaaaaaaaaaaaaaaaaaaaaaa", delta, delta_days, total_days, date_from, date_to, day_date_from,day_date_to, )

            worksheet.col(0).width = 3000
            worksheet.col(1).width = 8000
            for tt in range(2,month_days):
                worksheet.col(tt).width  = 2000
            worksheet.col(month_days+1).width  = 3000
            worksheet.col(month_days+2).width  = 4000
            worksheet.col(month_days+3).width  = 4000
            worksheet.col(month_days+4).width  = 4000

            # Headers
            a = ['Emp. No.','Employee Name']
            b = range(day_date_from,day_date_to + 1)
            c = ['Total Visits', 'App Used Days', 'Avg Visit','Avg Working Hours']
            header_fields = a+b+c
            row_index += 1

            for index, value in enumerate(header_fields):
                worksheet.write(row_index, index, value, header_style)
            row_index += 1

            
            user_type = [x.id for x in self.env['wp.res.users.type'].sudo().search([('name','in',('Salesmanager','Salesperson'))])]

            for days in range(total_days):
      
                intervals.append(date_from)
                date_from += timedelta(days=1)

            if self.user_ids:
                user_id = [user.id for user in self.user_ids]

                user_ids = [ x.id for x in self.env['res.users'].sudo().search([('id','in',user_id),
                                                                ('active','=',True),
                                                                ('company_id','=',self.company_id.id),
                                                                ('wp_user_type_id','in',user_type)]) ]

            else:


                user_ids = [x.id for x in self.env['res.users'].search([('active','=',True),
                                                         ('company_id','=',self.company_id.id),
                                                         ('wp_user_type_id','in',user_type)]) ]

            for user_id in user_ids:
                present = full_day = half_day = attendance_status = ''
                present_bool = False
                total_visits = present_days = avg_visit = duration = 0

                emp_id = self.env['hr.employee'].sudo().search([
                            ('user_id','=',user_id),
                            '|',('active','=',False),('active','=',True)], limit=1)

                print("11111111111111111", emp_id.name)
                count_day = 1
                for rec in intervals:
                    calendar_ids = [y.id for y in self.env['calendar.event'].sudo().search([
                                        ('expense_date','=',rec),
                                        ('user_id','=',user_id),
                                        ('company_id','=',self.company_id.id),
                                        ('meeting_type','=','check-in')]) ]

                    len_visits = len(calendar_ids)

                    journey_duration = self.env['wp.salesperson.journey'].sudo().search([('user_id','=',user_id),
                                                                                    ('date','=',rec)], limit=1).duration
                    if journey_duration:
                        duration += journey_duration

                    if calendar_ids:
                        present_days += 1

                    total_visits += len_visits

                    if total_visits and present_days:
                        avg_visit = float(total_visits/present_days)

                    worksheet.write(row_index, 0, emp_id.emp_id, base_style)
                    worksheet.write(row_index, 1, emp_id.name,  base_style)
                    worksheet.write(row_index, column_index + count_day , len_visits or 0,  base_style )
                    worksheet.write(row_index, total_days + 2 , total_visits or '',  base_style_gray)
                    worksheet.write(row_index, total_days + 3 , present_days or '',  base_style_gray)
                    worksheet.write(row_index, total_days + 4 , avg_visit or '',  base_style_gray)
                    worksheet.write(row_index, total_days + 5 , duration or '',  base_style_gray)

                    count_day += 1

                row_index += 1

            row_index +=1
            workbook.save(fp)


            out = base64.encodestring(fp.getvalue())
            self.write({'state': 'get','report': out,'name':rep_name + '.xls'})
            end = time.time()
            # print "------------- END Attendance Report -------", end-start

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'exec.attendance.details.report',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
            }
