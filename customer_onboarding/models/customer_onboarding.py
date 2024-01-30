from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError , Warning, ValidationError

class CustomerOnboarding(models.Model):
    _name = 'cust.onboard'

    def set_default_country(self):
        india = self.env['res.country'].sudo().search([('name','=','India')])
        return india.id

    name = fields.Char("Name")
    email = fields.Char("Email")
    company_id = fields.Many2one('res.company',string="Company")
    contact_name = fields.Char("Contact Person Name")
    designation= fields.Char("Designation")
    contact_no = fields.Char("Contact No")
    date = fields.Date("Date",default=fields.Date.context_today)
    street1 = fields.Char("Street1")
    street2 = fields.Char("Street2")
    district_id = fields.Many2one("res.state.district", string='District')
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state',"State")
    country_id = fields.Many2one('res.country',string="Country",default=set_default_country)
    zip_code = fields.Char("Zip Code")

    costing_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Costing Submission")
    fg_sample_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"FG Sample Submission")
    cust_code_gen = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Customer Code Creation")
    vend_code_gen = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Vendor Code Creation")
    virt_dep_aggreement = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Virtual Depot Agreement")
    physic_depo_agreement = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Physical Depot Agreement")
    sale_purchase_agreement = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Sales Purchase Agreement")
    artw_prep = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Artwork Preparation by Drychem")
    pack_bag_dev = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Packing Bag Development")
    art_spec_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Artwork & Specification Submission by customer")
    mast_sample_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Master Sample Submission to QC")
    bb_supply = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Blackbox Supply by Customer")
    fg_spec = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"FG Specification - Customer Product")
    mrp = fields.Selection([('Yes',"Yes"),('No',"No"),('NA',"NA")],"MRP")
    batch_slip_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Batch Slip Submission to Plant")
    ijp_approval = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"IJP Approval")
    fg_code_create = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"FG Code Creation in ERP")
    monthly_forecast = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Monthly Forecast")
    sop_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"SOP Submission")
    prem_available = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Premix Availability by Drychem as per Plan")
    landed_price_sub = fields.Selection([('Yes',"Yes"),('No',"No"),('NA',"NA")],"Landed Price Submission to Customer")
    po_cust = fields.Selection([('Yes',"Yes"),('No',"No"),('In Process',"In Process")],"Purchase Order from Customer")
    final_status = fields.Selection([('Pending',"Pending"),('Rejected',"Rejected"),('Completed',"Completed")],default='Pending',string="Status")

    costing_sub_attach = fields.Many2many('ir.attachment','costing_attach_rel',string="Attachments")
    fg_sample_sub_attach = fields.Many2many('ir.attachment','fg_sample_attach_rel',string="Attachments")
    cust_code_gen_attach = fields.Many2many('ir.attachment','cust_code_attach_rel',string="Attachments")
    vend_code_gen_attach = fields.Many2many('ir.attachment','vend_attach_rel',string="Attachments")
    virt_dep_aggreement_attach = fields.Many2many('ir.attachment','virt_attach_rel',string="Attachments")
    physic_depo_agreement_attach = fields.Many2many('ir.attachment','physic_attach_rel',string="Attachments")
    sale_purchase_agreement_attach = fields.Many2many('ir.attachment','sale_attach_rel',string="Attachments")
    artw_prep_attach = fields.Many2many('ir.attachment','artw_attach_rel',string="Attachments")
    pack_bag_dev_attach = fields.Many2many('ir.attachment','pack_attach_rel',string="Attachments")
    art_spec_sub_attach = fields.Many2many('ir.attachment','art_attach_rel',string="Attachments")
    mast_sample_sub_attach = fields.Many2many('ir.attachment','mast_attach_rel',string="Attachments")
    bb_supply_attach = fields.Many2many('ir.attachment','bb_sup_attach_rel',string="Attachments")
    fg_spec_attach = fields.Many2many('ir.attachment','fg_spec_attach_rel',string="Attachments")
    mrp_attach = fields.Many2many('ir.attachment','mrp_attach_rel',string="Attachments")
    batch_slip_sub_attach = fields.Many2many('ir.attachment','batch_attach_rel',string="Attachments")
    ijp_approval_attach = fields.Many2many('ir.attachment','ijp_attach_rel',string="Attachments")
    fg_code_create_attach = fields.Many2many('ir.attachment','fg_code_attach_rel',string="Attachments")
    monthly_forecast_attach = fields.Many2many('ir.attachment','monthly_fore_attach_rel',string="Attachments")
    sop_sub_attach = fields.Many2many('ir.attachment','sop_attach_rel',string="Attachments")
    prem_available_attach = fields.Many2many('ir.attachment','prem_attach_rel',string="Attachments")
    landed_price_sub_attach = fields.Many2many('ir.attachment','landed_attach_rel',string="Attachments")
    po_cust_attach = fields.Many2many('ir.attachment','po_attach_rel',string="Attachments")

    costing_sub_rem = fields.Text(string="Remarks")
    fg_sample_sub_rem = fields.Text(string="Remarks")
    cust_code_gen_rem = fields.Text(string="Remarks")
    vend_code_gen_rem = fields.Text(string="Remarks")
    virt_dep_aggreement_rem = fields.Text(string="Remarks")
    physic_depo_agreement_rem = fields.Text(string="Remarks")
    sale_purchase_agreement_rem = fields.Text(string="Remarks")
    artw_prep_rem = fields.Text(string="Remarks")
    pack_bag_dev_rem = fields.Text(string="Remarks")
    art_spec_sub_rem = fields.Text(string="Remarks")
    mast_sample_sub_rem = fields.Text(string="Remarks")
    bb_supply_rem = fields.Text(string="Remarks")
    fg_spec_rem = fields.Text(string="Remarks")
    mrp_rem = fields.Text(string="Remarks")
    batch_slip_sub_rem = fields.Text(string="Remarks")
    ijp_approval_rem = fields.Text(string="Remarks")
    fg_code_create_rem = fields.Text(string="Remarks")
    monthly_forecast_rem = fields.Text(string="Remarks")
    sop_sub_rem = fields.Text(string="Remarks")
    prem_available_rem = fields.Text(string="Remarks")
    landed_price_sub_rem = fields.Text(string="Remarks")
    po_cust_rem = fields.Text(string="Remarks")

    @api.constrains('contact_no')
    def contact_no_constraint(self):
        if self.contact_no and (len(self.contact_no) != 10 or not self.contact_no.isdigit()):
            # match = re.match('^[0-9]\d{10}$', self.contact_no)
            raise ValidationError('Contact No. can be 10 digit and 0-9 only')

    def action_close(self):
        if self.final_status == 'Pending':
            self.final_status = 'Completed'
        if self.final_status == 'Rejected':
            raise UserError("Rejected customer cannot be marked as Completed !")

    def action_reject(self):
        self.final_status = 'Rejected'

    # 
    # @api.onchange('costing_sub','fg_sample_sub','cust_code_gen','vend_code_gen','virt_dep_aggreement','physic_depo_agreement','sale_purchase_agreement',
    #               'artw_prep','pack_bag_dev','art_spec_sub','mast_sample_sub','bb_supply','fg_spec','mrp','batch_slip_sub','ijp_approval',
    #               'fg_code_create','monthly_forecast','sop_sub','prem_available','landed_price_sub','po_cust')
    # def set_final_status(self):
    #     for rec in self:
    #         if rec.costing_sub and rec.costing_sub.encode('ascii', 'ignore') == 'Yes' and rec.fg_sample_sub and rec.fg_sample_sub.encode('ascii', 'ignore') == 'Yes'\
    #                 and rec.cust_code_gen and rec.cust_code_gen.encode('ascii', 'ignore') == 'Yes' and rec.landed_price_sub and \
    #                 rec.landed_price_sub.encode('ascii', 'ignore') == 'Yes' and rec.po_cust and rec.po_cust.encode('ascii', 'ignore') == 'Yes' \
    #                 and rec.sop_sub and rec.sop_sub.encode('ascii', 'ignore') == 'Yes' and rec.prem_available and rec.prem_available.encode('ascii', 'ignore') == 'Yes'\
    #                 and rec.fg_code_create and rec.fg_code_create.encode('ascii', 'ignore') == 'Yes' and rec.monthly_forecast and rec.monthly_forecast.encode('ascii', 'ignore') == 'Yes' \
    #                 and rec.ijp_approval and rec.ijp_approval.encode('ascii', 'ignore') == 'Yes' and rec.mrp and rec.mrp.encode('ascii', 'ignore') == 'Yes' and rec.batch_slip_sub\
    #                 and rec.batch_slip_sub.encode('ascii', 'ignore') == 'Yes' and rec.bb_supply and rec.bb_supply.encode('ascii', 'ignore') == 'Yes' and rec.fg_spec \
    #                 and rec.fg_spec.encode('ascii', 'ignore') == 'Yes' and rec.art_spec_sub and rec.art_spec_sub.encode('ascii', 'ignore') == 'Yes' and \
    #                 rec.mast_sample_sub and rec.mast_sample_sub.encode('ascii', 'ignore') == 'Yes' and rec.artw_prep and rec.artw_prep.encode('ascii', 'ignore') =='Yes'\
    #                 and rec.physic_depo_agreement and rec.physic_depo_agreement.encode('ascii', 'ignore') == 'Yes' and rec.sale_purchase_agreement and \
    #                 rec.sale_purchase_agreement.encode('ascii', 'ignore') == 'Yes' and rec.vend_code_gen and rec.vend_code_gen.encode('ascii', 'ignore') == 'Yes'\
    #                 and rec.virt_dep_aggreement and rec.virt_dep_aggreement.encode('ascii', 'ignore') == 'Yes' and rec.pack_bag_dev and rec.pack_bag_dev.encode('ascii', 'ignore') == 'Yes':
    #             rec.final_status = 'Processed'
    #         else:
    #             rec.final_status = 'Pending'


