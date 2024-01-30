from odoo import http
from odoo.http import request
import json
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class WpJourneyController(http.Controller):

	# @http.route('/wmvdapi/start_journey', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/start_journey', methods=["POST"], type='json', auth='public')
	def start_journey(self, user_id=None, date=None, started_at=None):
		print("------------/wmvdapi/start_journey -----------", user_id)

		# journey = request.env['wp.salesperson.journey'].sudo().create_journey(user_id=user_id, date=date, started_at=started_at)

		jl = request.env['wp.salesperson.journey'].sudo().search([('user_id', '=', user_id),('date','=',date)])
		if jl:
			jl.ended_at = None
		else:
			val = {
					"user_id" : user_id,
					"date" : date,
					"started_at" : started_at,
					"name" : 'SJ/'+ str(user_id)+ '/' + str(date),
					# "started_at" : ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
				}
			jl = request.env['wp.salesperson.journey'].sudo().create(val)

		journey = {
				"id" : jl.id,
				"user_id" : user_id,
				"date": date ,
				"started_at" : jl.started_at,
				"ended_at" : jl.ended_at or '',
		}

		response = {'journey' : journey}
		return {'success': response, 'error': None}
		

	# @http.route('/wmvdapi/stop_journey', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/stop_journey', methods=["POST"], type='json', auth='public')
	def stop_journey(self, journey_id=None, ended_at=None):
		print("------------/wmvdapi/stop_journey -----------")
		jl = request.env['wp.salesperson.journey'].sudo().search([('id', '=', journey_id),('ended_at','=', False)])

		if jl:
			jl.ended_at = ended_at
			# jl.ended_at = ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
		else:
			return {'success': None, 'error':'Invalid request'}

		journey = {
				"id" : jl.id,
				"user_id" : jl.user_id.id,
				"date": jl.date ,
				"started_at" : jl.started_at,
				"ended_at" : jl.ended_at,
		}

		response = {'journey' : journey}
		return {'success': response, 'error': None}


	# @http.route('/wmvdapi/push_journey_routes', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/push_journey_routes', methods=["POST"], type='json', auth='public')
	# def push_journey_activity(self, activity_id, lat, long, journey_id, time):
	def push_journey_routes(self, routes):
		print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", routes)
		# print("------------/wmvdapi/push_journey_routes -----------", lat, long, journey_id)
		if routes:
			routes_list=[]
			for res in routes:
				#print("BBBBBBBBBBBBBBBBBBBBBBB", res, res['journey_id'])

				domain = [('id', '=', res['journey_id']),('ended_at','=', False)]
				jl = request.env['wp.salesperson.journey'].sudo().search(domain)

				if jl:
					route_vals = {
						'journey_routes_id':jl.id,
						'mobile_id': res['route_id'],
						'latitude': res['lat'],
						'longitude': res['long'],

					}

					rv = request.env['wp.journey.routes'].sudo().create(route_vals)

					journey_route = {
							"route_id" : res['route_id'],
							"journey_id" : res['journey_id'],
							"lat": res['lat'] ,
							"long" : res['long'],
					}
					routes_list.append(journey_route)


			response = {'routes' : routes_list}
			return {'success': response, 'error': None}

		else:
			return {'success': None, 'error':'Invalid request'}

	# @http.route('/wmvdapi/push_journey_activity', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/push_journey_activity', methods=["POST"], type='json', auth='public')
	def push_journey_activity(self, activity):
		print("------------/wmvdapi/push_journey_activity -----------", activity)
		if activity:
			activity_list=[]
			for res in activity:
				print("---------------", res, res['journey_id'])

				jl = request.env['wp.salesperson.journey'].sudo().search([('id', '=', res['journey_id']),('ended_at','=', False)])

				if jl:
					# started_at = (datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
					started_at = res['time']


					calendar_event_vals = {
						'name': 'Journey' + jl.user_id.name + str(started_at),
						'start_date': started_at,
						'stop_date': started_at,
						'start': started_at,
						'stop': started_at,
						'allday': False,
						'show_as': 'busy',
						'partner_ids': [(6, 0, [])] or '',
						'status': 'close',
						'journey_mobile_id': jl.mobile_id,
						'meeting_type': 'journey',
						'journey_id':jl.id,
						'mobile_id': res['activity_id'],
						'isjourney': True,
						'is_synched': True,
						'user_id': jl.user_id.id,
						'checkin_lattitude': res['lat'],
						'checkin_longitude': res['long'],
					}

					cal = request.env['calendar.event'].sudo().create(calendar_event_vals)

					activity_dict = {
						"id" : res['activity_id'],
						"portal_id" : cal.id,
						"lat": res['lat'],
						"long": res['long'],
						"journey_id" : jl.id,
						"time" : started_at,
						"address" : cal.reverse_location or '',
						"type": "journey",
						"reason" : "",
						"user_id" : jl.user_id.id,
					}
					activity_list.append(activity_dict)

					print("ssssssssssssssssssssssssssssssss", activity_dict)

			response = {'activity' : activity_list}
			return {'success': response, 'error': None}

		else:
			return {'success': None, 'error':'Invalid request'}


	# @http.route('/wmvdapi/get_journey', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/get_journey', methods=["POST"], type='json', auth='public')
	def get_journey(self, user_id=None):
		print("------------/wmvdapi/get_journey -----------", user_id)
		jl = request.env['wp.salesperson.journey'].sudo().search([('user_id', '=', user_id)])
		if jl:
			jl_count = len(jl)
			journey_list = []
			for res in jl:
				journey = {
						"id" : res.id,
						"user_id" : user_id,
						"date": res.date ,
						"started_at" : res.started_at,
						"ended_at" : res.ended_at or '',
				}
				journey_list.append(journey)

			response = {'count' : jl_count, 'journeys' : journey_list}
			return {'success': response, 'error': None}
		else:
			return {'success': None, 'error':' No Records Found'}



	# @http.route('/wmvdapi/get_journey_details', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/get_journey_details', methods=["POST"], type='json', auth='public')
	def get_journey_details(self, journey_id=None):
		print("------------/wmvdapi/get_journey_details -----------", journey_id)
		jl = request.env['wp.salesperson.journey'].sudo().search([('id', '=', journey_id)])
		cl = request.env['calendar.event'].sudo().search([('journey_id', '=', journey_id)])
		if cl:
			cl_count = len(cl)
			activity_list=[]
			for res in cl:

				activities = {
						"id" : res.mobile_id,
						"portal_id" : res.id,
						"lat": res.checkin_lattitude,
						"long": res.checkin_longitude,
						"journey_id" : res.journey_id.id,
						"time" : res.start_date,
						"address" : res.reverse_location or '',
						"type": "journey",
						"reason" : "",
						"user_id" : res.user_id.id,
					}
				activity_list.append((activities))

			response = {'count' : cl_count, 
						"date" : jl.date,
						"user_id" : jl.user_id.id,
						"started_at" : jl.started_at,
						"ended_at" : jl.ended_at or '',
						"activities": activity_list,
					}

			return {'success': response, 'error': None}
		else:
			return {'success': None, 'error':' No Records Found'}


	# @http.route('/wmvdapi/get_routes_details', methods=["POST"], type='json', auth='user')
	@http.route('/wmvdapi/get_routes_details', methods=["POST"], type='json', auth='public')
	def get_routes_details(self, journey_id=None):
		print("------------/wmvdapi/get_routes_details -----------", journey_id)
		jl = request.env['wp.salesperson.journey'].sudo().search([('id', '=', journey_id)])
		cl = request.env['wp.journey.routes'].sudo().search([('journey_routes_id', '=', journey_id)])
		if cl:
			cl_count = len(cl)
			routes_list=[]
			for res in cl:

				journey_route = {
							"route_id" : res.mobile_id,
							"journey_id" : res.journey_routes_id.id,
							"lat": res.latitude ,
							"long" : res.longitude,
					}
				routes_list.append((journey_route))

			response = {'count' : cl_count, 
						"date" : jl.date,
						"user_id" : jl.user_id.id,
						"started_at" : jl.started_at,
						"ended_at" : jl.ended_at or '',
						"routes": routes_list,
					}

			return {'success': response, 'error': None}
		else:
			return {'success': None, 'error':' No Records Found'}
