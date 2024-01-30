

import random
from odoo.exceptions import UserError, Warning, ValidationError
from odoo import models, fields, tools, api,  _ , registry, SUPERUSER_ID
from datetime import datetime, timedelta, date
import pandas as pd
import time
from io import BytesIO
import xlwt
import re
import base64
from odoo.http import request
# from werkzeug.urls import url_encode
from werkzeug.urls import url_encode
import ast
from xlrd import open_workbook

import io
import qrcode

# import cv2
# from PIL import Image
# from pyzbar.pyzbar import decode
# from iteration_utilities import duplicates

# list_barcode= []
# rejected_barcode = []
# todaydate = "{:%d-%b-%y}".format(datetime.now())
# current_time = ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
# server_time = ( datetime.now()).strftime('%Y-%m-%d %H:%M:%S')


STATE = [('draft', 'Draft'), 
		  ('generated', 'Generated'), 
		  ('create', 'Created'), 
		  ('update', 'Updated'), 
		  ('cn_raised', 'CN Raised'), 
		  ('reject', 'Rejected')]

class barcode_marketing(models.Model):
	_name = "barcode.marketing"
	_inherit = 'mail.thread'
	_description= "QR Code Generate"
	_order = 'id desc'

	name = fields.Char('Sequence No')
	date = fields.Date('Date', default=lambda self: fields.datetime.now())
	barcode = fields.Integer('No Of Sequence')
	attachment_id = fields.Many2one( 'ir.attachment', string="Attachment", ondelete='cascade')
	datas = fields.Binary(string="XLS Report", related="attachment_id.datas")
	report = fields.Binary('Prepared file', filters='.xls', readonly=True)
	state = fields.Selection([('draft', 'Draft'), ('generated', 'Generated'), ('print', 'Printed')], default='draft')
	amount= fields.Float('Coupon Worth')
	handling_charge= fields.Float('Handling Charge')
	product_name = fields.Char('Product')
	lines_one2many = fields.One2many('barcode.marketing.line', 'barcode_marketing_id', string='Barcode Lines')

	@api.depends('date','barcode')
	def _get_name(self):
		rep_name = "Barcode_Report"
		for res in self:
			# if not res.name:
				if res.date and res.barcode and not res.name:
					rep_name = "QRcode Sequences (%s)(%s Rupees) - %s.xls" % (res.date,res.amount,res.id)
				res.name = rep_name

	
	def generate_barcode(self):
		start = time.time()
		order_lines = []
		count = self.barcode
		if self.date and self.amount:
			self.name = "QRcode Sequences (%s)(%s Rupees) - %s.xls" % (self.date,self.amount,self.id)

		count_no = 0
		# self.env.cr.execute("SELECT name FROM barcode_marketing_line ")
		# sequence_name = [int(x[0]) for x in self.env.cr.fetchall()]

		while len(order_lines) < count:
			random_numbers = random.randint(1000000000000,9999999999999)

			# if sequence_name.count(random_numbers) == 0:
			# 	# print "aaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbb"


			order_lines.append((0, 0, {
										'name': random_numbers,
										'date': self.date,
										'amount': self.amount,
										'handling_charge': self.handling_charge,
										'barcode_marketing_id': self.id,
										'product_name': self.product_name

										}))
			count_no += 1
			# print "----------------Line count_no" , count_no


		self.lines_one2many = order_lines
		self.state = 'generated'
		end = time.time()
		# print "-------------------------------- generate_barcode TIME" , end-start



	
	def print_report(self):
		start = time.time()
		self.ensure_one()
		if self.date and self.barcode:
			if not self.attachment_id:
				workbook = xlwt.Workbook(encoding='utf-8')
				worksheet = workbook.add_sheet('Qrcode Details')
				fp = BytesIO()

				header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz center; \
					borders: bottom thin, top thin, left thin, right thin')
				base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')

				row_index = 0
				worksheet.col(0).width = 12000
				header_fields = ['Sequence No']
				row_index += 1
				
				for index, value in enumerate(header_fields):
					worksheet.write(row_index, index, value, header_style)
				row_index += 1

				barcode_marketing_ids = [x.name for x in self.env['barcode.marketing.line'].sudo().search([('date','=',self.date),
					('barcode_marketing_id','=',self.id)])]
				
				if (not barcode_marketing_ids):
					raise Warning(_('Record Not Found'))

				for barcode_marketing_id in barcode_marketing_ids:
					worksheet.write(row_index, 0,int(barcode_marketing_id), base_style)
					row_index += 1

				row_index +=1
				workbook.save(fp)

			out = base64.encodestring(fp.getvalue())
			self.write({'report': out,'state':'print'})
		end = time.time()
		# print "---------------print_report TIME --------" , end-start



