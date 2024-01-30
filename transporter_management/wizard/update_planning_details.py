from odoo import models, fields, api
import datetime

DATETIME_FORMAT = "%Y-%m-%d"

class UpdatePlanningDetails(models.Model):
    _name = 'update.planning'

    def set_tpr_id(self):
        transporter_id = self._context.get('active_id')
        return transporter_id


    def fetch_trans_prod_details(self):
        transporter_id = self._context.get('active_id')
        transporter_prod = self.env['transporter.management'].sudo().search([('id','=',transporter_id)])
        prod_list=[]
        for rec in transporter_prod.products_transport_rel:
            prod_list.append((0,0,{'product_id':rec.product_id,
                                   'bags':rec.bags,
                                   'volume':rec.volume}))
        return prod_list

    def get_next_date(self):
        transporter_id = self._context.get('active_id')
        transporter_prod = self.env['transporter.management'].sudo().search([('id', '=', transporter_id)])
        if transporter_prod:
            date = datetime.datetime.strptime(transporter_prod.date,DATETIME_FORMAT) + datetime.timedelta(days=1)
            # date = date + timedelta(days=1)
            return date.date()

    status = fields.Selection([('Yes',"Yes"),('No',"No")],string="Status",required=1)
    remarks = fields.Char("Remarks")
    reason = fields.Char("Reason")
    actual_type = fields.Float("Actual Type")
    duplicate_plan = fields.Boolean("Want to repeat plan?")
    next_date = fields.Date("Select Date",default=get_next_date)
    tpr_id = fields.Many2one('transporter.management',default=set_tpr_id,copy=True)
    products_transport_rel = fields.One2many('transporter.products','update_plan_id',String="Product Code",default=fetch_trans_prod_details,copy=True)
    truck_reporting_time = fields.Many2one('truck.reporting.time',"Truck Reporting Time",copy=True)
    # update_truck_trans = fields.Boolean(compute=fetch_trans_prod_details)

    def update_planning_details(self):
        if self._context.get('active_model') == 'transporter.management':
            transporter_id = self._context.get('active_id')
            transporter_plan = self.env['transporter.management'].sudo().search([('id','=',transporter_id)])
            if transporter_plan:
                transporter_plan.status = self.status
                transporter_plan.remarks = self.remarks
                transporter_plan.reason = self.reason
                transporter_plan.actual_type = self.actual_type
                transporter_plan.status_updated = True
                transporter_plan.products_transport_rel = self.products_transport_rel

                if self.duplicate_plan:
                    # date = datetime.strptime(transporter_plan.date, DATETIME_FORMAT)
                    # date = date + timedelta(days=1)
                    transporter_order_time = self.env['transporter.order.time'].sudo().search([('days','=',transporter_plan.order_time.days),('day_no','=',int(transporter_plan.order_time.day_no) + 1)],limit=1)
                    repeated_plan = transporter_plan.copy(default={
                        'order_type': 'Repeat',
                        'date':self.next_date,
                        'order_time':transporter_order_time.id
                    })
                    return repeated_plan
                if self.status == 'Yes' and self.truck_reporting_time:
                    transporter_plan.truck_reporting_time = self.truck_reporting_time.id

