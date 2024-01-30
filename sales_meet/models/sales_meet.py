from datetime import datetime, timedelta, date
from odoo import tools, api, SUPERUSER_ID, fields, models, _
from time import gmtime, strftime
from odoo.exceptions import UserError, ValidationError
from socket import error as SocketError
import requests
import urllib, json
import simplejson

# from geopy.geocoders import GoogleV3
# import geocoder
# import googlemaps
# import time
# import dateutil.parser
# from dateutil.relativedelta import relativedelta
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT , DEFAULT_SERVER_DATETIME_FORMAT
# import logging
# _logger = logging.getLogger(__name__)

# googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'
# gmaps = googlemaps.Client(key='AIzaSyBWGBUR56Byqip7RUel5-EeWzFQygna2Hg')
# google_api_key = 'AIzaSyCt4jsSrJ9C9tIhlAg0hMerzY3lOE1yoq8'
# key = 'AIzaSyAueXqmASv23IO3NSdPnVA_TNJOWADjEh8'
# google_key = 'AIzaSyCt4jsSrJ9C9tIhlAg0hMerzY3lOE1yoq8'
# geocoder = GoogleV3()


datetimeFormat = '%Y-%m-%d %H:%M:%S'
google_key = 'AIzaSyAueXqmASv23IO3NSdPnVA_TNJOWADjEh8'


