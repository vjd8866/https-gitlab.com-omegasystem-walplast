

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT , DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta , date
import time
from io import BytesIO
import xlwt
import re
import base64

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class SalespersonJourneyReport(models.TransientModel):
    _name = 'salesperson.journey.report'
    _description = "Salesperson Journey Report"

    name = fields.Char(string="SalespersonJourneyReport")
    date_from = fields.Date(string="Date From", default=lambda self: fields.datetime.now())
    date_to = fields.Date(string="Date To", default=lambda self: fields.datetime.now())
    attachment_id = fields.Many2one( 'ir.attachment', string="Attachment", ondelete='cascade')
    datas = fields.Binary(string="XLS Report", related="attachment_id.datas")
    user_id = fields.Many2one( 'res.users', string="User", default=lambda self: self._uid)
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    export_file = fields.Char(string="Export")
    hierarchy_bool = fields.Boolean(string="Hierarchy")
    all_records = fields.Boolean(string="All Records")
    can_salessupport_edit = fields.Boolean(default=lambda self: self.env.user.has_group('sales_meet.group_sales_support_user'))

    @api.constrains('date_from','date_to')
    @api.depends('date_from','date_to')
    def date_range_check(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("Start Date should be before or be the same as End Date."))
        return True

    @api.onchange('all_records')
    def _onchange_date(self):
        if self.all_records:
            self.user_id = False
    

    def print_report(self):
        start = time.time()
        self.ensure_one()
        if self.date_from and self.date_to:

            rep_name = ""
            date_from = datetime.strptime(str(self.date_from), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
            date_to = datetime.strptime(str(self.date_to), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
            if self.date_from == self.date_to:
                rep_name = "Journey Details Report(%s)" % (date_from,)
            else:
                rep_name = "Journey Details Report(%s-%s)" % (date_from, date_to)
            self.name = rep_name

            workbook = xlwt.Workbook(encoding='utf-8')
            worksheet = workbook.add_sheet('Journey Details')
            fp = BytesIO()
            
            main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1, vert centre, horiz left; borders: bottom thick, top thick, left thick, right thick')
            sp_style = xlwt.easyxf('font: bold on, height 350;')
            header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz left; borders: bottom thin, top thin, left thin, right thin; \
                                        pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
            base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
            
            worksheet.write_merge(0, 1, 0, 4, self.name ,main_style)
            row_index = 2
            
            worksheet.col(0).width = 3000
            worksheet.col(1).width = 6000
            worksheet.col(2).width = 4000
            worksheet.col(3).width = 6000
            worksheet.col(4).width = 6000
            worksheet.col(5).width = 6000
            worksheet.col(6).width = 8000
            worksheet.col(7).width = 8000
            worksheet.col(8).width = 4000
            worksheet.col(9).width = 4000
            worksheet.col(10).width = 7000
            worksheet.col(11).width = 8000
            worksheet.col(12).width = 8000
          
            # Headers
            header_fields = ['Sr.No','Name','Date','Started At','Ended At','Duration (Hours)', 'User','Manager',
            'Activity Count','Visit Count','State', 'First Visit Time', 'Last Visit Time']
            row_index += 1

            for index, value in enumerate(header_fields):
                worksheet.write(row_index, index, value, header_style)
            row_index += 1

            sj = self.env['wp.salesperson.journey']

            journey_ids = self.env['wp.salesperson.journey'].sudo().search([('date','>=',self.date_from),('date','<=',self.date_to)])
            print("1111111111111")

            if self.hierarchy_bool:
                manager_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id),('active', '=', True)], limit=1).id
                if manager_id:
                    all_users = self.env['hr.employee'].sudo().hierarchy_employees(manager_id, self.user_id.id, employees=[])
                    journey_ids = sj.sudo().search([('date','>=',self.date_from),
                                                    ('date','<=',self.date_to),
                                                    ('user_id','in',all_users)])

            elif self.user_id:
                journey_ids = sj.sudo().search([('date','>=',self.date_from),
                                                ('date','<=',self.date_to),
                                                ('user_id','=',self.user_id.id)])
      
            if (not journey_ids):
                raise Warning(_('Record Not Found'))

            count = 0
            for ji in journey_ids:
                ended_at = started_at = duration_hrs = ''
                emp_id = self.env['hr.employee'].sudo().search([('user_id','=',ji.user_id.id), 
                    '|',('active','=',False),('active','=',True)], limit=1).read(['parent_id', 'state_id'])

                # print("aaaaaaaa", emp_id, emp_id[0]['parent_id'][1], emp_id[0]['state_id'][1])
                # print(erroror)

                # event_id = self.env['calendar.event'].sudo().search([('journey_id','=',ji.id)])
                # activity_count = len(self.env['calendar.event'].sudo().search([('journey_id','=',ji.id),('meeting_type','=','journey')]))
                # visit_count = len(self.env['calendar.event'].sudo().search([('journey_id','=',ji.id),('meeting_type','=','check-in')]))

                activity_count = self.env['calendar.event'].sudo().search_count([('journey_id','=',ji.id),('meeting_type','=','journey')])
                visit_count = self.env['calendar.event'].sudo().search_count([('journey_id','=',ji.id),('meeting_type','=','check-in')])

                first_meet = self.env['calendar.event'].sudo().search([('expense_date','=',ji.date),
                                                          ('user_id','=',ji.user_id.id),
                                                          ('meeting_type','=','check-in')], order="id asc", limit=1).start_date
                last_meet = self.env['calendar.event'].sudo().search([('expense_date','=',ji.date),
                                                          ('user_id','=',ji.user_id.id),
                                                          ('meeting_type','=','check-in')], order="id desc", limit=1).start_date

                # started_at_date = datetime.strptime(ji.started_at, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                # started_at = started_at_date.strftime(DATETIME_FORMAT)
                started_at = ji.started_at

                if ji.ended_at:

                    # ended_at_date = datetime.strptime(ji.ended_at, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    # ended_at = ended_at_date.strftime(DATETIME_FORMAT)
                    ended_at = ji.ended_at

                    delta = ji.ended_at- ji.started_at
                    duration_hrs = format((delta.total_seconds() / 3600.0), '.2f')

                count +=1
                worksheet.write(row_index, 0,count, base_style )
                worksheet.write(row_index, 1,ji.name  or '',  base_style )
                worksheet.write(row_index, 2,ji.date  or '',  base_style )
                worksheet.write(row_index, 3,started_at or '',  base_style )
                worksheet.write(row_index, 4,ended_at or '',  base_style )
                worksheet.write(row_index, 5,duration_hrs or '',  base_style )
                worksheet.write(row_index, 6,ji.user_id.name or '',  base_style )
                worksheet.write(row_index, 7,emp_id[0]['parent_id'][1] if emp_id[0]['parent_id'] else '',  base_style )
                worksheet.write(row_index, 8,activity_count or '',  base_style )
                worksheet.write(row_index, 9,visit_count or '',  base_style )
                worksheet.write(row_index, 10, emp_id[0]['state_id'][1] or '',  base_style )
                worksheet.write(row_index, 11,first_meet or '',  base_style )
                worksheet.write(row_index, 12,last_meet or '',  base_style )

                row_index += 1
                activity_count = visit_count = duration_hrs=  0

            row_index +=1
            workbook.save(fp)

            out = base64.encodestring(fp.getvalue())
            self.write({'state': 'get','report': out,'export_file':self.name+'.xls'})
            end = time.time()
            # print "------------- END Report -------", end-start
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'salesperson.journey.report',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
                'name' : 'Salesperson Journey Report',
            }

# import sys

# #set up psycopg2 environment
# import psycopg2

# #driving_distance module
# #note the lack of trailing semi-colon in the query string, as per the Postgres documentation
# query = """
#     select *
#     from driving_distance ($$
#         select
#             gid as id,
#             start_id::int4 as source,
#             end_id::int4 as target,
#             shape_leng::double precision as cost
#         from network
#         $$, %s, %s, %s, %s
#     )
# """

# #make connection between python and postgresql
# conn = psycopg2.connect("dbname = 'routing_template' user = 'postgres' host = 'localhost' password = 'xxxx'")
# cur = conn.cursor()

# outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)

# with open('resultsfile', 'w') as f:
#     cur.copy_expert(outputquery, f)

# conn.close()
