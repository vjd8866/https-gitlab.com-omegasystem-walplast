from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, Warning, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime, timedelta , date
import time
from dateutil import relativedelta
from io import BytesIO
import xlwt
import re
import base64

class meetings_details_report(models.TransientModel):
    _name = 'meetings.details.report'
    _description = "Meetings Details Report"


    name = fields.Char(string="MeetingsDetailsReport")
    date_from = fields.Date(string="Date From", default=lambda self: fields.datetime.now())
    date_to = fields.Date(string="Date To", default=lambda self: fields.datetime.now())
    attachment_id = fields.Many2one( 'ir.attachment', string="Attachment", ondelete='cascade')
    datas = fields.Binary(string="XLS Report", related="attachment_id.datas")
    user_id = fields.Many2one( 'res.users', string="User")
    user_ids = fields.Many2many('res.users', 'meetings_details_report_res_user_rel', string='Users')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    select_all = fields.Boolean("All User" , default=False )
    company_id = fields.Many2one('res.company', 'Company', 
        default=lambda self: self.env['res.company']._company_default_get('meetings.details.report'))

  
    @api.constrains('date_from','date_to')
    @api.depends('date_from','date_to')
    def date_range_check(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("Start Date should be before or be the same as End Date."))
        return True
    

    
    def print_report(self):
        self.ensure_one()
        status = ''
        if self.date_from and self.date_to:
            if not self.attachment_id:

                rep_name = "Meetings Details Report"
                date_from = datetime.strptime(str(self.date_from), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
                date_to = datetime.strptime(str(self.date_to), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
                if self.date_from == self.date_to:
                    rep_name = rep_name + "(%s)" % (date_from,)
                else:
                    rep_name = rep_name + "(%s-%s)" % (date_from, date_to)
                self.name = rep_name

                workbook = xlwt.Workbook(encoding='utf-8')
                worksheet = workbook.add_sheet(rep_name)
                fp = BytesIO()
                
                main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1; borders: bottom thick, top thick, left thick, right thick')
                sp_style = xlwt.easyxf('font: bold on, height 350;')
                header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz center; borders: bottom thin, top thin, left thin, right thin ; pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
                base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
                base_style_gray = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
                base_style_yellow = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; pattern: pattern fine_dots, fore_color white, back_color red;')
                
                worksheet.write_merge(0, 1, 0, 21, rep_name ,main_style)
                row_index = 2
                
                worksheet.col(0).width = 3000
                worksheet.col(1).width = 4000
                worksheet.col(2).width = 4000
                worksheet.col(3).width = 8000
                worksheet.col(4).width = 12000
                worksheet.col(5).width = 24000
                worksheet.col(6).width = 4000
                worksheet.col(7).width = 4000
                worksheet.col(8).width = 8000
                worksheet.col(9).width = 8000
                worksheet.col(10).width = 18000
                worksheet.col(11).width = 8000
                worksheet.col(12).width = 8000
                worksheet.col(13).width = 8000
                worksheet.col(14).width = 4000
                worksheet.col(15).width = 4000
                worksheet.col(16).width = 6000
                worksheet.col(17).width = 4000
                worksheet.col(18).width = 8000
                worksheet.col(19).width = 3000
                # worksheet.col(20).width = 3000

                
                # Headers
                header_fields = ['Sr.No','Date','Time','Responsible','Meeting Subject','Address','Distance(Km)','Duration','Lead','Customer','Description',
                'Dest Address','Stage','Latitude','Longitude','Next Date','State','Emp Code','Visit Type','Location type']
                row_index += 1
              
                for index, value in enumerate(header_fields):
                    worksheet.write(row_index, index, value, header_style)
                row_index += 1

                meeting_ids = self.env['calendar.event'].sudo().search([
                        ('start_date','>=',self.date_from),
                        ('start_date','<=',self.date_to),
                        ('meeting_type','=','check-in'),
                        ('company_id','=',self.company_id.id)
                        ,'|',('active','=',False),('active','=',True)])

                if self.user_id.has_group('sales_meet.group_sales_meet_srexecutive') == True:
                    if self.user_ids:
                        user_id = [user.id for user in self.user_ids]
                        # meeting_ids = meeting_ids.sudo().search([('user_id','in',user_id)])
                        meeting_ids = self.env['calendar.event'].sudo().search([
                                            ('start_date','>=',self.date_from),
                                            ('start_date','<=',self.date_to),
                                            ('meeting_type','=','check-in'),
                                            ('company_id','=',self.company_id.id),
                                            ('user_id','in',user_id)
                                            ,'|',('active','=',False),('active','=',True)])

                    elif self.select_all:
                        meeting_ids = meeting_ids
                    else:
                        meeting_ids = self.env['calendar.event'].sudo().search([
                                            ('start_date','>=',self.date_from),
                                            ('start_date','<=',self.date_to),
                                            ('meeting_type','=','check-in'),
                                            ('company_id','=',self.company_id.id),
                                            ('user_id','=',self.env.uid)
                                            ,'|',('active','=',False),('active','=',True)])
                        # meeting_ids = meeting_ids.sudo().search([('user_id','=',self.env.uid)])

                else:
                    # meeting_ids = meeting_ids.sudo().search([('user_id','=',self.env.uid)])
                    meeting_ids = self.env['calendar.event'].sudo().search([
                                            ('start_date','>=',self.date_from),
                                            ('start_date','<=',self.date_to),
                                            ('meeting_type','=','check-in'),
                                            ('company_id','=',self.company_id.id),
                                            ('user_id','=',self.env.uid)
                                            ,'|',('active','=',False),('active','=',True)])

                
                if (not meeting_ids):
                    raise Warning(_('Record Not Found'))

                count = 0
                for meeting_id in meeting_ids:
                    if meeting_id:

                        if meeting_id.ishome or meeting_id.name:
                            status = 'complete'
                        else:
                            status = 'pending'

                        if str(meeting_id.id) == meeting_id.mobile_id:
                            date_starttime = datetime.strptime(str(meeting_id.start_date), tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                            date_start_date = date_starttime.strftime('%d-%m-%Y')
                            date_start_time = date_starttime.strftime('%H:%M:%S')

                        else:

                            date_starttime = datetime.strptime(str(meeting_id.start_date), tools.DEFAULT_SERVER_DATETIME_FORMAT)
                            date_start_date = date_starttime.strftime('%d-%m-%Y')
                            date_start_time = date_starttime.strftime('%H:%M:%S')

                        employee_ids = self.env['hr.employee'].sudo().search([('user_id','=',meeting_id.user_id.id),
                            '|',('active','=',False),('active','=',True)], limit=1)


                        count +=1
                        worksheet.write(row_index, 0,count, base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 1,date_start_date,  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 2,date_start_time,  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 3,meeting_id.user_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 4,meeting_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 5,meeting_id.reverse_location or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 6,meeting_id.distance or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 7,meeting_id.duration or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 8,meeting_id.lead_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 9,meeting_id.partner_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 10,meeting_id.description or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 11,meeting_id.destination or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 12,meeting_id.stage_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        # worksheet.write(row_index, 13,meeting_id.categ_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 13,meeting_id.checkin_lattitude or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 14,meeting_id.checkin_longitude or '',  base_style if status=='complete' else base_style_yellow)
                        # worksheet.write(row_index, 16,meeting_id.next_activity_id.name or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 15,meeting_id.date_action or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 16,employee_ids.state_id.name or employee_ids.work_state or '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 17,employee_ids.emp_id or  '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 18,meeting_id.visit_type or  '',  base_style if status=='complete' else base_style_yellow)
                        worksheet.write(row_index, 19,meeting_id.location_type or  '',  base_style if status=='complete' else base_style_yellow)

                        row_index += 1

                row_index +=1
                workbook.save(fp)


            out = base64.encodestring(fp.getvalue())
            self.write({'state': 'get','report': out,'name':rep_name + '.xls'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'meetings.details.report',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
            }