class sales_meet(models.Model):
    _inherit = "calendar.event"
    _order = 'start_date desc'

    
    def create(self, vals):
        event = super(sales_meet, self).create(vals)
        if event.lead_id:
            event.lead_id.log_meeting(event.name, event.start, event.duration)
        return event

    
    def default_get(self, fields_list):
        res = super(sales_meet, self).default_get(fields_list)

        res['start_date'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        res['start'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        res['stop'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        res['expense_date'] = datetime.now().strftime('%Y-%m-%d')
        res['user_name'] = self.env['res.users'].sudo().search([('id', '=', self.env.uid)]).name

        ip = requests.get('https://api64.ipify.org?format=json').json()
        response = requests.get(f'https://ipapi.co/{ip["ip"]}/json/').json()
        if not response:
            raise ValidationError(
                "Please allow location access to the site ! \n Go to Site settings and select allow in location section")
        res['checkin_lattitude'] = response['latitude']
        res['checkin_longitude'] = response['longitude']
        return res

    name = fields.Char('Meeting Subject', required=False,
                       store=True)  # states={'done': [('readonly', True)]}, required=False,
    checkin_lattitude = fields.Float('Checkin Latitude', digits=(16, 5), store=True)
    checkin_longitude = fields.Float('Checkin Longitude', digits=(16, 5), store=True)
    checkout_lattitude = fields.Char('Checkout Latitude')
    checkout_longitude = fields.Char('Checkout Longitude')
    # distance = fields.Char('Distance')
    timein = fields.Datetime(string="Time IN")
    timeout = fields.Datetime(string="Time OUT")
    islead = fields.Boolean("Lead")
    isopportunity = fields.Boolean("Opportunity")
    iscustomer = fields.Boolean("Customer")
    ischeck = fields.Selection([('lead', 'Lead'),
                                ('Retailer', 'Retailer'),
                                ('customer', 'Customer')], string='Partner Type')
    lead_id = fields.Many2one('crm.lead', string='Lead', domain="[('type', '=', 'lead')]")
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    status = fields.Selection([('draft', 'Draft'),
                               ('open', 'In Meeting'),
                               ('close', 'Close')], string='Status', readonly=True, default='draft')
    stage_id = fields.Many2one('crm.stage', string='Stage', index=True)
    meeting_duration = fields.Char('Meeting Duration', store=True)
    source = fields.Char('Source Address', store=True)
    source_address = fields.Char('Source Address', store=True)
    destination = fields.Char('Destination Address', store=True)
    destination_address = fields.Char('Destination Address')
    partner_latitude = fields.Float(string='Source Geo Latitude', digits=(16, 5), store=True)
    partner_longitude = fields.Float(string='Source Geo Longitude', digits=(16, 5), store=True)
    partner_dest_latitude = fields.Float(string='Dest Geo Latitude', digits=(16, 5), store=True)
    partner_dest_longitude = fields.Float(string='Dest Geo Longitude', digits=(16, 5), store=True)
    date_localization = fields.Date(string='Geolocation Date', store=True)
    # next_activity_id = fields.Many2one("crm.activity", string="Next Meeting Reminder", index=True)
    date_action = fields.Date('Next Activity Date', index=True)
    # categ_id = fields.Many2one('crm.activity', string="Activity")
    partner_id = fields.Many2one('res.partner', string="Customer")
    retailer_id = fields.Many2one('wp.retailer', string="Retailer")

    # start = fields.Datetime('Start')
    # stop = fields.Datetime('Stop')
    start_date = fields.Date('Start Date', compute=False, inverse=False)
    stop_date = fields.Date('End Date', compute=False, inverse=False)
    display_time = fields.Char('Event Time', compute=False)
    display_start = fields.Char('Date', compute=False)
    reverse_location = fields.Char('Current Location')
    next_flag = fields.Boolean("Next Date Flag")
    expense_date = fields.Date('Meeting Date')
    attach_doc_count = fields.Integer(string="Number of documents attached", compute='count_docs')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('calendar.event'))

    user_name = fields.Char('User Name', readonly=True, store=True)
    participants_names = fields.Char('Participants', compute='onchange_partner', store=True)
    ishome = fields.Boolean("Home Location")
    distance = fields.Float(string='Distance', store=True)
    # duration = fields.Char(string='Duration',  store=True)
    draft_entries = fields.Boolean("Draft")
    ho_lead = fields.Boolean("HO Lead", default=False)
    expense_bool = fields.Boolean("Expense Bool", default=False)
    expense_id = fields.Many2one('hr.expense', string="Expense")
    business_generated = fields.Float('Business Generated')
    journey_id = fields.Many2one('wp.salesperson.journey', string="Journey")
    is_synched = fields.Boolean("Synced", default=False)
    isjourney = fields.Boolean("Journey")
    mobile_id = fields.Char('Mobile ID')
    journey_mobile_id = fields.Integer('Journey Mobile ID')
    meeting_type = fields.Selection([('check-in', 'Checkin'),
                                     ('check-out', 'Checkout'),
                                     ('journey', 'Journey')], string='Type')
    visit_type = fields.Selection([('Retail', 'Retail'),
                                   ('Project', 'Project')], string='Visit Type')
    location_type = fields.Selection([('Headquarter', 'Headquarter'),
                                      ('Outstation', 'Outstation')], string='Location Type')

    def action_save(self, context):
        return {'type': 'ir.actions.act_window_close'}

    def write(self, values, context=None):

        if len(values) and len(values) >= 3 and not self.expense_bool and not self.ishome and not self.isjourney:
            if values['description']:
                values.update({'expense_bool': True})

        update_rec = super(sales_meet, self).write(values)

        for res in self:
            # # print "kkkkkkkkkkkkkkkkkkkkddddddddddddd" , res.checkin_lattitude , res.checkin_longitude
            if res.lead_id or res.opportunity_id:
                log_data = {
                    # 'next_activity_id': res.categ_id.id,
                    'lead_id': res.lead_id.id,
                    'list_lead_id': res.lead_id.id,
                    'sale_description': res.description,
                    'user_id': res.user_id.id,
                    'status': 'open',
                    'business_generated': res.business_generated,
                }

                self.env['crm.lead.log.list'].with_context(mail_auto_subscribe_no_notify=True).sudo().create(log_data)

        print("----------- Meetings Write Method Initiated ----------------")
        return update_rec

    @api.depends('partner_ids')
    def onchange_partner(self):
        for event in self:
            participants = []
            for partner in event.partner_ids:
                participants.append(partner.name)
            participants = ",".join(participants)
            event.participants_names = participants

    def checkedin(self):
        pass

    
    def process_delete_meetings_scheduler_queue(self):
        for rec in self.sudo().search(['|', ('name', '=', False), ('stage_id', '=', False)]):
            rec.sudo().unlink()

    
    def process_update_address_scheduler_queue(self):
        today = datetime.now() - timedelta(days=1)
        daymonth = today.strftime("%Y-%m-%d")
        count = 0

        for rec in self.sudo().search([('status', '!=', 'draft'), ('meeting_type', '=', 'check-in'),
                                       ('expense_date', '>=', daymonth), ('reverse_location', '=', False)]):

            if rec.checkin_lattitude and rec.checkin_longitude:
                # location_list = geocoder.google([rec.checkin_lattitude,rec.checkin_longitude], method='reverse')
                # address = location_list.address
                # rec.reverse_location = address
                # rec.write({'reverse_location': address}) 

                latitude = rec.checkin_lattitude
                longitude = rec.checkin_longitude

                f = urllib.urlopen("https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s" % (
                    latitude, longitude, google_key))
                values = json.load(f)

                address = (values["results"][1]['formatted_address']).encode('utf8')
                count += 1
                print("Count ---------------", count, address)
                rec.write({'reverse_location': address})

                f.close()

    
    def process_update_distance_scheduler_queue(self):
        location_dict = {}
        users = []
        location = []

        today = datetime.now() - timedelta(days=1)
        daymonth = today.strftime("%Y-%m-%d")

        meeting_ids = self.sudo().search([('status', '!=', 'draft'), ('meeting_type', '=', 'check-in'),
                                          ('expense_date', '>=', daymonth), ('duration', '=', False)],
                                         order="user_id , id asc")
        for rec in meeting_ids:
            if rec.reverse_location:
                users.append(rec.user_id.id)
                location.append(rec.id)

                for i, j in zip(users, location):
                    location_dict.setdefault(i, []).append(j)

        for key, values in location_dict.items():
            # print "key: {}, value: {}".format(key, values)
            location_list = sorted(list(set(location_dict[key])))

            final_loc_list = [(location_list[i], location_list[i + 1]) for i in range(0, len(location_list) - 1)]
            count = 0
            for records in final_loc_list:
                record_list = self.search([('id', 'in', records)])
                meet_list = [x.reverse_location for x in record_list]
                # record_id_list = [x.id for x in record_list]
                # date_list = [x.expense_date for x in record_list][1]
                meet_list.append(google_key)
                lo = tuple(meet_list)
                first_id = [x.id for x in record_list][0]
                # sec_id = record_id_list[1]

                try:
                    url_list = []
                    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=%s&destinations=%s&key=%s' % lo

                    result = simplejson.load(urllib.urlopen(url))
                    # driving_time = result['rows'][0]['elements'][0]
                    # # print "sssssssssssssssssssssssssssss" , result['status'] , type(result['status']) , result['rows'] != []

                    if result['rows'] != []:

                        if result['rows'][0]['elements'][0] != {'status': 'NOT_FOUND'} or result[
                            'status'] != 'OVER_QUERY_LIMIT':
                            distance = result['rows'][0]['elements'][0]['distance']
                            meters = float(distance['value'])
                            kilometers = float(meters / 1000)
                            duration = result['rows'][0]['elements'][0]['duration']
                            time = duration['text']
                    else:
                        kilometers = time = 0.0

                except SocketError as e:
                    pass

                count += 1

                print("-------------- count, kilometers , time ---------", count, kilometers, time)

                write_data = self.search([('id', '=', first_id)]).write({
                    'distance': kilometers,
                    'duration': time,
                })

    def checkin(self):
        if self.checkin_lattitude and self.checkin_longitude:
            self.status = 'open'
            self.next_flag = False
            self.meeting_type = 'check-in'
            self.expense_date = datetime.now().strftime('%Y-%m-%d')
            if not self.mobile_id:
                self.mobile_id = str(self.id)
        else:
            if not self.ho_lead:
                raise UserError(_("Your location Settings/GPS are not enabled. \
                 Contact IT Support for help"))
            else:
                self.status = 'open'
                self.next_flag = False
                self.meeting_type = 'check-in'
                self.expense_date = datetime.now().strftime('%Y-%m-%d')
                if not self.mobile_id:
                    self.mobile_id = str(self.id)

    def create_event(self):
        new_stage = self.env['crm.stage'].sudo().search([('name', '=', 'New')])
        calendar_event_vals = {
            'name': self.name,
            'start_date': self.date_action,
            'stop_date': self.date_action,
            'start': self.date_action,
            'stop': self.date_action,
            'allday': False,
            'show_as': 'busy',
            'partner_ids': [(6, 0, [])] or '',
            'partner_id': self.partner_id.id if self.ischeck == 'customer' else '',
            'stage_id': new_stage.id or '',
            # 'categ_id': self.next_activity_id.id,
            'user_id': self.user_id.id,
            'ischeck': self.ischeck,
            'lead_id': self.lead_id.id if self.ischeck == 'lead' else '',
            'opportunity_id': self.opportunity_id.id if self.ischeck == 'opportunity' else '',
            'retailer_id': self.retailer_id.id if self.ischeck == 'Retailer' else '',
            'next_flag': True,
        }

        self.status = 'close'
        self.env['calendar.event'].create(calendar_event_vals)

    def count_docs(self):
        expense_ids = self.env['hr.expense'].sudo().search([("meeting_id", "=", self.id)])
        self.attach_doc_count = len(expense_ids) or 0

    def get_attached_docs(self):
        # print "------------Meetings ---- get_attached_docs ----------------------------"
        expense_ids = self.env['hr.expense'].sudo().search([("meeting_id", "=", self.id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sales_meet.hr_expense_actions_my_unsubmitted_ext')
        list_view_id = imd.xmlid_to_res_id('hr_expense.view_expenses_tree')
        form_view_id = imd.xmlid_to_res_id('hr_expense.hr_expense_form_view')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'],
                      [False, 'graph'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(expense_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % expense_ids.ids
        elif len(expense_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = expense_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def create_expense(self):

        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)]).id

        ctx = self._context.copy()
        ctx.update({
            'default_meeting_id': self.id,
            'default_date': self.expense_date,
            'default_employee_id': employee_id,
            'default_meeting_boolean': True,

        })
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('hr_expense.hr_expense_actions_my_unsubmitted')
        form_view_id = imd.xmlid_to_res_id('hr_expense.hr_expense_form_view')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': 'new',
            'context': ctx,
            'res_model': action.res_model,
        }

        # print "------------------- create_expense from Meeting -----------------------"
        return result

    @api.onchange('ischeck')
    def _onchange_date(self):
        if self.ischeck == 'customer':
            return {'domain': {'opportunity_id': [('user_id', 'in', [self.env.uid])], }}
        elif self.ischeck == 'Retailer':
            return {'domain': {'retailer_id': [('salesperson_id', 'in', [self.env.uid])], }}
        elif self.ischeck == 'lead':
            return {'domain': {'opportunity_id': [('user_id', 'in', (self.env.uid, False))], }}

    @api.onchange('lead_id', 'opportunity_id', 'partner_id', 'retailer_id', 'ishome')
    def _onchange_lead_id(self):
        if self.ishome:
            self.name = "Home location"
        elif self.isjourney:
            self.name = "Journey"
        elif self.ischeck == 'lead':
            if self.lead_id:
                self.opportunity_id = self.partner_id = ''
                self.name = "Meeting With " + self.lead_id.name

        elif self.ischeck == 'Retailer':
            if self.retailer_id:
                self.partner_id = self.lead_id = ''
                self.name = "Meeting With " + self.retailer_id.name

        elif self.ischeck == 'customer':
            if self.partner_id:
                self.opportunity_id = self.lead_id = ''
                self.name = "Meeting With " + self.partner_id.name
