from odoo import api, fields, models, tools
from datetime import datetime, timedelta, date

class TransporterManagement(models.Model):
    _name = 'transporter.management'

    name = fields.Char("Sr. No.",readonly=1)
    truck_order_id = fields.Char("Truck Order ID",compute='compute_truck_order_id')
    plant = fields.Many2one('wp.plant',"Plant")
    order_type = fields.Selection([('Fresh',"Fresh"),('Repeat',"Repeat"),('Transferred',"Transferred"),('N/A',"N/A")],"Order Type")
    sending_location = fields.Char("Sending Location",copy=True)
    # partner_id = fields.Many2one('res.partner',"Partner")
    depot_code = fields.Many2one('transporter.customer',"Depot Code",copy=True)
    depot_desc = fields.Char("Depot Description",copy=True)
    date = fields.Date("Date",default=fields.Date.context_today)
    # transporter = fields.Many2one('res.partner',"Transporter")
    transporter = fields.Many2one('wp.transporter',"Transporter",copy=True)
    type = fields.Many2one('truck.type',"Truck Type",copy=True)
    actual_type = fields.Float("Actual Type")
    # product_code = fields.Many2one('product.product',"Product Code")
    products_transport_rel = fields.One2many('transporter.products','transporter_management',String="Product Code",copy=True)
    # sku_code = fields.Char("SKU Code")
    # bags = fields.Integer("Bags",default=0)
    # volume = fields.Char("Volume")
    order_time = fields.Many2one('transporter.order.time',"Order Time",copy=True)
    truck_reporting_time = fields.Many2one('truck.reporting.time',"Truck Reporting Time",copy=True)
    reason = fields.Char("Reason")
    status = fields.Selection([('Yes',"Yes"),('No',"No")],string="Status")
    status_updated = fields.Boolean(default=False)
    remarks = fields.Char("Updated Remarks")
    remarks_2 = fields.Char("Remarks")
    user_id = fields.Many2one('res.users',"User",default=lambda self: self.env.user)

    @api.onchange('depot_code')
    def set_depot_details(self):
        for rec in self:
            if rec.depot_code:
                rec.depot_desc = rec.depot_code.name

    @api.depends('plant','name','depot_code','date')
    def compute_truck_order_id(self):
        for rec in self:
            if rec.plant and rec.name and rec.depot_code and rec.date:
                date = datetime.strptime(str(rec.date), tools.DEFAULT_SERVER_DATE_FORMAT).strftime('%d')
                rec.truck_order_id = str(rec.plant.name) + str(rec.depot_code.bp_code) + str(date)+str(rec.name)
            else:
                rec.truck_order_id = ''

    # @api.onchange('product_code','bags')
    # def update_volume(self):
    #     for rec in self:
    #         if rec.product_code:
    #             rec.volume = rec.product_code.uom_id.weight_per_bag * rec.bags

    # @api.onchange('plant')
    @api.depends('plant')
    def update_sending_location(self):
        if self.plant:
            self.sending_location = self.plant.plant_name
        return {'domain': {'plant': [('id', '=', self.env.user.factory_id.id)]}}

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('transporter.management')
        result = super(TransporterManagement, self).create(vals)
        return result

    def send_tpr_summary_report(self):
        plants = self.env['wp.plant'].sudo().search([])
        for pl in plants:
            transporters = self.env['wp.transporter'].sudo().search([])
            body = """<table style="width: 80%; border: 1px solid;border-collapse:collapse" class="table text-center">
                        <tbody>
                        <tr style="border: 1px solid;">
                        <th style="border: 1px solid black;">Transporter</th>
                        <th style="border: 1px solid black;">Depot Desc</th>
                        <th style="border: 1px solid black;">NO</th>
                        <th style="border: 1px solid black;">YES</th>
                        <th style="border: 1px solid black;">Grand Total</th>
                        </tr>"""

            grand_total_yes = grand_total_no = 0
            for transporter in transporters:
                tpr_summary = []

                transporter_yes_count = transporter_no_count = 0
                rowspan= len(transporter.depot_ids)
                rowspan_counter = 0
                for depot in transporter.depot_ids:
                    count_yes = count_no = 0
                    plans = self.env['transporter.management'].sudo().search([('depot_code','=',depot.id),('plant','=',pl.id)])
                    for plan in plans:

                        if plan.status == "Yes":
                            count_yes +=1
                        else:
                            count_no +=1
                    if plans:
                        tpr_summary.append({
                            'depot': depot.name,
                            'count_yes':count_yes,
                            'count_no':count_no
                        })
                    transporter_no_count += count_no
                    transporter_yes_count += count_yes
                grand_total_yes += transporter_yes_count
                grand_total_no  += transporter_no_count
                if len(tpr_summary) > 0:
                    for tpr in tpr_summary:
                        if rowspan_counter == 0:
                            body += """<tr style="border: 1px solid;">
                                        <td style="border: 1px solid black;" rowspan='""" + str(len(tpr_summary)) + """' >""" + transporter.name + """</td>
                                        <td style="border: 1px solid black;">""" + tpr['depot'] + """</td>
                                        <td style="border: 1px solid black;">""" + str(tpr['count_no']) + """</td>
                                        <td style="border: 1px solid black;">""" + str(tpr['count_yes']) + """</td>
                                        <td style="border: 1px solid black;">""" + str(tpr['count_yes'] + tpr['count_no']) + """</td>
                                        </tr> """
                        else:
                            body += """<tr style="border: 1px solid;">
                                        <td style="border: 1px solid black;">""" + tpr['depot'] + """</td>
                                        <td style="border: 1px solid black;">""" + str(tpr['count_no']) + """</td>
                                        <td style="border: 1px solid black;">""" + str(tpr['count_yes']) + """</td>
                                        <td style="border: 1px solid black;">""" + str(tpr['count_yes'] + tpr['count_no']) + """</td>
                                        </tr>"""
                        rowspan_counter += 1
                    body += """<tr style="border: 1px solid;">
                               <td colspan="2" style="border: 1px solid black;">""" + transporter.name + """ Total</td>
                               <td style="border: 1px solid black;">""" + str(transporter_no_count) + """</td>
                               <td style="border: 1px solid black;">""" + str(transporter_yes_count) + """</td>
                               <td style="border: 1px solid black;">""" + str(transporter_no_count + transporter_yes_count) + """</td>
                                </tr>
                                """

            body +="""
            <tr style="border: 1px solid;">
            <td colspan="2" style="border: 1px solid black;"><b>Grand Total</b></td>
            <td style="border: 1px solid black;"><b>""" + str(grand_total_no) + """</b></td>
            <td style="border: 1px solid black;"><b>""" + str(grand_total_yes) + """</b></td>
            <td style="border: 1px solid black;"><b>""" + str(grand_total_no + grand_total_yes) + """</b></td>
            </tr>
            </tbody></table>
            """
            yes_percent = (grand_total_yes/(grand_total_no + grand_total_yes))*100 if grand_total_no+grand_total_yes > 0 else 0
            no_percent = (grand_total_no/(grand_total_no + grand_total_yes))*100 if grand_total_no+grand_total_yes > 0 else 0

            upper_body = """
            <table style="width: 35%; border: 1px solid;border-collapse:collapse" class="table text-center">
            <tr style="border: 1px solid;">
            <td style="border: 1px solid;">Total Yes %</td>
            <td style="border: 1px solid;">"""+str(float("{:.2f}".format(yes_percent)))+"""</td>
            </tr>
            <tr style="border: 1px solid;">
            <td style="border: 1px solid;">Total No %</td>
            <td style="border: 1px solid;">"""+str(float("{:.2f}".format(no_percent)))+"""</td>
            </tr>
            </table>
            <br/>
            <br/>
            """

            if grand_total_no + grand_total_yes > 0 :
                tpr_summary_email = self.env['mail.mail'].sudo().create({
                    'email_from': 'it@walplast.com',
                    'email_to': "gurnam.sharma@drychem.com,sandhya.shinde@drychem.com,akshay.parmar@mirajdrymix.com,nitish.pomendkar@drychem.com",
                    'subject': str(pl.plant_name)+"- TPR Summary Report",
                    'body_html': upper_body + body,
                })
                tpr_summary_email.send()

class TransporterProducts(models.Model):
    _name = 'transporter.products'

    product_id = fields.Many2one('product.product')
    bags = fields.Float("Bags")
    volume = fields.Float("Volume",compute='update_volume')
    transporter_management = fields.Many2one('transporter.management',"Transporter Plan")
    update_plan_id = fields.Many2one('update.planning')

    @api.depends('product_id', 'bags')
    def update_volume(self):
        for rec in self:
            if rec.product_id:
                rec.volume = rec.product_id.uom_id.weight_per_bag * rec.bags
            else:
                rec.volume = 0

