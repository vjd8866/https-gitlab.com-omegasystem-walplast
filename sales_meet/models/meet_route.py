

from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT , DEFAULT_SERVER_DATETIME_FORMAT
from odoo import tools, api, SUPERUSER_ID, fields, models, _
from time import gmtime, strftime
from odoo.exceptions import UserError , ValidationError

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class WpSalespersonJourney(models.Model):
    _name = "wp.salesperson.journey"
    _inherit = 'mail.thread'
    _description= "Salesperson Journey"
    _order = 'id desc'

    @api.depends('started_at', 'ended_at')
    def _compute_duration(self):
        for rec in self:
            if rec.ended_at:
                delta = rec.ended_at - rec.started_at
                rec.duration = float(delta.total_seconds() / 3600.0)
                # print "vvvvvvvvvvvvvvvvvvvv_compute_duration vvvvvvvvvvvvvvvvvvvvvvvvv" , rec.duration

    name = fields.Char('Sequence No' )
    user_id = fields.Many2one('res.users', string='User', index=True)
    date = fields.Date('Date', default=lambda self: fields.datetime.today())
    started_at = fields.Datetime('Started Date')
    ended_at = fields.Datetime('Ended Date')
    mobile_id = fields.Integer('Mobile ID' )
    duration = fields.Float(string="Duration", compute=_compute_duration, store=True, digits=(16, 2))
    meetings_one2many = fields.One2many('calendar.event', 'journey_id', string='Journey Activities')
    routes_one2many = fields.One2many('wp.journey.routes', 'journey_routes_id', string='Route Activities')

    def start_journey(self):
        self.started_at = datetime.now()
        self.ended_at = None
        self.name = 'SJ/'+ str(self.user_id.id)+ '/' + str(self.date)

    def end_journey(self):
        self.ended_at = datetime.now()

    def process_user_end_journey(self):
        for rec in self.sudo().search([('ended_at', '=',False)]) :
            rec.ended_at = ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
            print("------------ process_user_end_journey -------")


class WpJourneyRoutes(models.Model):
    _name = "wp.journey.routes"
    _description= "Journey Routes"
    _order = 'id desc'

    name = fields.Char('Sequence No' )
    mobile_id = fields.Char('Mobile ID' )
    journey_routes_id = fields.Many2one('wp.salesperson.journey', string="Journey")
    latitude = fields.Float('Latitude' , digits=(16, 5) , store=True)
    longitude = fields.Float('Longitude', digits=(16, 5), store=True)


class WpDraftSalesMeet(models.Model):
    _name = "wp.draft.sales.meet"
    _order = 'id desc'

    name = fields.Char('Sequence No' )
    date = fields.Date('Date')
    output = fields.Text('Output')
    state = fields.Selection([('Draft', 'Draft'), ('Done', 'Done')], default='Draft')

    def draft_meetings(self):
        self.env.cr.execute(""" select count(*)  FROM calendar_event where meeting_type = 'check-in' and expense_date <= '%s' and active = True""" % (self.date))
        res1 = self.env.cr.fetchall()
        res = " Active True Count : " + str(res1[0][0]) + '\n \n'

        self.env.cr.execute(""" select count(*) from calendar_event where meeting_type = 'check-in' and active = False and draft_entries = False """)
        res2 = self.env.cr.fetchall()
        res  += " Active False Count : " +  str(res2[0][0]) + '\n \n'

        self.env.cr.execute(""" select count(*)  from calendar_event where meeting_type = 'check-in' and checkin_lattitude = 0.0 """)
        res3 = self.env.cr.fetchall()
        res  += " Lat Long Not fetched Count : " + str(res3[0][0]) + '\n \n'

        self.env.cr.execute(""" delete from calendar_event where meeting_type = 'check-in' and active = False and draft_entries = False """)
        self.env.cr.execute(""" delete from calendar_event where meeting_type = 'check-in' and checkin_lattitude = 0.0 """)
        self.env.cr.execute(""" update calendar_event set active = False , draft_entries = True
where meeting_type = 'check-in' and active = True  and expense_date <= '%s' and (draft_entries is Null or draft_entries = False)""" % (self.date))


        if res1[0][0] > 0:
            res += " Meetings Drafted Successfully" + '\n \n'

        if res2[0][0] > 0 or res3[0][0]:
            res += " Meetings Cleaned Successfully" + '\n \n'

        self.sudo().write({'output':res, 'name': 'DM/'+ str(self.id), 'state': 'Done' })
