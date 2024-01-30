

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta , date
from io import BytesIO
import xlwt
import xlrd
import base64
import dateutil.parser

df = '%Y-%m-%d'

class WpHrApplicantReport(models.TransientModel):
    _name = "wp.exit.process.automation.report"
    
    name = fields.Char('Name', size=256)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string="End Date")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    file_name = fields.Binary('Exit Employee Report', readonly=True)
    company_id = fields.Many2one('res.company', string='Company')
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    _sql_constraints = [
            ('check','CHECK((start_date <= end_date))',"End date must be greater then start date")  
    ]


    def action_exit_employee_report(self):
        file = BytesIO()
        self.ensure_one()
        if self.start_date and self.end_date:
            exit_employee = self.env['wp.exit.process.automation'].sudo().search([
                                                            ('dor', '>=', self.start_date), 
                                                            ('dor', '<=', self.end_date)])
            
        if (not exit_employee):
            raise Warning(_('Record Not Found'))

        status = ''
        if exit_employee :

            workbook = xlwt.Workbook(encoding='utf-8')
            worksheet = workbook.add_sheet('Exit Employee')
            datastyle = xlwt.XFStyle()
            datastyle.num_format_str = 'yyyy-mm-dd'
            fp = BytesIO()
            
            main_style = xlwt.easyxf('font: bold on, height 400; align: wrap 1, vert centre, horiz left; \
                borders: bottom thick, top thick, left thick, right thick')
            sp_style = xlwt.easyxf('font: bold on, height 350;')
            header_style = xlwt.easyxf('font: bold on, height 220; align: wrap 1,  horiz center, vertical center; \
                borders: bottom thin, top thin, left thin, right thin; \
                pattern: pattern fine_dots, fore_color white, back_color gray_ega;' )
            base_style = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin')
            base_style_gray = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; \
                pattern: pattern fine_dots, fore_color white, back_color gray_ega;')
            base_style_yellow = xlwt.easyxf('align: wrap 1; borders: bottom thin, top thin, left thin, right thin; \
                pattern: pattern fine_dots, fore_color white, back_color yellow;')

            rep_name = 'Exit Employee'
            if self.start_date and  self.end_date:
                start_date = datetime.strptime(str(self.start_date), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
                end_date = datetime.strptime(str(self.end_date), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
                if self.start_date == self.end_date:
                    rep_name = "Exit Employee(%s)" % (start_date)
                else:
                    rep_name = "Exit Employee(%s-%s)"  % (start_date, end_date)
            self.name = rep_name

            
            worksheet.write_merge(0, 1, 0, 5, self.name ,main_style)
            row_index = 2

            worksheet.row(3).height = 1000   #Sr No
                        
            worksheet.col(1).width = 6000  #'Sr. No'
            worksheet.col(2).width = 6000  #'Employee'
            worksheet.col(3).width = 6000  #'Department'
            worksheet.col(4).width = 6000  #'EmpID'
            worksheet.col(5).width = 6000  #'Company'
            worksheet.col(6).width = 6000  #'Designation'
            worksheet.col(7).width = 6000  #'Domain'
            worksheet.col(8).width = 6000  #'Grade'
            worksheet.col(9).width = 6000  #'Location'
            worksheet.col(10).width = 6000  #'Employment Status'
            worksheet.col(11).width = 6000  #'DOJ'
            worksheet.col(12).width = 6000  #'FnF Status'
            worksheet.col(13).width = 6000  #'DOR'
            worksheet.col(14).width = 6000  #'Date on which Acceptance mail sent'
            worksheet.col(15).width = 6000  #'Resignation Type'
            worksheet.col(16).width = 6000  #'Last working day'
            worksheet.col(17).width = 6000  #'Resignation intimation to HR/ Admin & IT'
            worksheet.col(18).width = 6000  #'Last Working Day (HOD)'
            worksheet.col(19).width = 6000  #'Hold Expenses & Salary'
            worksheet.col(20).width = 6000  #'Last Working Day (Attendance)'
            worksheet.col(21).width = 6000  #'Early Release'
            worksheet.col(22).width = 6000  #'Early Release Reason'
            worksheet.col(23).width = 6000  #'Exit Documents Received'
            worksheet.col(24).width = 6000  #'Exit documents submitted by employee on'
            worksheet.col(25).width = 6000  #'Exit Documents Received after 1st Reminder'
            worksheet.col(26).width = 6000  #'Exit Documents Reminder 1'
            worksheet.col(27).width = 6000  #'Exit Documents Received after 2nd Reminder'
            worksheet.col(28).width = 6000  #'Exit Documents Reminder 2'
            worksheet.col(29).width = 6000  #'Exit Documents Received after 3rd Reminder'
            worksheet.col(30).width = 6000  #'Exit Documents Reminder 3'
            worksheet.col(31).width = 6000  #'Exit Documents Reminder to employees after last day'
            worksheet.col(32).width = 6000  #'Comments'
            worksheet.col(33).width = 6000  #'Clearance From IT'
            worksheet.col(34).width = 6000  #'Comments From IT'
            worksheet.col(35).width = 6000  #'Clearance From Admin'
            worksheet.col(36).width = 6000  #'Comments From Admin'
            worksheet.col(37).width = 6000  #'Clearance From Sales Support'
            worksheet.col(38).width = 6000  #'Comments From Sales Support'
            worksheet.col(39).width = 6000  #'Clearance From Accounts'
            worksheet.col(40).width = 6000  #'Comments From Accounts'
            worksheet.col(41).width = 6000  #'Clearance From HOD/ZSM'
            worksheet.col(42).width = 6000  #'Comments From HOD/ZSM'
            worksheet.col(43).width = 6000  #'Email-id Deactivated'
            worksheet.col(44).width = 6000  #'Comments - Email Status'
            worksheet.col(45).width = 6000  #'SIM Card Status'
            worksheet.col(46).width = 6000  #'Comments - SIM Status'
            worksheet.col(47).width = 6000  #'Eligible for Farewell Lunch'
            worksheet.col(48).width = 6000  #'Mail to Manager Sent on'
            worksheet.col(49).width = 6000  #'Bill Sent to Admin On'
            worksheet.col(50).width = 6000  #'Amount paid on'
            worksheet.col(51).width = 6000  #'Eligible for Farewell Gift'
            worksheet.col(52).width = 6000  #'Mail to Admin on'
            worksheet.col(53).width = 6000  #'Farwell Gift Sent on'
            worksheet.col(54).width = 6000  #'Eligible for Farewell E-Card'
            worksheet.col(55).width = 6000  #'Farwell E-Card Sent on'
            worksheet.col(56).width = 6000  #'Eligible for Farewell Skype Call'
            worksheet.col(57).width = 6000  #'Farewell Skype Call Mail to the Team'
            worksheet.col(58).width = 6000  #'Date on which Skype call was conducted'
            worksheet.col(59).width = 6000  #'Eligible for BHR exit Interview'
            worksheet.col(60).width = 6000  #'Mail to BHR for Exit Interview'
            worksheet.col(61).width = 6000  #'Date on Which Exit Interview was conducted'
            worksheet.col(62).width = 6000  #'FnF input forwarded to payroll'
            worksheet.col(63).width = 6000  #'FnF input forwarded to payroll on'
            worksheet.col(64).width = 6000  #'File Handover to Payroll'
            worksheet.col(65).width = 6000  #'File Handover to Payroll on'
            worksheet.col(66).width = 6000  #'FnF released'
            worksheet.col(67).width = 6000  #'FnF released on'
            worksheet.col(68).width = 6000  #'Eligible for Relieving & Experience Letter'
            worksheet.col(69).width = 6000  #'Relieving & Experience letter given on'
            worksheet.col(70).width = 6000  #'Acceptance received on Relieving & Experience'
            worksheet.col(71).width = 6000  #'Relieving & Experience acceptance on'
            worksheet.col(72).width = 6000  #'Remarks'
            worksheet.col(73).width = 6000  #'Recovery in any case'
            worksheet.col(74).width = 6000  #'Recovery Reason'
            worksheet.col(75).width = 6000  #'2nd Recovery Letter via registered post shared'
            worksheet.col(76).width = 6000  #'Recovery Amount'
            worksheet.col(77).width = 6000  #'2nd Recovery Letter'
            worksheet.col(78).width = 6000  #'Recovery intimation mail to ex employee'
            worksheet.col(79).width = 6000  #'2nd Recovery Letter Receipt received on'
            worksheet.col(80).width = 6000  #'Recovery Amount Received'
            worksheet.col(81).width = 6000  #'Recovery Received amount'
            worksheet.col(82).width = 6000  #'Recovery Amount Received After 1st Reminder'
            worksheet.col(83).width = 6000  #'3rd Recovery Letter'
            worksheet.col(84).width = 6000  #'Recovery Reminder mail 1'
            worksheet.col(85).width = 6000  #'3rd Recovery Letter Receipt received on'
            worksheet.col(86).width = 6000  #'Recovery Amount Received After 2nd Reminder'
            worksheet.col(87).width = 6000  #'Recovery Status'
            worksheet.col(88).width = 6000  #'Recovery Reminder mail 2'
            worksheet.col(89).width = 6000  #'Case Forwaded to HR compliance'
            worksheet.col(90).width = 6000  #'Recovery Amount Received After 3rd Reminder'
            worksheet.col(91).width = 6000  #'Case Forwaded to HR compliance On'
            worksheet.col(92).width = 6000  #'Recovery Reminder mail 3'
            worksheet.col(93).width = 6000  #'Recovery Amount'
            worksheet.col(94).width = 6000  #'1st Recovery Letter via registered post shared'
            worksheet.col(95).width = 6000  #'Recovery Reason'
            worksheet.col(96).width = 6000  #'1st Recovery Letter via registered post'
            worksheet.col(97).width = 6000  #'Legal Notice sent by Compliance Team 1'
            worksheet.col(98).width = 6000  #'1st Recovery Letter Receipt received on'
            worksheet.col(99).width = 6000  #'Legal Notice sent by Compliance Team 2'
            worksheet.col(100).width = 6000  #'Legal Notice sent by Compliance Team 3'
            worksheet.col(101).width = 6000  #'Legal Notice sent through External Lawyer'
            worksheet.col(102).width = 6000  #'Reason for closure'
          
            # Headers
            header_fields = ['Sr. No',
                            'Employee',
                            'Department',
                            'EmpID',
                            'Company',
                            'Designation',
                            'Domain',
                            'Grade',
                            'Location',
                            'Employment Status',
                            'DOJ',
                            'FnF Status',

                            'DOR',
                            'Date on which Acceptance mail sent',
                            'Resignation Type',
                            'Last working day',
                            'Resignation intimation to HR/ Admin & IT',
                            'Last Working Day (HOD)',
                            'Hold Expenses & Salary',
                            'Last Working Day (Attendance)',
                            'Early Release',
                            'Early Release Reason',

                            'Exit Documents Received',
                            'Exit documents submitted by employee on',
                            'Exit Documents Received after 1st Reminder',
                            'Exit Documents Reminder 1',
                            'Exit Documents Received after 2nd Reminder',
                            'Exit Documents Reminder 2',
                            'Exit Documents Received after 3rd Reminder',
                            'Exit Documents Reminder 3',
                            'Exit Documents Reminder to employees after last day',
                            'Comments',

                            'Clearance From IT',
                            'Comments From IT',
                            'Clearance From Admin',
                            'Comments From Admin',
                            'Clearance From Sales Support',
                            'Comments From Sales Support',
                            'Clearance From Accounts',
                            'Comments From Accounts',
                            'Clearance From HOD/ZSM',
                            'Comments From HOD/ZSM',
                            'Email-id Deactivated',
                            'Comments - Email Status',
                            'SIM Card Status',
                            'Comments - SIM Status',

                            'Eligible for Farewell Lunch',
                            'Mail to Manager Sent on',
                            'Bill Sent to Admin On',
                            'Amount paid on',
                            'Eligible for Farewell Gift',
                            'Mail to Admin on',
                            'Farwell Gift Sent on',
                            'Eligible for Farewell E-Card',
                            'Farwell E-Card Sent on',
                            'Eligible for Farewell Skype Call',
                            'Farewell Skype Call Mail to the Team',
                            'Date on which Skype call was conducted',
                            'Eligible for BHR exit Interview',
                            'Mail to BHR for Exit Interview',
                            'Date on Which Exit Interview was conducted',

                            'FnF input forwarded to payroll',
                            'FnF input forwarded to payroll on',
                            'File Handover to Payroll',
                            'File Handover to Payroll on',
                            'FnF released',
                            'FnF released on',

                            'Eligible for Relieving & Experience Letter',
                            'Relieving & Experience letter given on',
                            'Acceptance received on Relieving & Experience',
                            'Relieving & Experience acceptance on',
                            'Remarks',

                            'Recovery in any case',
                            'Recovery Reason',
                            '2nd Recovery Letter via registered post shared',
                            'Recovery Amount',
                            '2nd Recovery Letter',
                            'Recovery intimation mail to ex employee',
                            '2nd Recovery Letter Receipt received on',
                            'Recovery Amount Received',
                            'Recovery Received amount',
                            'Recovery Amount Received After 1st Reminder',
                            '3rd Recovery Letter',
                            'Recovery Reminder mail 1',
                            '3rd Recovery Letter Receipt received on',
                            'Recovery Amount Received After 2nd Reminder',
                            'Recovery Status',
                            'Recovery Reminder mail 2',
                            'Case Forwaded to HR compliance',
                            'Recovery Amount Received After 3rd Reminder',
                            'Case Forwaded to HR compliance On',
                            'Recovery Reminder mail 3',
                            'Recovery Amount',
                            '1st Recovery Letter via registered post shared',
                            'Recovery Reason',
                            '1st Recovery Letter via registered post',
                            'Legal Notice sent by Compliance Team 1',
                            '1st Recovery Letter Receipt received on',
                            'Legal Notice sent by Compliance Team 2',
                            'Legal Notice sent by Compliance Team 3',
                            'Legal Notice sent through External Lawyer',
                            'Reason for closure',

                            ]
            row_index += 1
         
            for index, value in enumerate(header_fields):
                worksheet.write(row_index, index, value, header_style)
            row_index += 1

            count = 0
            for ee in exit_employee:
                if ee:
                   
                    count +=1
                    worksheet.write(row_index,0,count,base_style )
                    worksheet.write(row_index,1,ee.employee_id.name or '', base_style )
                    worksheet.write(row_index,2,ee.department_id.name or '', base_style )
                    worksheet.write(row_index,3,ee.emp_id or '', base_style )
                    worksheet.write(row_index,4,ee.company_id.name or '', base_style )
                    worksheet.write(row_index,5,ee.job_id.name or '', base_style )
                    worksheet.write(row_index,6,ee.domain or '', base_style )
                    worksheet.write(row_index,7,ee.grade_id.name or '', base_style )
                    worksheet.write(row_index,8,ee.location or '', base_style )
                    worksheet.write(row_index,9,ee.employment_status or '', base_style )
                    worksheet.write(row_index,10,datetime.strptime(ee.doj,df) if ee.doj else '', datastyle )
                    worksheet.write(row_index,11,ee.fnf_status or '', base_style )

                    worksheet.write(row_index,12,datetime.strptime(ee.dor,df) if ee.dor else '', datastyle )
                    worksheet.write(row_index,13,datetime.strptime(ee.date_on_which_acceptance_mail_sent,df) if ee.date_on_which_acceptance_mail_sent else '', datastyle )
                    worksheet.write(row_index,14,ee.type_of_resignation or '', base_style )

                    worksheet.write(row_index,15,datetime.strptime(ee.last_working_day,df)  if ee.last_working_day else '', datastyle )
                    worksheet.write(row_index,16,datetime.strptime(ee.resignation_intimation_to_hr_or_admin_and_it,df) if ee.resignation_intimation_to_hr_or_admin_and_it else '', datastyle )
                    worksheet.write(row_index,17,datetime.strptime(ee.last_working_day_hod,df) if ee.last_working_day_hod else '', datastyle )
                    worksheet.write(row_index,18,datetime.strptime(ee.hold_expenses_and_salary,df) if ee.hold_expenses_and_salary else '', datastyle )
                    worksheet.write(row_index,19,datetime.strptime(ee.last_working_day_attendance,df) if ee.last_working_day_attendance else '', datastyle )
                    worksheet.write(row_index,20,ee.early_release or '', base_style )
                    worksheet.write(row_index,21,ee.early_release_reason or '', base_style )

                    worksheet.write(row_index,22,ee.exit_documents_received or '', base_style )
                    worksheet.write(row_index,23,datetime.strptime(ee.exit_documents_submitted_by_employee_on,df) if ee.exit_documents_submitted_by_employee_on else '', datastyle )
                    worksheet.write(row_index,24,ee.exit_documents_received1 or '', base_style )
                    worksheet.write(row_index,25,datetime.strptime(ee.exit_documents_reminder1,df) if ee.exit_documents_reminder1 else '', datastyle )
                    worksheet.write(row_index,26,ee.exit_documents_received2 or '', base_style )
                    worksheet.write(row_index,27,datetime.strptime(ee.exit_documents_reminder2,df) if ee.exit_documents_reminder2 else '', datastyle )
                    worksheet.write(row_index,28,ee.exit_documents_received3 or '', base_style )
                    worksheet.write(row_index,29,datetime.strptime(ee.exit_documents_reminder3,df) if ee.exit_documents_reminder3 else '', datastyle )
                    worksheet.write(row_index,30,ee.exit_documents_reminder_to_employees_after_last_day or '', base_style )
                    worksheet.write(row_index,31,ee.exit_documents_comments or '', base_style )

                    worksheet.write(row_index,32,ee.clearance_pending_it or '', base_style )
                    worksheet.write(row_index,33,ee.comments_it or '', base_style )
                    worksheet.write(row_index,34,ee.clearance_pending_admin or '', base_style )
                    worksheet.write(row_index,35,ee.comments_admin or '', base_style )
                    worksheet.write(row_index,36,ee.clearance_pending_sales_support or '', base_style )
                    worksheet.write(row_index,37,ee.comments_sales_support or '', base_style )
                    worksheet.write(row_index,38,ee.clearance_pending_accounts or '', base_style )
                    worksheet.write(row_index,39,ee.comments_accounts or '', base_style )
                    worksheet.write(row_index,40,ee.clearance_pending_hod_zsm or '', base_style )
                    worksheet.write(row_index,41,ee.comments_hod_zsm or '', base_style )
                    worksheet.write(row_index,42,ee.email_id_deactivated or '', base_style )
                    worksheet.write(row_index,43,ee.comments_email or '', base_style )
                    worksheet.write(row_index,44,ee.sim_card_status or '', base_style )
                    worksheet.write(row_index,45,ee.comments_sim or '', base_style )

                    worksheet.write(row_index,46,ee.eligible_farewell_lunch or '', base_style )
                    worksheet.write(row_index,47,datetime.strptime(ee.mail_to_manager_sent_on,df) if ee.mail_to_manager_sent_on else '', datastyle )
                    worksheet.write(row_index,48,datetime.strptime(ee.bill_sent_to_admin_on,df) if ee.bill_sent_to_admin_on else '', datastyle )
                    worksheet.write(row_index,49,datetime.strptime(ee.amount_paid_on_by_admin,df) if ee.amount_paid_on_by_admin else '', datastyle )
                    worksheet.write(row_index,50,ee.eligible_farewell_gift or '', base_style )
                    worksheet.write(row_index,51,datetime.strptime(ee.mail_to_admin_on,df) if ee.mail_to_admin_on else '', datastyle )
                    worksheet.write(row_index,52,datetime.strptime(ee.farwell_gift_sent_on,df) if ee.farwell_gift_sent_on else '', datastyle )
                    worksheet.write(row_index,53,ee.eligible_farewell_ecard or '', base_style )
                    worksheet.write(row_index,54,datetime.strptime(ee.farwell_ecard_sent_on,df) if ee.farwell_ecard_sent_on else '', datastyle )
                    worksheet.write(row_index,55,ee.eligible_farewell_skype or '', base_style )
                    worksheet.write(row_index,56,datetime.strptime(ee.farewell_skype,df) if ee.farewell_skype else '', datastyle )
                    worksheet.write(row_index,57,datetime.strptime(ee.farewell_skype_date,df) if ee.farewell_skype_date else '', datastyle )
                    worksheet.write(row_index,58,ee.eligible_bhr_exit_interview or '', base_style )
                    worksheet.write(row_index,59,datetime.strptime(ee.mail_to_bhr,df) if ee.mail_to_bhr else '', datastyle )
                    worksheet.write(row_index,60,datetime.strptime(ee.exit_interview_date,df) if ee.exit_interview_date else '', datastyle )

                    worksheet.write(row_index,61,ee.fnf_input_forwarded_to_payroll or '', base_style )
                    worksheet.write(row_index,62,datetime.strptime(ee.fnf_input_forwarded_to_payroll_on,df) if ee.fnf_input_forwarded_to_payroll_on else '', datastyle )
                    worksheet.write(row_index,63,ee.file_handover_payroll or '', base_style )
                    worksheet.write(row_index,64,datetime.strptime(ee.file_handover_payroll_on,df) if ee.file_handover_payroll_on else '', datastyle )
                    worksheet.write(row_index,65,ee.fnf_released or '', base_style )
                    worksheet.write(row_index,66,datetime.strptime(ee.fnf_released_on,df) if ee.fnf_released_on else '', datastyle )
                    worksheet.write(row_index,67,ee.eligible_experience_letter or '', base_style )
                    worksheet.write(row_index,68,datetime.strptime(ee.relieving_and_experience_letter_given_on,df) if ee.relieving_and_experience_letter_given_on else '', datastyle )
                    worksheet.write(row_index,69,ee.acceptance_received or '', base_style )
                    worksheet.write(row_index,70,datetime.strptime(ee.relieving_and_experience_acceptance_on,df) if ee.relieving_and_experience_acceptance_on else '', datastyle )
                    worksheet.write(row_index,71,ee.remarks or '', base_style )
                    worksheet.write(row_index,72,ee.recovery_in_case_any or '', base_style )
                    worksheet.write(row_index,73,ee.recovery_reason or '', base_style )
                    worksheet.write(row_index,74,ee.second_recovery_letter_via_registered or '', base_style )
                    worksheet.write(row_index,75,ee.recovery_amount or '', base_style )
                    worksheet.write(row_index,76,datetime.strptime(ee.second_recovery_letter,df) if ee.second_recovery_letter else '', datastyle )
                    worksheet.write(row_index,77,datetime.strptime(ee.recovery_intimation_mail_to_ex_employee,df) if ee.recovery_intimation_mail_to_ex_employee else '', datastyle )
                    worksheet.write(row_index,78,datetime.strptime(ee.second_recovery_letter_recipt_received_on,df) if ee.second_recovery_letter_recipt_received_on else '', datastyle )
                    worksheet.write(row_index,79,ee.recovery_amount_received or '', base_style )
                    worksheet.write(row_index,80,datetime.strptime(ee.recovery_received_amount_date,df) if ee.recovery_received_amount_date else '', datastyle )
                    worksheet.write(row_index,81,ee.recovery_amount_received1 or '', base_style )
                    worksheet.write(row_index,82,datetime.strptime(ee.third_recovery_letter,df) if ee.third_recovery_letter else '', datastyle )
                    worksheet.write(row_index,83,datetime.strptime(ee.recovery_reminder_mail_1,df) if ee.recovery_reminder_mail_1 else '', datastyle )
                    worksheet.write(row_index,84,datetime.strptime(ee.third_recovery_letter_recipt_received_on,df) if ee.third_recovery_letter_recipt_received_on else '', datastyle )
                    worksheet.write(row_index,85,ee.recovery_amount_received2 or '', base_style )
                    worksheet.write(row_index,86,ee.recovery_status or '', base_style )
                    worksheet.write(row_index,87,datetime.strptime(ee.recovery_reminder_mail_2,df) if ee.recovery_reminder_mail_2 else '', datastyle )
                    worksheet.write(row_index,88,ee.case_fwd_hr_cmpl or '', base_style )
                    worksheet.write(row_index,89,ee.recovery_amount_received3 or '', base_style )
                    worksheet.write(row_index,90,datetime.strptime(ee.case_fwd_hr_cmpl_on,df) if ee.case_fwd_hr_cmpl_on else '', datastyle )
                    worksheet.write(row_index,91,datetime.strptime(ee.recovery_reminder_mail_3,df) if ee.recovery_reminder_mail_3 else '', datastyle )
                    worksheet.write(row_index,92,ee.recovery_amount_hr_cmpl or '', base_style )
                    worksheet.write(row_index,93,ee.first_recovery_letter_via_registered or '', base_style )
                    worksheet.write(row_index,94,ee.recovery_reason_hr_cmpl or '', base_style )
                    worksheet.write(row_index,95,datetime.strptime(ee.first_recovery_letter_via_registered_post,df) if ee.first_recovery_letter_via_registered_post else '', datastyle )
                    worksheet.write(row_index,96,datetime.strptime(ee.legal_notice_sent_cmpl_team1,df) if ee.legal_notice_sent_cmpl_team1 else '', datastyle )
                    worksheet.write(row_index,97,datetime.strptime(ee.first_recovery_letter_recipt_received_on,df) if ee.first_recovery_letter_recipt_received_on else '', datastyle )
                    worksheet.write(row_index,98,datetime.strptime(ee.legal_notice_sent_cmpl_team2,df) if ee.legal_notice_sent_cmpl_team2 else '', datastyle )
                    worksheet.write(row_index,99,datetime.strptime(ee.legal_notice_sent_cmpl_team3,df) if ee.legal_notice_sent_cmpl_team3 else '', datastyle )
                    worksheet.write(row_index,100,datetime.strptime(ee.legal_notice_sent_ext_lawyer,df) if ee.legal_notice_sent_ext_lawyer else '', datastyle )
                    worksheet.write(row_index,101,ee.reason_closure or '', base_style )

                    row_index += 1

            row_index +=1
            workbook.save(fp)

            out = base64.encodestring(fp.getvalue())

            self.write({'state': 'get','file_name': out,'name':self.name+'.xls'})
            return {
                'name' : 'Excel Report',
                'type': 'ir.actions.act_window',
                'res_model': 'wp.exit.process.automation.report',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
            }