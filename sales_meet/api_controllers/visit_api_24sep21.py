from odoo import http
from odoo.http import request
import json
import uuid
import time
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.http import Response


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
mainfields = ['id', 'name']

headers = {'Content-Type': 'application/json',}
# headers = {'Content-Type': 'message/http',}

class WpVisitController(http.Controller):

    @http.route('/wmvdapi/create_visit', methods=["POST"], type='json', auth='user')
    def create_visit(self, visit_id=None, user_id=None, lead_id=None, retailer_id=None, distributor_id=None, stage_id=None, 
        activity_id=None, date=None, started_at=None, latitude=None, longitude=None, description=None, address=None):
        print("------------/wmvdapi/create_visit -----------", visit_id, user_id, lead_id, retailer_id, distributor_id, 
            stage_id, activity_id, date, started_at, latitude, longitude, description, address)
        # {"jsonrpc":"2.0","params":{"user_id":  1088, "lead_id": None, "retailer_id" :None, "distributor_id":None,
         # "stage_id":None, "activity_id": None, "date":None, "started_at": None}}
        lead = retailer = partner = stage = activity = ''
        if lead_id: lead = request.env['crm.lead'].sudo().search([('id', '=', lead_id)])

        if retailer_id: retailer = request.env['wp.retailer'].sudo().search([('id', '=', retailer_id)])

        if distributor_id: partner = request.env['res.partner'].sudo().search([('id', '=', distributor_id)])

        if stage_id: stage = request.env['crm.stage'].sudo().search([('id', '=', stage_id)])

        if activity_id: activity = request.env['crm.activity'].sudo().search([('id', '=', activity_id)])

        users_rec = request.env['res.users'].sudo().search([('id', '=', user_id),('active', '=', True)], limit=1).name

        meet_name = "Meeting With " + (lead.name if lead_id else  partner.name if distributor_id else retailer.name if  retailer_id else '')
        ischeck = 'lead' if lead_id else  'customer' if distributor_id else 'Retailer' if  retailer_id else ''

        jl = request.env['wp.salesperson.journey'].sudo().search([('user_id', '=', user_id),('date','=',date)], limit=1)
        if not jl:
            val = {
                    "user_id" : user_id,
                    "date" : date,
                    "started_at" : started_at,
                    "name" : 'SJ/'+ str(user_id)+ '/' + str(date),
                    # "started_at" : ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                }
            jl = request.env['wp.salesperson.journey'].sudo().create(val)

       
        calendar_event_vals = {
                'name': meet_name,
                'start_date': started_at,
                'stop_date': started_at,
                'start': started_at,
                'stop': started_at,
                'allday': False,
                'show_as': 'busy',
                'meeting_type': 'check-in',
                'partner_ids': [(6, 0, [])] or '',
                'stage_id': stage.id or '',
                # 'categ_id': activity.id or '',
                'user_id': user_id,
                'ischeck': ischeck,
                'partner_id': partner.id if distributor_id else '',
                'lead_id': lead.id if lead_id else '',
                'retailer_id': retailer.id if retailer_id else '',
                'status': 'close',
                "description": description or '',
                'mobile_id': visit_id,
                'checkin_lattitude': latitude,
                'checkin_longitude': longitude,
                'reverse_location': address,
                'journey_id':jl.id,
                'expense_date': datetime.now().strftime('%Y-%m-%d'),
                # "mobile_id": str(uuid.uuid4()),
            }

        event = request.env['calendar.event'].sudo().create(calendar_event_vals)

        journey = {
                    "id" : jl.id or None,
                    "date": jl.date or '',
                    "started_at" : jl.started_at or '',
                    "ended_at" : jl.ended_at or '',
                }

        vals = {
                "id": visit_id,
                "stage_id": stage.id or None,
                "stage": stage.name or '',
                "activity_id": activity.id or 0,
                "activity": activity.name or '',
                "time": started_at,
                "user_id": user_id,
                "user": users_rec,
                "name": meet_name  or '',
                'distributor_id': partner.id if distributor_id else None,
                'lead_id': lead.id if lead_id else None,
                'retailer_id': retailer.id if retailer_id else None,
                'distributor_name': partner.name if distributor_id else '',
                'lead_name': lead.name if lead_id else '',
                'retailer_name': retailer.name if retailer_id else '',
                "meeting_type": "check-in",
                "ischeck": ischeck,
                "type": "check-in",
                "reason" : description or '',
                "lat": latitude,
                "long": longitude,
                "portal_id" : event.id,
                'address': address,
                "journey_id" : jl.id,
                "mobile_id": event.mobile_id,
                "journey": journey,
            }

        response = {'visit' : vals}
        return {'success': response, 'error': None}

    @http.route('/wmvdapi/create_home_visit', methods=["POST"], type='json', auth='user')
    def create_home_visit(self, visit_id=None, user_id=None, meeting_date=None, started_at=None, 
        latitude=None, longitude=None, address=None):
        print("------------/wmvdapi/create_home_visit -----------", visit_id, user_id, meeting_date, started_at, latitude, longitude, address)
        users_rec = request.env['res.users'].sudo().search([('id', '=', user_id),('active', '=', True)], limit=1).name
        meet_name = "Home Location"

        calendar_event_vals = {
                'name': meet_name,
                'start_date': started_at,
                'stop_date': started_at,
                'start': started_at,
                'stop': started_at,
                'allday': False,
                'show_as': 'busy',
                'meeting_type': 'check-in',
                'partner_ids': [(6, 0, [])] or '',
                'stage_id': '',
                # 'categ_id': '',
                'user_id': user_id,
                'ischeck': False,
                'partner_id': '',
                'lead_id': '',
                'retailer_id': '',
                'status': 'close',
                "description": meet_name or '',
                'mobile_id': visit_id,
                'checkin_lattitude': latitude,
                'checkin_longitude': longitude,
                'reverse_location': address,
                'journey_id': '',
                'expense_date': meeting_date,
            }

        event = request.env['calendar.event'].sudo().create(calendar_event_vals)

        journey = { "id" : None, "date": '', "started_at" : '', "ended_at" : '', }

        vals = {
                "id": visit_id,
                "stage_id": None,
                "stage": '',
                "activity_id": None,
                "activity": '',
                "time": started_at,
                "user_id": user_id,
                "user": users_rec,
                "name": meet_name  or '',
                'distributor_id': None,
                'lead_id': None,
                'retailer_id': None,
                'distributor_name': '',
                'lead_name': '',
                'retailer_name': '',
                "meeting_type": "check-in",
                "ischeck": False,
                "type": "check-in",
                "reason" : meet_name or '',
                "lat": latitude,
                "long": longitude,
                "portal_id" : event.id,
                'address': address,
                "journey_id" : '',
                "mobile_id": event.mobile_id,
                "journey": journey,
        }

        response = {'visit' : vals}
        return {'success': response, 'error': None}

    @http.route('/wmvdapi/get_user_visits', auth='user', methods=["POST"], type='json')
    def get_user_visits(self, user_id=None, date=None):
        print("------------/wmvdapi/get_user_visits -----------")
        if date:
            domain = [('user_id', '=', user_id),('meeting_type','=','check-in'),('expense_date','=',date)]
        else:
            domain = [('user_id', '=', user_id),('meeting_type','=','check-in')]

        calendar_rec = request.env['calendar.event'].sudo().search(domain)
        calendar_list = []
        if calendar_rec:
            for res in calendar_rec:
                if str(res.id) == res.mobile_id:
                    started_at_date = datetime.strptime(str(res.start), DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
                    start_date = started_at_date.strftime(DATETIME_FORMAT)
                else:
                    start_date = res.start

                journey = {
                    "id" : res.journey_id.id or None,
                    "date": res.journey_id.date or '',
                    "started_at" : res.journey_id.started_at or '',
                    "ended_at" : res.journey_id.ended_at or '',
                }
                vals = {
                        "id": res.mobile_id or None,
                        "stage_id": res.stage_id.id or None,
                        # "activity_id": res.categ_id.id or 0,
                        "stage": res.stage_id.name or '',
                        # "activity": res.categ_id.name or '',
                        "time": start_date,
                        "user_id": res.user_id.id,
                        "user": res.user_id.name or '',
                        "name": res.name or '',
                        'distributor_id': res.partner_id.id or None,
                        'lead_id': res.lead_id.id or None,
                        'retailer_id': res.retailer_id.id or None,
                        'distributor_name': res.partner_id.name or '',
                        'lead_name': res.lead_id.name or '',
                        'retailer_name': res.retailer_id.name or '',
                        "meeting_type": "check-in",
                        "partner_type": res.ischeck,
                        "type": "check-in",
                        "reason" : res.description or '',
                        "lat": res.checkin_lattitude or 0.0,
                        "long": res.checkin_longitude or 0.0,
                        "portal_id" : res.id,
                        'address': res.reverse_location or '',
                        "journey": journey,
                }
                calendar_list.append(vals)

            response = {'count' : len(calendar_rec), 'list': calendar_list}
            return {'success': response, 'error': None}
        else:
            response = {'count' : 0, 'list': []}
            return {'success': response, 'error': None}
            # return {'success': None, 'error':'No Records Found'}


    @http.route('/wmvdapi/get_crm_activity', auth='user', methods=["POST"], type='json')
    def get_crm_activity(self):
        print("------------/wmvdapi/get_crm_activity -----------")
        result = request.env['crm.activity'].search([]).read(mainfields)
        activity = {'success': result or {}, 'error': None}
        # return json.dumps(activity)
        # return Response(json.dumps(activity),headers=headers)
        return activity


    @http.route('/wmvdapi/get_crm_stage', auth='user', methods=["POST"], type='json')
    def get_crm_stage(self):
        print("------------/wmvdapi/get_crm_stage -----------")
        result = request.env['crm.stage'].search([]).read(mainfields)
        stage = {'success': result or {}, 'error': None}
        # return json.dumps(stage)
        # return Response(json.dumps(stage),headers=headers)
        return stage

    @http.route('/wmvdapi/get_salesperson_lead', auth='user', methods=["POST"], type='json')
    def get_salesperson_lead(self, user_id=None):
        start = time.time()
        print("------------/wmvdapi/get_salesperson_lead -----------", user_id)
#        state_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).state_id.id
#        result = request.env['crm.lead'].search([('state_id', '=', state_id),('state_id', '!=', False),]).read(['id','name'])
        result = []
        state_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).state_id.id
        #lead_ids = request.env['crm.lead'].sudo().search([('state_id', '=', state_id),
         #   ('state_id', '!=', False),]).read(['id','display_name','user_id'])
        lead_ids = request.env['crm.lead'].sudo().search([('state_id', '!=', False),
            '|',('user_id', '=', user_id),('state_id', '=', state_id)]).read(['id','display_name','user_id'])

        for leads in lead_ids:
            vals = {'id': leads['id'], 
                    'name': str((leads['display_name']).encode('ascii', 'ignore')) + (' - (' \
                    + str(leads['user_id'][1]) + ')' if leads['user_id'] else '' ) }
            result.append(vals)

        end = time.time()
        # print "------------- END get_salesperson_lead -------", end-start
        return {'success': result or {}, 'error': None}


    @http.route('/wmvdapi/get_assigned_retailer_list', methods=["POST"], type='json', auth='user')
    def get_assigned_retailer_list(self, user_id=None):
        start = time.time()
        print("------------/wmvdapi/get_assigned_retailer_list -----------", user_id)

        manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).id
        if manager_id:
            response = self.assigned_retailer_list(manager_id, user_id, retailers=[])

            end = time.time()
            # print "------------- END get_assigned_retailer_list -------", end-start

            if response:
                return {'success': response, 'error': None}
            else:
                return {'success': None, 'error':'No Retailer Found'}

        else:
            return {'success': None, 'error':'No Retailer Found'}


    def assigned_retailer_list(self,manager_id=False, user_id=False, retailers=[]):
        retailers_rec = request.env['wp.retailer'].sudo().search([('salesperson_id', '=', user_id), ('salesperson_id', '!=', False),
                                                                  ('active', '=', True)]).read(['id', 'name', 'city', 'state_id'])

        if retailers_rec :
            for retailer in retailers_rec:
                vals = {'id': retailer['id'],
                        'name': str((retailer['name']).encode('ascii', 'ignore')) + (' - ' \
                        + str(retailer['city']) if retailer['city'] else '' ) + (" - " \
                        + str(retailer['state_id'][1]) if retailer['state_id'] else '')}
                retailers.append(vals)
            # retailers.extend(retailers_rec)

        subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id)])
        if subordinate_ids :
            for res in subordinate_ids:
                self.assigned_retailer_list(res.id, res.user_id.id, retailers)

        response = {'count' : len(retailers), 'retailers': retailers}
        return response



    @http.route('/wmvdapi/get_salesperson_distributor_list', methods=["POST"], type='json', auth='user')
    def get_salesperson_distributor_list(self, user_id=None):
        start = time.time()
        print("------------/wmvdapi/get_salesperson_distributor_list -----------", user_id)

        manager_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).id
        if manager_id:
            response = self.assigned_distributor_list(manager_id, user_id, distributors=[])

            end = time.time()
            # print "------------- END get_salesperson_distributor_list -------", end-start

            if response:
                return {'success': response, 'error': None}
            else:
                return {'success': None, 'error':'No Distributors Found'}

        else:
            return {'success': None, 'error':'No Distributors Found'}


    def assigned_distributor_list(self,manager_id=False, user_id=False, distributors=[]):
        partner_rec = request.env['res.partner'].sudo().search([('user_id', '=', user_id), ('user_id', '!=', False),
                                                                ('active', '=', True)]).read(['id', 'name', 'bp_code', 'city'])

        if partner_rec :
            for partner in partner_rec:
                vals = {'id': partner['id'], 
                        'name': (str(partner['bp_code'] + " - ") if partner['bp_code'] else '' ) \
                        +  (str((partner['name']).encode('ascii', 'ignore'))  if partner['name'] else '' ) \
                        + (' - ' + str(partner['city']) if partner['city'] else '' )}
                distributors.append(vals)
            # distributors.extend(partner_rec)

        subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id)])
        if subordinate_ids :
            for res in subordinate_ids:
                self.assigned_distributor_list(res.id, res.user_id.id, distributors)

        response = {'count' : len(distributors), 'distributors': distributors}
        return response


    # @http.route(['/wmvdapi/get_crm_stage', '/wmvdapi/get_crm_stage/<int:id>'], auth='user', methods=["POST"], type='json')
    # def get_crm_stage(self, stage_id=None):
    #     print("------------/wmvdapi/get_crm_stage -----------", stage_id)
    #     mainfields = ['id', 'name']
    #     if stage_id:
    #         result = request.env['crm.stage'].browse(stage_id).read(mainfields)
    #         stage = result and result[0] or {}
    #         return {'success': stage, 'error': None}
    #     else:
    #         result = request.env['crm.stage'].search([]).read(mainfields)
    #         stage = result or {}
    #         return {'success': stage, 'error': None}



    # @http.route(['/wmvdapi/get_crm_activity', '/wmvdapi/get_crm_activity/<int:id>'], auth='user', methods=["POST"], type='json')
    # def get_crm_activity(self, activity_id=None):
    #     print("------------/wmvdapi/get_crm_activity -----------", activity_id)
    #     mainfields = ['id', 'name']
    #     if activity_id:
    #         result = request.env['crm.activity'].browse(activity_id).read(mainfields)
    #         activity = result and result[0] or {}
    #         return {'success': activity, 'error': None}
    #     else:
    #         result = request.env['crm.activity'].search([]).read(mainfields)
    #         activity = result or {}
    #         return {'success': activity, 'error': None}


    # @http.route('/wmvdapi/get_crm_activity', auth='user', methods=["GET"], type='http')
    # def get_crm_activity(self):
    #     print("------------/wmvdapi/get_crm_activity -----------")
    #     result = request.env['crm.activity'].search([]).read(mainfields)
    #     activity = {'success': result or {}, 'error': None}
    #     # return json.dumps(activity)
    #     return Response(json.dumps(activity),headers=headers)


    # @http.route('/wmvdapi/get_crm_stage', auth='user', methods=["GET"], type='http')
    # def get_crm_stage(self):
    #     print("------------/wmvdapi/get_crm_stage -----------")
    #     result = request.env['crm.stage'].search([]).read(mainfields)
    #     stage = {'success': result or {}, 'error': None}
    #     # return json.dumps(stage)
    #     return Response(json.dumps(stage),headers=headers)

    # @http.route(['/wmvdapi/get_salesperson_lead', '/wmvdapi/get_salesperson_lead/<int:id>'], auth='user', methods=["POST"], type='json')
    # def get_salesperson_lead(self, user_id=None, lead_id=None, search_query=None):
    #     print("------------/wmvdapi/get_salesperson_lead -----------", user_id, lead_id)
    #     if user_id:
    #         state_id = request.env['hr.employee'].sudo().search([('user_id', '=', user_id),('active', '=', True)], limit=1).state_id.id
    #     mainfields = ['id', 'name', 'state_id']
    #     if lead_id:
    #         result = request.env['crm.lead'].browse(lead_id).read(mainfields)
    #         lead = result and result[0] or {}
    #         return {'success': lead, 'error': None}
    #     elif search_query:
    #         result = request.env['crm.lead'].search([('state_id', '=', state_id),
    #             ('state_id', '!=', False),
    #             ('name', 'ilike', search_query)]).read(mainfields)
    #         lead = result or {}
    #         return {'success': lead, 'error': None}

    #     else:
    #         result = request.env['crm.lead'].search([('state_id', '=', state_id),('state_id', '!=', False),]).read(mainfields)
    #         lead = result or {}
    #         return {'success': lead, 'error': None}

    # def assigned_retailer_list(self,manager_id=False, user_id=False, search_query=False,  retailers=[]):
    #     if search_query:
    #         domain = [('salesperson_id', '=', user_id),
    #                     ('salesperson_id', '!=', False),
    #                     ('active', '=', True),
    #                     ('name', 'ilike', search_query)]
    #     else:
    #         domain = [('salesperson_id', '=', user_id),
    #                   ('salesperson_id', '!=', False),
    #                   ('active', '=', True)]

    #     partner_rec = request.env['wp.retailer'].sudo().search(domain)   

    #     if partner_rec :

    #         for rec in partner_rec:
    #             retailer_user_id = request.env['res.users'].sudo().search([('partner_id','=',rec.retailer_partner_id.id)], limit=1)
    #             vals = {
    #                 'id': rec.id,
    #                 'retailer_user_id': retailer_user_id.id or '',
    #                 'name': rec.name,
    #                 'mobile': rec.mobile or '',
    #                 'email' : rec.email or '',
    #                 'salesperson_id' : rec.salesperson_id.id,
    #                 'salesperson_name' : rec.salesperson_id.name,
    #                 'state_id' : rec.state_id.id or '',
    #                 'state' : rec.state_id.name or '',
    #                 'address' : ((rec.street + ', ') if rec.street else '' ) + \
    #                             ((rec.street2+ ', ') if rec.street2 else '' )  + \
    #                             ((rec.city + ', ') if rec.city else '' ) + \
    #                             ((rec.zip + ', ') if rec.zip else '' ) + \
    #                             ((rec.state_id.name + ', ') if rec.state_id else '' ) + \
    #                             ((rec.country_id.name + ', ') if rec.country_id else '' )

    #             }
    #             retailers.append(vals)

    #     subordinate_ids = request.env['hr.employee'].sudo().search([('parent_id','=', manager_id)])
    #     if subordinate_ids :
    #         for res in subordinate_ids:
    #             print("aaaaaaaaaaaa--------------------", res.id, res.user_id.id, search_query)
    #             self.assigned_retailer_list(res.id, res.user_id.id, search_query, retailers)

    #     response = {'count' : len(retailers), 'retailers': retailers}
    #     return response