class barcode_marketing_line(models.Model):
	_name = "barcode.marketing.line"
	_description= "QR Code Lines"

	name = fields.Char('Sequence No' )
	sequence_no = fields.Integer('Sequence')
	date = fields.Date('Date')
	updated_date = fields.Date('Updated Date')
	updated_datetime = fields.Datetime('Updated Datetime')

	barcode_marketing_id = fields.Many2one('barcode.marketing', string="Barcode", ondelete='cascade')
	barcode_check_id = fields.Many2one('barcode.marketing.check', string="Scan ID")
	barcode_check2_id = fields.Many2one('barcode.marketing.check', string="Scan ID 2")
	partner_id = fields.Many2one('res.partner',  string="Partner")
	scanned_datetime2 = fields.Datetime('Scanned Datetime 2')
	scanned_date2 = fields.Date('Scanned Date 2')
	partner_id2 = fields.Many2one('res.partner',  string="Partner 2")
	flag = fields.Boolean('Flag')
	second_flag = fields.Boolean('Second Flag')
	amount= fields.Float('Coupon Worth')
	handling_charge= fields.Float('Handling Charge')
	product_name = fields.Char('Product')
	state = fields.Selection(STATE, default='draft')
	recheck_bool = fields.Boolean('Coupon Recheck Bool')
	rechecked_date = fields.Date('Rechecked Date')
	barcode_recheck_id = fields.Many2one('barcode.marketing.check', string="ReCheck ID")

	mobile_bool = fields.Boolean('Mobile Bool')
	user_id = fields.Many2one('res.users', string='User')
	user_id2 = fields.Many2one('res.users', string='User 2')

	retailer_scanned = fields.Boolean('Retailer Scanned')
	distributor_scanned = fields.Boolean('Distributor Scanned')
	employee_scanned = fields.Boolean('Employee Scanned')

	distributor_paid_bool = fields.Boolean('Amount Paid')
	distributor_paid_date = fields.Date('Paid Date')
	amount_validated = fields.Boolean('Amount Validated')
	cn_raised_date = fields.Date('CN Raised Date')

	distributor_paid_bool2 = fields.Boolean('Amount Paid 2')
	distributor_paid_date2 = fields.Date('Paid Date 2')
	amount_validated2 = fields.Boolean('Amount Validated 2')
	cn_raised_date2 = fields.Date('CN Raised Date 2')
	qr_code = fields.Binary('QR Code')

	
	def set_to_draft(self):
		self.sudo().write({'flag': False,
						'partner_id': False,
						'user_id': False,
						'state': 'create',
						'barcode_check_id': False,
						'updated_date': False,
						'updated_datetime': False,
						'second_flag': False, 
						'barcode_check2_id': False,
						'mobile_bool': False,})


	
	def generate_qr_code(self):
		qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4)
		if self.name :
			qr.add_data(self.name)
			qr.make(fit=True)
			img = qr.make_image()
			buffer = io.StringIO()
			img.save(buffer, format="PNG")
			qrcode_img = base64.b64encode(buffer.getvalue())
			self.update({'qr_code': qrcode_img,})


