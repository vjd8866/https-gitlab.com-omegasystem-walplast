from odoo import http
from odoo.http import request
import json
import xmlrpc, xmlrpc.client
from odoo.addons.web.controllers.main import ensure_db, Session
from odoo.tools.translate import _

#
db = 'walplast_2'
url = 'walplast.in'

# db = 'walplast_2'
# url = 'http://127.0.0.32:9229'

NOT_FOUND = {'error': 'unknown_command',}

DB_INVALID = {'error': 'invalid_db',}

FORBIDDEN = {'error': 'token_invalid',}

NO_API = {'error': 'rest_api_not_supported',}

LOGIN_INVALID = {'error': 'invalid_login',}

DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'

class ResUsers(http.Controller):

    @http.route('/wmvdapi/auth', auth='none', methods=["POST"], type="json")
    def authenticate(self, login, password):
        # print "----------------- /wmvdapi/auth ---------------" , db, login, password

        try:
            mobile = ""
            request.session.authenticate(db, login, password)
            session_info = request.env['ir.http'].session_info()
            users_rec = request.env['res.users'].search([('id', '=', session_info['uid']),('active', '=', True)])
            if users_rec.wp_user_type_id.name == 'Distributor':
                distributer_id = session_info['partner_id']
                mobile = request.env['res.partner'].search([('id', '=', session_info['partner_id']),
                    ('active', '=', True)], limit=1).mobile
            elif users_rec.wp_user_type_id.name == 'Retailer':
                retailer_id = request.env['res.partner'].search([('id', '=', session_info['partner_id']),
                    ('active', '=', True)], limit=1)
                distributer_id = retailer_id.wp_distributor_id.id
                mobile = retailer_id.mobile
            else:
                distributer_id = session_info['partner_id']

            hrid = request.env['hr.employee'].sudo().search([('user_id', '=', session_info['uid']),
                                                            ('active', '=', True),
                                                            ('status','!=', 'left')], limit=1)

            data = {'id':session_info['uid'],
                    'partner_id': session_info['partner_id'],
                    # 'session_id': session_info['session_id'] ,
                    'session_id': request.session.sid,
                    'name': session_info['name'],
                    'email': session_info['username'],
                    'user_type' : users_rec.wp_user_type_id.name or "",
                    'distributor_id' : distributer_id or None,
                    'grade_id' : hrid.grade_id.id or None,
                    'grade' : hrid.grade_id.name or "",
                    'company_id': session_info['company_id'],
                    'mobile': hrid.mobile_phone or mobile,
                    'work_location' : hrid.work_location or "",
                    'work_state_id' : hrid.state_id.id or None,
                    'work_state' : hrid.state_id.name or "",
                    'designation': hrid.job_id.name or "",
                    'manager_id': hrid.parent_id.user_id.id or None,
                    'manager': hrid.parent_id.user_id.name or "",

                    }
                    # 'company_name': session_info['user_companies']['current_company'][1],

            return {'success': data, 'error': None}
        except:
            return {'success': None, 'error':'The entered Email / Password is incorrect'}


    @http.route('/wmvdapi/reset_password', auth='public', methods=["POST"], type="json")
    def reset_password(self, login):
        try:
            # print "--------- /wmvdapi/reset_password---------- " , login
            request.env['res.users'].sudo().reset_password(login)
            return {'success': 'An email has been sent with credentials to reset your password', 'error': None}
        except:
            return {'success': None, 'error': 'Invalid Email ID. EMail ID Not Present'}

    # @http.route('/wmvdapi/logout', auth='user', methods=["POST"], type="json")
    @http.route('/wmvdapi/logout', auth='public', methods=["POST"], type="json")
    def logout(self,user_id):
        try:
            # print "----------------------logout----------", user_id
            request.session.logout()
            return {'success': 'Logout Successful', 'error': None}
        except:
            return {'success': None, 'error':'Logout Failed'}      


    # @http.route(['/wmvdapi/get_users', '/wmvdapi/get_users/<int:user_id>'], methods=["POST"], type='json', auth='user')
    @http.route(['/wmvdapi/get_users', '/wmvdapi/get_users/<int:user_id>'], methods=["POST"], type='json', auth='public')
    def get_users(self, user_id=None):
        print("-------------/wmvdapi/get_users-------------------", user_id)
        if user_id:
            domain = [('id', '=', user_id),('active', '=', True)]
        else:
            domain = [('active', '=', True)]
        users_rec = request.env['res.users'].sudo().search(domain)

        if users_rec :
            users = []

            for rec in users_rec:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url_128 = base_url + '/web/image?' + 'model=res.users&id=' + str(rec.id) + '&field=image'
                vals = {
                    'id': rec.id,
                    'name': rec.name,
                    'partner_id': rec.partner_id.name,
                    'email' : rec.email,
                    'image' : image_url_128,
                    'user_type' : rec.wp_user_type_id.name
                }
                users.append(vals)
            # data = {'status': 200, 'response': users, 'message': 'User(s) returned'}
            return {'success': users, 'error': None}
        else:
            return {'success': None, 'error':'Invalid Request'}

    # @http.route(['/wmvdapi/get_partner', '/wmvdapi/get_partner/<int:partner_id>'], methods=["POST"], type='json', auth='user')
    @http.route(['/wmvdapi/get_partner', '/wmvdapi/get_partner/<int:partner_id>'], methods=["POST"], type='json', auth='public')
    def get_partner(self, partner_id=None):
        print("------------/wmvdapi/get_partner -----------", partner_id)
        if partner_id:
            domain = [('id', '=', partner_id),('active', '=', True)]
        else:
            domain = [('active', '=', True)]
        partner_rec = request.env['res.partner'].sudo().search(domain)

        if partner_rec :
            partner = []

            for rec in partner_rec:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url_128 = base_url + '/web/image?' + 'model=res.partner&id=' + str(rec.id) + '&field=image'
                vals = {
                    'id': rec.id,
                    'name': rec.name,
                    'mobile': rec.mobile,
                    'email' : rec.email,
                    'image' : image_url_128,
                    'address' : ((rec.street + ', ') if rec.street else ' ' ) + \
                                ((rec.street2+ ', ') if rec.street2 else ' ' )  + \
                                ((rec.city + ', ') if rec.city else ' ' ) + \
                                ((rec.zip + ', ') if rec.zip else ' ' ) + \
                                ((rec.state_id.name + ', ') if rec.state_id else ' ' ) + \
                                ((rec.country_id.name + ', ') if rec.country_id else ' ' )

                }
                partner.append(vals)
            # data = {'status': 200, 'response': partner, 'message': 'partner(s) returned'}
            return {'success': partner, 'error': None}
            # return data
        else:
            return {'success': None, 'error':'Invalid Request'}


    @http.route('/wmvdapi/login', auth='none', type="json")
    def login(self, **kw):
        
        xmlrpclib = xmlrpc.client
        db, login, password = http.request.env.cr.dbname, kw.get('username'), kw.get('password')
        # print "aaaaaaaaaaaaaaaaaaaaa" , url, db, login, password
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        try:
            uid = common.authenticate(db, login, password, {})
            # return json.dumps({'user_id':uid})

            # data = {'status': 200, 'user_id':uid, 'message': 'Done All users Returned'}
            # data = {'user_id':uid}
            data = uid
            return data
        except:
            return {'Error':'Invalid Request'}

    @http.route('/restfulapi/get-products', auth='none', type="http")
    def get_products(self, **kw):
        xmlrpclib = xmlrpc.client
        url, db, username, password = 'http://localhost:7900', http.request.env.cr.dbname, kw.get('username'), kw.get('password')
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        try:
            uid = common.authenticate(db, username, password, {})
            res = models.execute_kw(db, uid, password, 'product.product', 'search_read', [], {})
            return {'products':res}
        except:
            return {'Error':'Invalid Request'}


    # @http.route('/wmvdapi/get_new_users', csrf=False, type='http', methods=["GET"], token=None, auth='user')
    @http.route('/wmvdapi/get_new_users', csrf=False, type='http', methods=["GET"], token=None, auth='public')
    def get_new_users(self, **args):
        request.env.cr.execute(""" SELECT * FROM res_users where active= True  """)
        data = []
        q_result = request.env.cr.dictfetchall()
        for line in q_result:

            id_user = line.get('id')
            active = line.get('active')
            company_id = line.get('company_id')
            partner_id = line.get('partner_id')

            data.append({
                    "id_user":id_user,
                    "active":active,
                    "company_id":company_id,
                    "partner_id":partner_id
                })
        return {'response':data}



    # @http.route(['/orden_detalle', '/orden_detalle/<int:order_id>'], type='json', auth='user')
    # def orden_detalle(self, order_id=None):
    #     if order_id:
    #         domain = [('id', '=', order_id)]
    #     else:
    #         domain = []
    #     sales_rec = request.env['sale.order'].search(domain)
    #     sales = []
    #     for rec in sales_rec:
    #         vals = {
    #             'id': rec.id,
    #             'name': rec.name,
    #             'partner_id': rec.partner_id.name,
    #             'user_id': rec.user_id.name,
    #         }
    #         sales.append(vals)
    #     data = {'status': 200, 'response': sales, 'message': 'Sale(s) returned'}
    #     return data

    # @http.route('/web/session/change_password', type='json', auth="user")
    # def change_password(self, fields):
    #     new_password = operator.itemgetter('new_password')(
    #         dict(map(operator.itemgetter('name', 'value'), fields))
    #     )
    #     user = request.env.user
    #     user.check_password(new_password)
    #     return super(PasswordSecuritySession, self).change_password(fields)


    # @http.route('/api/auth', auth='none', methods=["POST"], type="json")
    # def authenticate(self, db, login, password):
    #     # print "aaaaaaaaaaaaaaaaaaaaa" , db, login, password
    #     # Before calling /api/auth, call /web?db=*** otherwise web service is not found
    #     request.session.authenticate(db, login, password)
    #     return request.env['ir.http'].session_info()


    # @http.route('/get_users', type='json', auth='user')
    # def get_users(self):
    #     print("Yes here entered")
    #     users_rec = request.env['res.users'].search([('active','=',True)])
    #     users = []
    #     for rec in users_rec:
    #         vals = {
    #             'id': rec.id,
    #             'login': rec.login,
    #             # 'partner_id': rec.partner_id,
    #         }
    #         users.append(vals)
    #     print("users List--->", users)
    #     data = {'status': 200, 'response': users, 'message': 'Done All users Returned'}
    #     return data



    # @http.route('/api/change_master_password', auth="none", type='json', methods=['POST'], csrf=False)
    # def api_change_password(self, password_old="admin", password_new=None, **kw):
    #     check_params({'password_new': password_new})
    #     try:
    #         http.dispatch_rpc('db', 'change_admin_password', [
    #             password_old,
    #             password_new])
    #         return Response(json.dumps(True,
    #             sort_keys=True, indent=4, cls=ObjectEncoder),
    #             content_type='application/json;charset=utf-8', status=200)
    #     except Exception as error:
    #         # _logger.error(error)

    #         # abort({'error': traceback.format_exc()}, status=400)
    #         return json.dumps({'Error':'Invalid Request'})



    # @http.route('/create/webpatient', type="http", auth="public", website=True)
    # def create_webpatient(self, **kw):
    #     print("Data Received.....", kw)
    #     request.env['hospital.patient'].sudo().create(kw)
    #     # doctor_val = {
    #     #     'name': kw.get('patient_name')
    #     # }
    #     # request.env['hospital.doctor'].sudo().create(doctor_val)
    #     return request.render("om_hospital.patient_thanks", {})







    # @http.route('/patient_webform', website=True, auth='user')
    # def patient_webform(self):
    #     return request.render("om_hospital.patient_webform", {})
    #
    # # Check and insert values from the form on the model <model>
    # @http.route(['/create_web_patient'], type='http', auth="public", website=True)
    # def patient_contact_create(self, **kwargs):
    #     print("ccccccccccccc")
    #     request.env['hospital.patient'].sudo().create(kwargs)
    #     return request.render("om_hospital.patient_thanks", {})



    # # Sample Controller Created
    # @http.route('/hospital/patient/', website=True, auth='user')
    # def hospital_patient(self, **kw):
    #     # return "Thanks for watching"
    #     patients = request.env['hospital.patient'].sudo().search([])
    #     return request.render("om_hospital.patients_page", {
    #         'patients': patients
    #     })

    # # Sample Controller Created
    # @http.route('/update_patient', type='json', auth='user')
    # def update_patient(self, **rec):
    #     if request.jsonrequest:
    #         if rec['id']:
    #             print("rec...", rec)
    #             patient = request.env['hospital.patient'].sudo().search([('id', '=', rec['id'])])
    #             if patient:
    #                 patient.sudo().write(rec)
    #             args = {'success': True, 'message': 'Patient Updated'}
    #     return args

    # @http.route('/create_patient', type='json', auth='user')
    # def create_patient(self, **rec):
    #     if request.jsonrequest:
    #         print("rec", rec)
    #         if rec['name']:
    #             vals = {
    #                 'patient_name': rec['name'],
    #                 'email_id': rec['email_id']
    #             }
    #             new_patient = request.env['hospital.patient'].sudo().create(vals)
    #             print("New Patient Is", new_patient)
    #             args = {'success': True, 'message': 'Success', 'id': new_patient.id}
    #     return args




    # @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    # def web_auth_reset_password(self, *args, **kw):
    #     return super(AuthSignupHomeInherit, self).web_auth_reset_password(*args, **kw)

# class PasswordSecurityHome(AuthSignupHome):
#     @http.route(
#         '/wmvdweb/reset_password',
#         type='json',
#         auth='public'
#     )
#     def web_auth_reset_password(self, *args, **kw):
#         response = super(PasswordSecurityHome, self).web_auth_reset_password(*args, **kw )
#         # qcontext = response.qcontext
#         # if 'error' not in qcontext and qcontext.get('token'):
#         #     qcontext['error'] = _("Your password has expired")
#         #     return request.render('auth_signup.reset_password', qcontext)
#         return response

