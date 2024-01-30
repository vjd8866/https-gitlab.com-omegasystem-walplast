

import calendar
from io import BytesIO
from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime, timedelta , date
import time
from io import BytesIO
import xlwt
import re
import base64

class salesperson_nojourney_report(models.TransientModel):
    _name = "salesperson.nojourney.report"
    
    start_date = fields.Date(string='Start Date', required=True, default=datetime.today())
    end_date = fields.Date(string="End Date")
    user_id = fields.Many2one('res.users', string='Salesperson')
    nojourney_data = fields.Char('Name', size=256)
    file_name = fields.Binary('No Journey Report', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    _sql_constraints = [
            ('check','CHECK((start_date <= end_date))',"End date must be greater then start date")  
    ]


    def action_nojourney_report(self):
        self.ensure_one()
        fp = BytesIO()
        self.env.cr.execute(""" select ru.id, 
            (select name from res_partner where id = (select partner_id from res_users where id = ru.id )) as "Salesperson",
            hr.work_location, (select name from res_country_state where id = hr.state_id) as "State",
            (select name from hr_employee hrm where hrm.id = hr.parent_id) as "Manager",
            hr.mobile_phone, hr.work_email as "Work Mail", hr.emp_id, hr.state_id, ru.active, hr.status
            from res_users ru 
            JOIN resource_resource rr ON rr.user_id = ru.id
            JOIN hr_employee hr ON hr.resource_id = rr.id
            where ru.wp_user_type_id in (select id from wp_res_users_type where name in ('Salesperson','Salesmanager')) and 
            hr.status <> 'left'  and hr.category_ids_many2one = 3 and
            ru.id not in (select user_id from wp_salesperson_journey sj 
            where date = '%s' and user_id is not null)""" % (self.start_date))
        res1 = self.env.cr.fetchall()

        if (not res1):
            raise Warning(_('Record Not Found'))
        
        rep_name = 'No Journey Details Report'
        second_heading = approval_status = ''
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet(rep_name)
        
        main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1, vert centre, horiz left; \
        borders: bottom thick, top thick, left thick, right thick')
        sp_style = xlwt.easyxf('font: bold on, height 350;')
        header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz center, vertical center; \
            borders: bottom thin, top thin, left thin, right thin; \
            pattern: pattern fine_dots, fore_color white, back_color gray_ega;' )
        base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')

        start_date = datetime.strptime(str(self.start_date), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
        rep_name = rep_name + "(%s)" % (start_date)
        # end_date = datetime.strptime(str(self.end_date), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
        # if self.start_date == self.end_date:
        #     rep_name = rep_name + "(%s)" % (start_date)
        # else:
        #     rep_name = rep_name + "(%s|%s)"  % (start_date, end_date)

        worksheet.write_merge(0, 1, 0, 7, rep_name ,main_style)
        row_index = 2
        
        worksheet.col(0).width = 2000
        worksheet.col(1).width = 12000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 12000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 12000
        worksheet.col(7).width = 4000
        
        header_fields = ['S.No','Employee','Work Location','State','Manager', 'Mobile','Work Mail','Emp ID']
        row_index += 1
     
        for index, value in enumerate(header_fields):
            worksheet.write(row_index, index, value, header_style)
        row_index += 1

        count = 0
        for res in res1:

            count +=1
            worksheet.write(row_index, 0,count, base_style )
            worksheet.write(row_index, 1,res[1] or '',  base_style )
            worksheet.write(row_index, 2,res[2] or '',  base_style )
            worksheet.write(row_index, 3,res[3] or '',  base_style )
            worksheet.write(row_index, 4,res[4] or '',  base_style )
            worksheet.write(row_index, 5,res[5] or '',  base_style )
            worksheet.write(row_index, 6,res[6] or '',  base_style )
            worksheet.write(row_index, 7,res[7] or '',  base_style )

            row_index += 1

        row_index +=1
        workbook.save(fp)
        out = base64.encodestring(fp.getvalue())

        self.write({'state': 'get','file_name': out,'nojourney_data':rep_name +'.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'salesperson.nojourney.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
        }