class barcode_marketing_check(models.Model):
	_name = "barcode.marketing.check"
	_inherit = 'mail.thread'
	_description= "QR Code Scan"
	_order = 'id desc'

	name = fields.Char('Name')
	barcode = fields.Char('Barcode')
	accepted = fields.Text('Accepted', copy=False)
	rejected = fields.Text('Rejected', copy=False)
	duplicated = fields.Text('Duplicated', copy=False)
	previously_scanned = fields.Text('Previously Scanned', copy=False)
	old_scanned = fields.Text('Old Scanned', copy=False)
	flag = fields.Boolean('Flag', copy=False)
	date = fields.Date('Date', default=lambda self: fields.datetime.today())
	partner_id = fields.Many2one('res.partner',  string="Partner")
	bp_code = fields.Char(string="Partner Code" , compute="onchange_partner_id", copy=False)
	accepted_count = fields.Char('Accepted Count', compute="onchange_accepted_data", copy=False)
	rejected_count = fields.Char('Rejected Count', compute="onchange_rejected_data", copy=False)
	duplicated_count = fields.Char('Duplicated Count', compute="onchange_duplicated_data", copy=False)
	previously_scanned_count = fields.Char('Previously Scanned Count', compute="onchange_previously_scanned_data", copy=False)
	old_scanned_count = fields.Char('Old Scanned Count', compute="onchange_old_scanned_data", copy=False)
	state = fields.Selection([('draft', 'Draft'), 
								('recheck', 'Rechecked'), 
								('create', 'Created'), 
								('update', 'Updated'), 
								('reject', 'Rejected'),
								('cn_raised', 'CN Raised'),], default='draft')
	amount= fields.Float('Coupon Worth', copy=False)
	net_amount= fields.Float('Net Coupon Worth', copy=False)
	total_amount= fields.Float('Total Coupon Worth', copy=False)
	manual_count = fields.Integer('Manual Count')
	count_accepted = fields.Integer('Accepted')
	count_rejected = fields.Char('Rejected' , related='rejected_count')
	count_duplicated = fields.Char('Duplicated' , related='duplicated_count')
	count_previously_scanned = fields.Char('Previously Scanned' , related='previously_scanned_count')
	count_old_scanned = fields.Char('Old Scanned' , related='old_scanned_count')

	charge = fields.Selection([('tr', 'Token Reimbursment'), ('scd', 'Scratch Card Discount')])
	imported = fields.Boolean('Imported', default=False)
	qrcode_image = fields.Binary("Qr Image", attachment=True)

	output_file = fields.Binary('Prepared file', filters='.xls', attachment=True, copy=False)
	export_file = fields.Char(string="Export")

	user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange',
	 default=lambda self: self.env.user)
	lines_one2many = fields.One2many('barcode.scan.lines', 'check_line_id', string='Check Lines')
	mobile_bool = fields.Boolean('Mobile Bool')
	recheck_bool = fields.Boolean('Coupon Recheck')

	def unlink(self):
		for order in self:
			# if order.state not in  ('draft','create') and self.env.uid != 1:
			if order.state not in ('draft','create') or not self.env.user.has_group('sales_meet.group_barcode_marketing_manager'):
				raise UserError(_('You can only delete Draft / Created Entries'))
		return super(barcode_marketing_check, self).unlink()

	
	def set_to_draft(self): #Set To Draft
		if self.state in ('create','recheck'): self.state = 'draft'
		else: raise Warning("Record can be set to draft only in 'Created' State")

	
	@api.onchange('partner_id')
	def onchange_partner_id(self):
		if self.partner_id:	self.bp_code = self.partner_id.bp_code
		else: self.bp_code = False


	
	def add_lines(self):
		if not self.partner_id.c_bpartner_id:
			raise Warning("Idempiere ID is missing for the Partner/Distributor !!")

		start = time.time()
		total_amount_list = []
		net_amount_list = []
		list_barcode_scan = []
		rejected_barcode_scan = []
		duplicated_barcode_scan = []
		previously_scanned_barcode = []
		old_scanned_barcode = []
		barcode_found = []
		net_amount_total = net_amount_new = net_amount_old = 0
		amount_commission_total = amount_commission_new = amount_commission_old = 0
		receipt_name = self.partner_id.name + ' (' + "{:%Y-%m-%d}".format(datetime.now()) + ')'

		if not self.output_file:
			raise Warning('Attach the Qrcode file')

		if self.state == 'draft':
			wb = open_workbook(file_contents = base64.decodestring(self.output_file))
			sheet = wb.sheets()[0]
			arrayofvalues = sheet.col_values(0, 1)

			try:
				all_barcodes = [barcode.encode('utf-8').strip() for barcode in arrayofvalues]
			except:
				all_barcodes = [str(barcode).encode('utf-8').strip() for barcode in arrayofvalues]

			barcode_accepted_list = [ x for x in all_barcodes  if x.isdigit()  ]
			# barcode_duplicated_list = list(duplicates(all_barcodes))
			# barcode_duplicated_list = [all_barcodes if arrayofvalues.count(barcode) > 1]
			barcode_duplicated_list = list(pd.Series(all_barcodes)[pd.Series(all_barcodes).duplicated()].values)
			barcode_rejected_list = [ x for x in  all_barcodes if not x.isdigit()  ]

			barcode_ids = self.env['barcode.marketing.line'].sudo().search([('name','in', barcode_accepted_list)])
			barcode_found = [x.name for x in barcode_ids]

			barcode_rejected = ','.join(map(str, [i for i in barcode_accepted_list if i not in barcode_found]  ))
			if len(barcode_rejected) != 0:	barcode_rejected_list.append(barcode_rejected)


			if not barcode_ids:	raise Warning('No Records Found. \n Check the Sheet')

			for rec in barcode_ids:
				barcode = rec.name.encode('utf-8').strip()

				if rec.flag == False:
					list_barcode_scan.append(barcode)
					
					# amount_commission = float(rec.amount) + (float(rec.amount)*10/100)
					# net_amount_list.append(rec.amount)
					# total_amount_list.append(amount_commission)
					amount_commission_new = float(rec.amount) + (float(rec.amount)* rec.handling_charge/100)
					net_amount_new = float(rec.amount)
					net_amount_list.append(net_amount_new)
					total_amount_list.append(amount_commission_new)

				elif rec.flag == True:
					if rec.barcode_marketing_id.id in (10,11) and rec.second_flag == False:
						old_scanned_barcode.append(barcode)
						amount_commission_old = float(rec.amount) + (float(rec.amount)*  rec.handling_charge/100)
						net_amount_old = float(rec.amount)
						net_amount_list.append(net_amount_old)
						total_amount_list.append(amount_commission_old)
					else:
						previously_scanned_barcode.append(barcode)

			if len(barcode_rejected_list) != 0: 
				self.count_rejected = len(barcode_rejected_list)
				self.rejected = barcode_rejected_list

			if len(old_scanned_barcode) != 0: 
				self.count_old_scanned = len(old_scanned_barcode)
				self.old_scanned = old_scanned_barcode
			
			if len(barcode_duplicated_list) != 0: 
				self.count_duplicated = len(barcode_duplicated_list)
				self.duplicated = barcode_duplicated_list

			if len(previously_scanned_barcode) != 0: 
				self.count_previously_scanned = len(previously_scanned_barcode)
				self.previously_scanned = previously_scanned_barcode

			if len(list_barcode_scan) != 0: 
				self.count_accepted = len(list_barcode_scan)
				self.accepted = list_barcode_scan
			
			self.total_amount = sum(total_amount_list)
			self.net_amount = sum(net_amount_list)
			self.state = 'create'
			self.name = receipt_name
			self.charge = 'scd'
			# self.update_records()

		if sum(total_amount_list) > 0 :
			self.send_for_approval()
			# print "---------------- Mail Sent to Aprrover - Coupon" 
		else:
			raise Warning("Total Amount is 0.0. \n Check Whether you have uploaded the same file twice. \n \
				Click on 'SUBMIT' Button once again. ")
			
		end = time.time()
		# print "------------------add_lines --- TIME---------" , end - start

	
	def recheck_records(self):
		start = time.time()
		accepted  = []
		warning_list = []
		if self.state in ('recheck','update', 'cn_raised'):
			raise Warning('You Cannot Update an already Updated/CN Raised Record.')

		if self.accepted :
			accepted = ast.literal_eval(self.accepted)
			accepted_list = [str(n).strip() for n in accepted]
			line_ids = self.env['barcode.marketing.line']

			# warning_list = [x.name for x in line_ids.sudo().search([('name','in',accepted_list), ('recheck_bool','=', True)]) ]
			# self.warning_already_scanned(warning_list, self.accepted_count)

			line_ids.sudo().search([('name','in',accepted_list), ('recheck_bool','=', False)]).write({
						'recheck_bool': True,
						'barcode_recheck_id': self.id,
						'rechecked_date': self.date,
						})

			# rechecked_date = date.today()
			# tuple_accepted_list = tuple([str(n).strip() for n in accepted])
			# self.env.cr.execute("""UPDATE barcode_marketing_line SET recheck_bool= True, \
			#  barcode_recheck_id = %s , rechecked_date='%s' WHERE name in %s """ % (self.id, rechecked_date, tuple_accepted_list))


			self.state = 'recheck'
			self.name = "Recheck Qrcode - (%s)" % (self.date)

		elif not self.rejected and not self.manual_count:
			raise Warning('No Qrcode Scanned')

		end = time.time()
		# print "----------------------------recheck_records TIME------------------------" , end - start

	def check_mobile_coupon(self, 
							coupon=False, 
							user_id=False, 
							user_type=False, 
							distributor_id=False, 
							partner_id=False):

		print("------------ check_mobile_coupon -----------", coupon, user_id, user_type, distributor_id, partner_id)

		start = time.time()
		# line_ids = self.env['barcode.marketing.line']
		data = {}
		data2 = {}

		if user_type == 'Retailer':
			retailer = True
			distributor = employee = False
			
		elif user_type == 'Distributor':
			distributor = True
			retailer = employee = False
		else:
			employee = True
			retailer = distributor = False
			
		new_coupon = self.env['barcode.marketing.line'].sudo().search([('name','=',coupon), ('flag','=', False)])
		end1 = time.time()
		print("1111111111111111111111111111111111111111111111111", new_coupon, end1 - start)

		already_scanned_coupon = self.env['barcode.marketing.line'].sudo().search([('name','=',coupon),
																				   ('flag','=', True), 
																				   ('second_flag','=', False),	
																				   ('barcode_marketing_id','in', (10,11))])

		end2 = time.time()
		print("222222222222222222222222222222222222222222222222", already_scanned_coupon, end2 - start)


		scanned_coupon = self.env['barcode.marketing.line'].sudo().search([('name','=',coupon), 
																			('flag','=', True),
																			('second_flag','=', False),	
																			('barcode_marketing_id','not in', (10,11))])

		end3 = time.time()
		print("33333333333333333333333333333333333333333333333333333333333", already_scanned_coupon, end3 - start)


			
		if new_coupon:
			print("------------new_coupon---------------")

			new_coupon.write({
							'flag': True,
							'partner_id': distributor_id,
							'user_id': user_id,
							'state': 'update',
							'updated_date': date.today(),
							'updated_datetime': datetime.now() ,
							'mobile_bool': True,
							'retailer_scanned' : retailer,
							'distributor_scanned' : distributor,
							'employee_scanned' : employee,
							})

			cn_amount_rec = new_coupon.amount + (new_coupon.amount * (new_coupon.handling_charge /100))

			resp = self.sudo().create_coupon_payment(coupon= new_coupon.name,
									   coupon_id=new_coupon.id,
									   user_id=user_id,
									   user_type=user_type,
									   distributor_id=distributor_id,
									   retailer_id=partner_id,
									   amount=new_coupon.amount,
									   cn_amount=cn_amount_rec, )

			# print resp

			data = {
					'id': new_coupon.id,
					'coupon': new_coupon.name,
					'date': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
					'distributor' : new_coupon.partner_id.name, 
					'distributor_id' : new_coupon.partner_id.id, 
					'user' : new_coupon.user_id.name, 
					'amount' : new_coupon.amount,
					'status' : resp['status'],
					'payment' : resp['payment'],
					'payment_item' : resp['payment_item'],
					'credit' :  resp['credit'],

				}
			return data

		
		elif already_scanned_coupon:
			print("-----------------already_scanned_coupon ---------------")

			already_scanned_coupon.write({
					'second_flag': True,
					'partner_id2': distributor_id,
					'user_id2': user_id,
					'mobile_bool': True,
					'scanned_date2': date.today(),
					'scanned_datetime2': datetime.now(),
					'retailer_scanned' : retailer,
					'distributor_scanned' : distributor,
					'employee_scanned' : employee,
					})

			cn_amount_rec = already_scanned_coupon.amount + (already_scanned_coupon.amount * (already_scanned_coupon.handling_charge /100))

			resp = self.create_coupon_payment(coupon= already_scanned_coupon.name,
									   coupon_id=already_scanned_coupon.id,
									   user_id=user_id,
									   user_type=user_type,
									   distributor_id=distributor_id,
									   retailer_id=partner_id,
									   amount=already_scanned_coupon.amount,
									   cn_amount=cn_amount_rec, )

			data2 = {
					'id': already_scanned_coupon.id,
					'coupon': already_scanned_coupon.name,
					'date': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
					'distributor' : already_scanned_coupon.partner_id2.name, 
					'distributor_id' : already_scanned_coupon.partner_id2.id, 
					'user' : already_scanned_coupon.user_id2.name, 
					'amount' : already_scanned_coupon.amount,

					'status' : resp['status'],
					'payment' : resp['payment'],
					'payment_item' : resp['payment_item'],
					'credit' :  resp['credit'],
				}
			return data2

		

		elif scanned_coupon:
			scanned_coupon_resp = "This Coupon " + coupon + " is already scanned "+ \
			(" by " + scanned_coupon.user_id.name if scanned_coupon.user_id else '') + \
			(" for " + scanned_coupon.partner_id.name if scanned_coupon.partner_id else '') + \
			(" at " + str(scanned_coupon.updated_date) if scanned_coupon.updated_date else '')

			return str(scanned_coupon_resp)

		else:
			print("------ Invalid Coupon. Coupon Not Present--------")
			return 'Invalid Coupon. Coupon Not Present in the system or Coupon Not Generated from Walplast'

		end = time.time()
		# print "--------------------- update_records TIME-----------------" , end - start

	def create_coupon_payment(self, 
								coupon=False, 
								coupon_id=False, 
								user_id=False, 
								user_type=False,
								distributor_id=False, 
								retailer_id=False, 
								amount=False,
								cn_amount=False):

		print("----------create_coupon_payment -------", coupon, coupon_id, user_id, distributor_id, user_type, retailer_id, amount)
		start = time.time()
		payment = self.env['wp.coupon.payment']
		credit_resp = None
		payment_mode = ''

		if user_type == 'Retailer':
			payment_ids = payment.sudo().search([('distributor_id','=',distributor_id),
												('retailer_id','=',retailer_id), 
												('status','=', 'pending')])
			status = 'pending'

			if payment_ids:
				payment_ids.amount += amount
				payment_ids.cn_amount += cn_amount
				payment_id = payment_ids.id
			else:
				
				values = {
					'created_at': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
					'amount' : amount,
					'cn_amount' : cn_amount,
					'distributor_id': distributor_id,
					'retailer_id' : retailer_id,
					'status': status,
				}

				payment_id =  payment.sudo().create(values)
				payment_id.name = 'CP/' + str(payment_id.id).zfill(4)
				payment_id = payment_id.id
			

			# print "---------- user_type == 'Retailer' -----------" , payment_id, retailer_id, coupon_id, coupon, amount

		else:
			status = 'paid'
			values2 = {
					'created_at': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
					'amount' : amount,
					'cn_amount' : cn_amount,
					'distributor_id': distributor_id,
					'retailer_id' : retailer_id,
					'status': status,
				}

			payment_id =  payment.sudo().create(values2)
			payment_id.name = 'CP/' + str(payment_id.id).zfill(4)
			payment_id = payment_id.id

			credit_resp = self.create_coupon_credit(payment_id=payment_id, 
													distributor_id=distributor_id, 
													user_type=user_type)

			# # print "UUUUUUUUUUUUUUUHHHHHHHHHHHHHHHHHHH", credit_resp

			# # print "---------- user_type == 'Distributor' -----------" , payment_id, retailer_id, coupon_id, coupon, amount

		item_id_resp = self.create_coupon_payment_item(payment_id=payment_id,
										scan_user_id=retailer_id,
										coupon_id=coupon_id,
										scan_id=coupon,
										amount=amount,
										cn_amount=cn_amount )

		payment = {
					'id': payment_id,
					'status' : status,
					'payment_mode': payment_mode or '',
					}


		return {"status": status, "payment" : payment,  
				"payment_item": item_id_resp, "credit": credit_resp,}


	def create_coupon_payment_item(self, 
								payment_id=False,
								scan_user_id=False,
								coupon_id=False,
								scan_id=False,
								amount=False,
								cn_amount=False	):

		# print "---------- create_coupon_payment_item -----------" , payment_id, scan_user_id, coupon_id, scan_id, amount

		values2 = {
			'payment_id' : payment_id,
			'created_at': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
			'amount' : amount,
			'cn_amount' : cn_amount,
			'scan_id': scan_id,
			'coupon_id': coupon_id,
			'scan_user_id' : scan_user_id,
		}

		item_id =  self.env['wp.coupon.payment.item'].sudo().create(values2)
		item_id.name = 'CPI/' + str(item_id.id).zfill(4)
		data = {'id': item_id.id,}


		return data


	def create_coupon_credit(self, 
							payment_id=False,
							user_type=False,
							distributor_id=False,
							retailer_id=False,
							payment_mode=False):

		payment = self.env['wp.coupon.payment']
		credit = self.env['wp.coupon.credit']

		if user_type == 'Retailer':

			payment_ids = payment.sudo().search([('distributor_id','=',distributor_id),
												('retailer_id','=',retailer_id), 
												('status','=', 'pending'),
												('id','=',payment_id), 
												])

			if not payment_ids:
				return 'No Pending payment found for this Distributor and Retailer'

			amount = payment_ids.amount
			cn_amount = payment_ids.cn_amount

			credit_ids = credit.sudo().search([('distributor_id','=',distributor_id), ('status','=', 'pending'),])
			if credit_ids:
				credit_ids.amount += amount
				credit_ids.cn_amount += cn_amount
				credit_id = credit_ids.id
			else:
				values = {
					'created_at': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
					'amount' : amount,
					'cn_amount' : cn_amount,
					'distributor_id': distributor_id,
					'status': 'pending',

				}

				# # print "ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss", values

				credit_ids =  credit.sudo().create(values)
				credit_id = credit_ids.id
				credit_ids.name = 'CC/' + str(credit_id).zfill(4)

			# print "---------- user_type == 'Retailer' -----------" , payment_id, payment_mode, retailer_id, distributor_id

		else:
			payment_ids = payment.sudo().search([('distributor_id','=',distributor_id), ('id','=',payment_id)])
			if not payment_ids:
				return 'No Pending payment found for this Distributor and Retailer'

			amount = payment_ids.amount
			cn_amount = payment_ids.cn_amount

			credit_ids = credit.sudo().search([('distributor_id','=',distributor_id), ('status','=', 'pending'),])
			if credit_ids:
				credit_ids.amount += amount
				credit_ids.cn_amount += cn_amount
				credit_id = credit_ids.id
			else:
				values = {
					'created_at': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
					'amount' : amount,
					'cn_amount' : cn_amount,
					'distributor_id': distributor_id,
					'status': 'pending',

				}

				credit_ids =  credit.sudo().create(values)
				credit_id = credit_ids.id
				credit_ids.name = 'CC/' + str(credit_id).zfill(4)

			# print "---------- user_type == 'Distributor' -----------" , payment_id, payment_mode, retailer_id, distributor_id

		payment_ids.write({'status': 'paid', 'coupon_credit_id': credit_id, "payment_mode" : payment_mode })
		for pmt in payment_ids:
			payment_item_ids = self.env['wp.coupon.payment.item'].sudo().search([("payment_id","=", pmt.id)])

			if payment_item_ids:
				for pi in payment_item_ids:
					pi.coupon_id.distributor_paid_bool = True
					pi.coupon_id.distributor_paid_date = date.today()
					pi.coupon_id.updated_datetime = datetime.today()


		data2 = {
				'created_at': ( datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
				'amount' : amount,
				'distributor_id': distributor_id,
				'status': 'pending',
				'payment_mode': payment_mode or '',
				'id': credit_id,
				}

		return data2

	

	
	def update_records(self):
		start = time.time()
		accepted  = []
		warning_list = []
		line_ids = self.env['barcode.marketing.line']
		if self.state in ('update', 'cn_raised'):
			raise Warning('You Cannot Update an already Updated/CN Raised Record.')

		if not self.mobile_bool:
			if not self.partner_id: raise Warning('Select a partner to link the QRcodes')
			
			if not self.charge: raise Warning('Select a Charge to the record For CN Automation')

			if not self.amount: raise Warning('Enter Coupon Worth amount')

			self.name = "Qrcode Check - %s - (%s)" % (self.partner_id.name,self.date)
			self.total_amount = ( float(self.count_accepted) + float(self.manual_count)) * float(self.amount)

			if self.manual_count and not self.accepted:
				self.state = 'update'

		if self.accepted or self.old_scanned or self.manual_count:
			if self.accepted :
				accepted = ast.literal_eval(self.accepted)
				accepted_list = [str(n).strip() for n in accepted]

				warning_list = [x.name for x in line_ids.sudo().search([('name','in', accepted_list), ('flag','=', True)]) ]
				if warning_list: self.warning_already_scanned(warning_list, len(accepted))

				barcode_ids = line_ids.sudo().search([('name','in',accepted_list), ('flag','=', False)]).sudo().write({
							'flag': True,
							'partner_id': self.partner_id.id,
							'user_id': self.user_id.id,
							'state': 'update',
							'barcode_check_id': self.id,
							'updated_date': self.date,
							'updated_datetime': datetime.now(),
							})

			if self.old_scanned :
				old_scanned = ast.literal_eval(self.old_scanned)
				old_scanned_list = [str(n).strip() for n in old_scanned]

				warning_list = [x.name for x in line_ids.sudo().search([('name','in', old_scanned_list), ('second_flag','=', True)]) ]
				if warning_list: self.warning_already_scanned(warning_list, self.old_scanned_count)

				old_scanned_barcode_ids = line_ids.sudo().search([('name','in',old_scanned_list), ('second_flag','=', False)]).write({
							'second_flag': True, 
							'barcode_check2_id': self.id,
							'partner_id2': self.partner_id.id,
							'user_id2': self.user_id.id,
							'scanned_date2': self.date,
							'scanned_datetime2': datetime.now(),})

			self.state = 'update'
				
		else:
			raise Warning('No Qrcode Scanned')

		if self.mobile_bool: self.approval_mail()

		end = time.time()
		# print "--------------------- update_records TIME-----------------" , end - start


	
	def reject_records(self): #Rollover
		if self.accepted or self.old_scanned or self.manual_count:
			if self.accepted :
				barcode_ids = self.env['barcode.marketing.line'].sudo().search([('barcode_check_id','=',self.id)]).write({
						'flag': False,
						'partner_id': False,
						'state': 'create',
						'barcode_check_id': False,
						'updated_date': False,
						})

			if self.old_scanned :
				old_barcode_ids = self.env['barcode.marketing.line'].sudo().search([('barcode_check2_id','=',self.id)]).write({
						'second_flag': False, 'barcode_check2_id': False, })

			self.state = 'create'
		else:
			raise Warning('No Qrcode Scanned or Found to Rollover')


	
	def refuse_records(self):
		accepted  = []
		if self.accepted :
			accepted = ast.literal_eval(self.accepted)
			accepted_list = [str(n).strip() for n in accepted]
			barcode_ids = self.env['barcode.marketing.line'].sudo().search([('name','in',accepted_list)]).write({
					'flag': True,
					'partner_id': self.partner_id.id,
					'state': 'reject',
					'barcode_check_id': self.id,
					'updated_date': self.date,
					})
			self.state = 'reject'

		elif not self.rejected and not self.manual_count:
			raise Warning('No Qrcode Scanned')

	def warning_already_scanned(self, warning_list, accepted_count):
		if warning_list:
			a= '\n'.join(map(str, warning_list))
			raise Warning("Some Coupons are already Scanned and Updated. \n \
				Total Coupons Repeated : %s \n \
				Total Coupons Scanned : %s \n \n \
				Following Coupons are Repeated : \n %s " % (len(warning_list), accepted_count, a))

	def test(self):
		print("Hello World")
	
	# @api.onchange('barcode')
	def onchange_name(self):
		if not self.accepted:
			list_qrcode = []
		else:
			list_qrcode = ast.literal_eval(self.accepted)
		if self.barcode :
			# barcode = int(self.barcode.encode('utf-8').strip())
			barcode = int(self.barcode)
			if barcode in list_qrcode:
				raise Warning('Same barcode scanned twice')

			if self.recheck_bool:
				barcode_ids = self.env['barcode.marketing.line'].search([('name','=',self.barcode),('recheck_bool','=',False)])
				if barcode_ids:
					list_qrcode.append(barcode)
				else:
					raise Warning('Coupon already Rechecked. Keep it seperate and submit to Sales Support Team')

			else:
				barcode_ids = self.env['barcode.marketing.line'].search([('name','=',self.barcode),('flag','=',False)])
				if barcode_ids:
					list_qrcode.append(barcode)
				else:
					raise Warning('No Coupon is available for this barcode')

			self.accepted = list_qrcode
			self.barcode = ''
			self.accepted_count = self.count_accepted = len(list_qrcode)

	def clear_records(self):
		if not self.rejected:
			rejected_barcode = []
		else:
			rejected_barcode = ast.literal_eval(self.rejected)
		if self.barcode :
			rejected_barcode.append(int(self.barcode.encode('utf-8').strip()))
			self.rejected = rejected_barcode
			self.rejected_count = len(rejected_barcode)
			self.barcode  = ''

	@api.onchange('accepted')
	def onchange_accepted_data(self):
		for res in self:
			if res.accepted :
				res.count_accepted = res.accepted_count = len(ast.literal_eval(res.accepted))
			else:
				res.count_accepted = res.accepted_count = 0
				# print "---------- count_accepted " , res.accepted_count

	
	@api.onchange('rejected')
	def onchange_rejected_data(self):
		for res in self:
			if res.rejected :
				res.rejected_count = len(ast.literal_eval(res.rejected))
			else:
				res.rejected_count = 0
			# print "---------- Rejected" , res.rejected_count

	
	@api.onchange('duplicated')
	def onchange_duplicated_data(self):
		for res in self:
			if res.duplicated :
				res.duplicated_count = len(ast.literal_eval(res.duplicated))
			else:
				res.duplicated_count = 0
				# print "---------- Duplicated" , res.duplicated_count


	
	@api.onchange('previously_scanned')
	def onchange_previously_scanned_data(self):
		for res in self:
			if res.previously_scanned :
				res.previously_scanned_count = len(ast.literal_eval(res.previously_scanned))
			else:
				res.previously_scanned_count = 0
				# print "---------- Previously Scanned" , res.previously_scanned_count

	
	@api.onchange('old_scanned')
	def onchange_old_scanned_data(self):
		for res in self:
			if res.old_scanned :
				res.old_scanned_count = len(ast.literal_eval(res.old_scanned))
			else:
				res.old_scanned_count = 0
				# print "---------- OLD Scanned" , res.old_scanned

				
	
	def send_for_approval(self):
		approver = self.env['credit.note.approver'].search([("id","!=",0)])
		if len(approver) < 1:
			raise ValidationError("Approval Config doesnot have any Approver. Configure the Approvers and Users ")

		todaydate = "{:%d-%b-%y}".format(datetime.now())
		subject = "Coupon Codes Scanned - %s ( %s )"  % (self.partner_id.name, todaydate)
		support_email = [x.approver.email for x in approver]
		email_to = ",".join(support_email)

		greeting_body = """<p>Hi Team,</p><br/>
				<p>I have submitted the Coupons from <b>%s</b> which are worth Rs. <b>%s</b>.</p><br/>
			""" % ( self.partner_id.name, self.total_amount)

		self.send_generic_mail(subject, email_to, greeting_body)


	
	def approval_mail(self):
		cn_user = self.env['credit.note.user'].search([("id","!=",0)])
		if len(cn_user) < 1:
			raise ValidationError("User Config doesnot have any user. Configure the Approvers and Users from CN Config")

		todaydate = "{:%d-%b-%y}".format(datetime.now())
		subject = "[Approved] Coupon Codes Scanned - %s ( %s )"  % (self.partner_id.name, todaydate)
		support_email = [x.user.email for x in cn_user]
		email_to = ",".join(support_email)

		greeting_body = """<p>Hi Team,</p><br/>
				<p>I have Approved the Coupons from <b>%s</b> which are worth Rs. <b>%s</b> scanned by <b>%s</b>.</p><br/>
			""" % ( self.partner_id.name, self.total_amount, self.user_id.name)

		self.send_generic_mail(subject, email_to, greeting_body)


	
	def send_generic_mail(self,subject, email_to, greeting_body):
		main_id = self.id
		email_from = self.env.user.email

		imd = self.env['ir.model.data']
		action = imd.xmlid_to_object('sales_meet.action_barcode_marketing_check_mobile')
		form_view_id = imd.xmlid_to_res_id('sales_meet.view_barcode_marketing_check_form_mobile')
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

		report_check = base_url + '/web#%s' % (url_encode({
				'model': self._name,
				'view_type': 'form',
				'id': main_id,
				'action' : action.id
			}))

		main_body = """
				<td>
					<a href="%s" target="_blank" style="-webkit-user-select: none; padding: 5px 10px; 
					font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#337ab7; 
					text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400;
					text-align: center; vertical-align: middle; cursor: pointer; 
					white-space: nowrap; background-image: none; background-color: #337ab7; 
					border: 1px solid #337ab7; margin-right: 10px;">Check Request</a>
				</td>
			""" % (report_check)

		full_body = greeting_body + main_body
		composed_mail = self.env['mail.mail'].sudo().create({
				'model': self._name,
				'res_id': main_id,
				'email_from': email_from,
				'email_to': email_to,
				'subject': subject,
				'body_html': full_body,
			})

		composed_mail.sudo().send()
		# print "------------QR Code ----------- Mail Sent to" , email_to


	def get_scan_details(self):
		uid = request.session.uid
		cr = self.env.cr

		user_id = self.env['res.users'].sudo().search_read([('id', '=', uid)], limit=1)
		draft_scan_count = self.env['barcode.marketing.check'].sudo().search_count([('user_id', '=', uid),('state', '=', 'draft')])
		create_scan_count = self.env['barcode.marketing.check'].sudo().search_count([('user_id', '=', uid),('state', '=', 'create')])
		done_scan_count = self.env['barcode.marketing.check'].sudo().search_count([('user_id', '=', uid),('state', '=', 'update')])
		cn_raised_scan_count = self.env['barcode.marketing.check'].sudo().search_count([('user_id', '=', uid),('state', '=', 'cn_raised')])
		scan_view_id = self.env.ref('sales_meet.view_barcode_marketing_check_form_mobile')
		
		if user_id:
			data = {
				'draft_scan_count': draft_scan_count,
				'create_scan_count': create_scan_count,	
				'done_scan_count': done_scan_count,	
				'cn_raised_scan_count': cn_raised_scan_count,	
				'scan_view_id': scan_view_id.id,		  
			}
			user_id[0].update(data)

		return user_id

	# 
	# def qr_code_check(self):
	# 	rejected_barcode_temp = []
	# 	img='opencv.png'

	# 	camera = cv2.VideoCapture(0)
	# 	for i in range(1):
	# 		return_value, image = camera.read()
	# 		cv2.imwrite(img, image)

	# 		data = decode(Image.open(img))
	# 		print(data)
	# 		print(data[0][0])
	# 	del(camera)

	# 
	# def qr_code_check(self):
	# 	data = decode(Image.open(self.qrcode_image))
	# 	print(data)
	# 	print(data[0][0])


class barcode_scan_lines(models.Model):
	_name = "barcode.scan.lines"
	_description= "QR Scan Lines"
	_order = 'id desc'

	name = fields.Char('Sequence No' )
	sequence_no = fields.Integer('Sequence')
	date = fields.Date('Date')
	check_line_id = fields.Many2one('barcode.marketing.check', string="Barcode Check", ondelete='cascade')
	partner_id = fields.Many2one('res.partner',  string="Partner")
	flag = fields.Boolean('Flag')
	amount= fields.Float('Coupon Worth')
	product_name = fields.Char('Product')
	state = fields.Selection(STATE, default='draft')


class wp_coupon_payment_item(models.Model):
	_name = "wp.coupon.payment.item"
	_description= "Coupon Payment Item"
	_order = 'id desc'

	name = fields.Char('Sequence No' )
	amount= fields.Float('Coupon Worth')
	cn_amount= fields.Float('CN Coupon Worth')
	created_at = fields.Datetime('Created Date')
	scan_id = fields.Char('Coupon' )
	coupon_id = fields.Many2one('barcode.marketing.line',  string="Coupon ID")
	scan_user_id = fields.Many2one('res.partner',  string="Distributor")
	payment_id = fields.Many2one('wp.coupon.payment',  string="Payment")


class wp_coupon_payment(models.Model):
	_name = "wp.coupon.payment"
	_inherit = 'mail.thread'
	_description= "Coupon Payment"
	_order = 'id desc'

	name = fields.Char('Sequence No' )
	amount= fields.Float('Total Amount')
	cn_amount= fields.Float('Total CN Amount')
	status = fields.Selection([('pending', 'Pending'), ('paid', 'Paid')], default='pending')
	coupon_credit_id = fields.Many2one('wp.coupon.credit', string="Coupon Credit", ondelete='cascade')
	distributor_id = fields.Many2one('res.partner',  string="Distributor")
	retailer_id = fields.Many2one('res.partner',  string="Retailer")
	created_at = fields.Datetime('Created Date')
	items_one2many = fields.One2many('wp.coupon.payment.item', 'payment_id', string='Payment Items')
	payment_mode = fields.Selection([('GPay', 'GPay'), ('Paytm', 'Paytm'),
									('UPI', 'UPI'), ('Cash', 'Cash')], string="Payment Mode")


class wp_coupon_credit(models.Model):
	_name = "wp.coupon.credit"
	_inherit = 'mail.thread'
	_description= "Coupon Credit"
	_order = 'id desc'

	name = fields.Char('Sequence No' )
	amount= fields.Float('Total Amount')
	cn_amount= fields.Float('Total CN Amount')
	created_at = fields.Datetime('Created Date')
	status = fields.Selection([('pending', 'Pending'), ('paid', 'Paid')], default='pending')
	distributor_id = fields.Many2one('res.partner',  string="Distributor")
	payment_one2many = fields.One2many('wp.coupon.payment', 'coupon_credit_id', string='Coupon Payment')
	imported = fields.Boolean('Imported',default=False)
	# retailer_id = fields.Many2one('res.partner',  string="Retailer")
	
