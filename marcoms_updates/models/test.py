from odoo import api, fields, models, tools,_
from odoo.exceptions import except_orm, ValidationError ,UserError
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import math
import time
from num2words import num2words
from odoo.exceptions import Warning
from odoo.tools import float_utils, float_compare ,pycompat ,email_re, email_split, email_escape_char, float_is_zero, date_utils

from odoo.tools.misc import format_date

#CRM Module Customize Part
class crm_customize(models.Model):
    _inherit = "crm.lead"

    assign_to_designer = fields.Many2one('res.users',string="Assign to Designer")
    job_number = fields.Integer('Job number',compute="_compute_remaining_date")
    show = fields.Char('Show')
    show_venue = fields.Char('Show Venue')
    show_date = fields.Date('Show Dates')
    Sales_dir = fields.Text('Sales Director Remarks')
    creative_dir = fields.Text('Creative Director Remarks')
    visual_asset1 = fields.Boolean('Brand Guidelines')
    visual_asset2 = fields.Boolean('Reference Images')
    visual_asset3 = fields.Boolean('Full Detailed Brief Available')
    visual_asset4 = fields.Boolean('Brand Assets')
    visual_asset5 = fields.Boolean('Client Mood-board')
    response1 = fields.Boolean('Online Submission')
    response2 = fields.Boolean('Print Submission')
    sequence_no = fields.Char('Brief No', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'),track_visibility="onchange")
    eval_detail1 = fields.Many2one('details.sheet',string='Client History with Marcoms')
    eval_detail2 = fields.Many2one('details.sheet',string='Scalability')
    eval_detail3 = fields.Many2one('details.sheet',string='Brand Guidelines')
    eval_detail4 = fields.Many2one('details.sheet',string='Floor Plan and Requirements')
    eval_detail5 = fields.Many2one('details.sheet',string='Client Approach Time')
    eval_detail6 = fields.Many2one('details.sheet',string='Multi Shows')
    eval_detail7 = fields.Many2one('details.sheet',string='Design Time Line')
    eval_detail8 = fields.Many2one('details.sheet',string='Account Manager % of Project Approval')
    eval_detail9 = fields.Many2one('details.sheet',string='Budget Evaluated by Sales')
    eval_detail10 = fields.Many2one('details.sheet',string='Brief Details Evaluated by Sales')
    eval_detail11 = fields.Many2one('details.sheet',string='Number Of companies Pitching')
    rate1 = fields.Char('Client History with Marcoms Rate',related='eval_detail1.rate',store=True,readonly=True)
    rate2 = fields.Char('Scalability Rate',related='eval_detail2.rate',store=True,readonly=True)
    rate3 = fields.Char('Brand Guidelines Rate',related='eval_detail3.rate',store=True,readonly=True)
    rate4 = fields.Char('Floor Plan and Requirements Rate',related='eval_detail4.rate',store=True,readonly=True)
    rate5 = fields.Char('Client Approach Time Rate',related='eval_detail5.rate',store=True,readonly=True)
    rate6 = fields.Char('Multi Shows Rate',related='eval_detail6.rate',store=True,readonly=True)
    rate7 = fields.Char('Design Time Line Rate',related='eval_detail7.rate',store=True,readonly=True)
    rate8 = fields.Char('Account Manager % of Project Approval Rate',related='eval_detail8.rate',store=True,readonly=True)
    rate9 = fields.Char('Budget Evaluated by Sales Rate',related='eval_detail9.rate',store=True,readonly=True)
    rate10 = fields.Char('Brief Details " Evaluated by Sales Rate',related='eval_detail10.rate',store=True,readonly=True)
    rate11 = fields.Char('Number Of companies Pitching Rate',related='eval_detail11.rate',store=True,readonly=True)
    rate_sum = fields.Integer('Total Points',compute="_compute_remaining_date")
    grade = fields.Char('Grade',compute="_compute_remaining_date")
    design_deadline = fields.Date('Design Deadline')
    design_complete = fields.Date('Design Completion')
    quotation_deadline = fields.Date('Quotation Deadline')
    quotation_complete = fields.Date('Quotation Completion')
    remaining_dates_design = fields.Char('Design Timeline',compute="_compute_remaining_date")
    remaining_dates = fields.Char('Quotation Timeline',compute="_compute_remaining_date")
    stand_size = fields.Char('Stand Size')
    brief_type = fields.Selection([('exhibition', 'Exhibition'), ('event', 'Segments')],string='Type of Brief')
    brief_status = fields.Selection([('approve', 'Approved'), ('reject', 'Reject')],string='Brief Status')
    document_count = fields.Integer(compute='_document_count', string='# Documents')
    Service_ids = fields.Many2many('crm.lead.service', 'crm_lead_service_rel', 'lead_id', 'tag_id', string='Services', help="Classify and analyze your lead/opportunity categories like: Training, Service")
    des_reason = fields.Text('Lost Reason Description')
    flag = fields.Boolean('flag',store=True,compute='_compute_sale_amount_total')
    team_ids = fields.Many2one('crm.team', string='Sales Team',compute='_compute_sale_amount_total')
    team1 = fields.Char('team')
    team2 = fields.Char('team')
    quotation_value = fields.Float('Quotation Value',compute="_get_quo_value")
    quotation_value2 = fields.Float('Quotation Value')
    submit_leadd = fields.Boolean('Submit Lead',default=False,copy=False)
    reason_for_lost = fields.Text('Reason For Lost')
    reason_for_cancel = fields.Text('Reason For Cancel')
    tag_ids = fields.Many2one('crm.lead.tag',string='Tags', help="Classify and analyze your lead/opportunity categories like: Training, Service")
    source_master = fields.Many2one('source.master',string="Source")
    is_oppor = fields.Boolean('print lead form from oppourtunity',default=False)
    email_from_contact = fields.Char('Contact Person Email', help="Email address of the contact", track_visibility='onchange', track_sequence=4, index=True)

    @api.multi
    def action_duplicate(self):
        self.copy(default={'type':'opportunity'})
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        # raise UserError('Duplicate is done')
        # return 

    @api.multi
    def mark_as_lost(self):
        for rec in self:
            if rec.reason_for_lost:
                rec.write({'stage_id':11})
            else:
                raise UserError(_("You should add the reason for lost field ,then click the button again"))

    @api.multi
    def mark_as_cancel(self):
        for rec in self:
            if rec.reason_for_cancel:
                rec.write({'stage_id':12})
            else:
                raise UserError(_("You should add the reason for cancel field ,then click the button again"))
            


    @api.multi
    def submit_lead(self):
        for rec in self:
            rec.submit_leadd = True
            channel_all_employees = self.env.ref('marcoms_updates.channel_all_new_leads').read()[0]
            template_new_employee = self.env.ref('marcoms_updates.email_template_data_new_leads').read()[0]
            # raise ValidationError(_(template_new_employee))
            if template_new_employee:
                # MailTemplate = self.env['mail.template']
                body_html = template_new_employee['body_html']
                subject = template_new_employee['subject']
                # raise ValidationError(_('%s %s ') % (body_html,subject))
                ids = channel_all_employees['id']
                channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                channel_id.message_post(body='Hello there are New lead generated Please Check it with name '+str(self.name), subject='New Lead',subtype='mail.mt_comment')
            

    @api.depends('sale_number','quotation_value')
    def _get_quo_value(self):
        for rec in self:
            x = 0.0
            if rec.sale_number:
                com = self.env['sale.order'].search([('opportunity_id','=',rec.id)])
                for l in com:
                    if l.quo_optional == False:
                        x = x + l.amount_total
            rec.quotation_value = x
            rec.write({'quotation_value2':x})
            # rec.write({'planned_revenue': x})

    @api.multi
    def write(self, vals):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
        # Only write the 'date_open' if no salesperson was assigned.
        if vals.get('user_id') and 'date_open' not in vals and not self.mapped('user_id'):
            vals['date_open'] = fields.Datetime.now()
        # stage change with new stage: update probability and date_closed
        if vals.get('stage_id') and 'probability' not in vals:
            vals.update(self._onchange_stage_id_values(vals.get('stage_id')))
        if vals.get('probability', 0) >= 100 or not vals.get('active', True):
            vals['date_closed'] = fields.Datetime.now()
        elif 'probability' in vals:
            vals['date_closed'] = False
        if vals.get('stage_id') == 11:
            if not self.reason_for_lost:
                raise UserError(_("You should add the reason for lost field"))
        if vals.get('stage_id') == 12:
            if not self.reason_for_cancel:
                raise UserError(_("You should add the reason for cancel field"))

        if vals.get('stage_id') == 7:
            # vals['quotation_complete'] = date.today()
            if self.sale_number:
                com = self.env['sale.order'].search([('opportunity_id','=',self.id)])
                for l in com:
                    l.write({
                        'state':'sent',
                    })
        if vals.get('stage_id') == 8:
            # vals['quotation_complete'] = date.today()
            if self.sale_number:
                com = self.env['sale.order'].search([('opportunity_id','=',self.id)])
                for l in com:
                    l.write({
                        'state':'reject',
                    })
        if vals.get('stage_id') == 5:
            if not self.assign_to_designer.id == 80 : 
                vals['design_complete'] = date.today()
                if not self.design_deadline:
                    raise ValidationError(_("You should add the Design Deadline Date"))
            if self.sale_number:
                com = self.env['sale.order'].search([('opportunity_id','=',self.id)])
                for l in com:
                    l.write({
                        'state':'draft',
                    })
        if vals.get('stage_id') == 6:
            if self.sale_number:
                com = self.env['sale.order'].search([('opportunity_id','=',self.id)])
                for l in com:
                    l.write({
                        'state':'approve',
                    })

        return super(crm_customize, self).write(vals)

    # @api.onchange('stage_id')
    # def _compute_dates(self):
    #     for rec in self:
    #         if rec.stage_id == 9:
    #             rec.quotation_deadline = date.today()

    #         if rec.stage_id == 8:
    #             rec.design_complete = date.today()


    @api.multi
    def _document_count(self):
        for each in self:
            document_ids = self.env['crm.lead.document'].sudo().search([('lead_ref', '=', each.id)])
            each.document_count = len(document_ids)

    @api.depends('order_ids')
    def _compute_sale_amount_total(self):
        for lead in self:
            total = 0.0
            nbr = 0
            company_currency = lead.company_currency or self.env.user.company_id.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent','approve','sale','reject','cancel'):
                    nbr += 1
                if order.state not in ('draft', 'sent', 'cancel'):
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.sale_number = nbr
            for x in lead.team_id.member_ids:
                if self.env.user.id == x.id:
                    lead.flag = True
                    # lead.team_ids = lead.team_id.id
                else:
                    lead.flag = False
                    # lead.team_ids = 1
            lead.team_ids = self.env['crm.team'].sudo()._get_default_team_id(user_id=self.env.uid)
            


    @api.onchange('team_ids','team_id')
    def _compute_sale_amount_total2(self):
        for rec in self:
            # use = self.env['res.users'].search([('id','=',self.env.uid)])
            # for l in use:
            #     l.write({'team_ids' : rec.team_ids.id})
            rec.team1 = rec.team_ids.name
            rec.team2 = rec.team_id.name

    @api.multi
    def next_stage_6(self):
        return {
                # 'name': _('Quotation'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'add.qty.purchase',
                'view_id': self.env.ref('marcoms_updates.add_next_stage_form').id,
                'type': 'ir.actions.act_window',
                # 'context': vals,
                'target': 'new'
            }

    # @api.multi
    # def handle_partner_assignation(self,  action='create', partner_id=False):
    #     """ Handle partner assignation during a lead conversion.
    #         if action is 'create', create new partner with contact and assign lead to new partner_id.
    #         otherwise assign lead to the specified partner_id

    #         :param list ids: leads/opportunities ids to process
    #         :param string action: what has to be done regarding partners (create it, assign an existing one, or nothing)
    #         :param int partner_id: partner to assign if any
    #         :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
    #     """
    #     partner_ids = {}
    #     for lead in self:
    #         if lead.partner_id:
    #             partner_ids[lead.id] = lead.partner_id.id
    #             continue
    #         if action == 'create':
    #             partner = lead._create_lead_partner()
    #             if partner.parent_id:
    #                 partner_id = partner.parent_id.id
    #             else:
    #                 partner_id = partner.id
    #             partner.team_id = lead.team_id
    #         if partner_id:
    #             lead.partner_id = partner_id
    #         partner_ids[lead.id] = partner_id
    #     return partner_ids

    @api.multi
    def handle_partner_assignation(self,  action='create', partner_id=False):
        """ Handle partner assignation during a lead conversion.
            if action is 'create', create new partner with contact and assign lead to new partner_id.
            otherwise assign lead to the specified partner_id

            :param list ids: leads/opportunities ids to process
            :param string action: what has to be done regarding partners (create it, assign an existing one, or nothing)
            :param int partner_id: partner to assign if any
            :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        Partners = self.env['res.partner']
        partner_ids = {}
        for lead in self:
            lead.email_from_contact = lead.email_from
            if lead.partner_id:
                partner_ids[lead.id] = lead.partner_id.id
                # continue
            # if lead.email_from:  # search through the existing partners based on the lead's email
                
            #     if Partners.search([('email', '=', lead.email_from)], limit=1):
            #         continue
            #     else:
            #         partner = lead._create_lead_partnerss()
            if action == 'create':
                partner = lead._create_lead_partner()
                if partner.parent_id:
                    partner_id = partner.parent_id.id
                else:
                    partner_id = partner.id
                partner.team_id = lead.team_id
            if action == 'exist':
                if lead.contact_name :  # search through the existing partners based on the lead's email
                    # raise UserError('test2 %s'% (lead.contact_name) )
                    if Partners.search([('email', '=', lead.email_from)], limit=1):
                        if lead.partner_id.parent_id:
                            partner_id = lead.partner_id.parent_id.id
                        else:
                            partner_id = lead.partner_id.id
                        # continue
                    else:
                        partner = lead._create_lead_partnerss()
                        if partner.parent_id:
                            partner_id = partner.parent_id.id
                        else:
                            partner_id = partner.id
                        partner.team_id = lead.team_id
            # else:
                
            if partner_id:
                lead.partner_id = partner_id
            partner_ids[lead.id] = partner_id
        return partner_ids

    @api.multi
    def _create_lead_partnerss(self):
        """ Create a partner from lead data
            :returns res.partner record
        """
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        # if self.partner_name:
        #     partner_company = Partner.create(self._create_lead_partner_data(self.partner_name, True))
        # elif self.partner_id:
        #     partner_company = self.partner_id
        # else:
        #     partner_company = None
        partner_company = Partner.browse(self.partner_id.id)
        if contact_name:
            return Partner.create(self._create_lead_partner_data(contact_name, False, partner_company.id if partner_company else False))

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [
            ('lead_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'crm.lead.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_lead_ref': '%s'}" % self.id
        }

    @api.multi
    def lead_form_print_report(self):
        return self.env.ref('marcoms_updates.lead_form_report').report_action(self) 
    
    @api.constrains('design_deadline','quotation_deadline','create_date')
    def check_inv_date(self):
        for rec in self:
            if rec.quotation_deadline and rec.design_deadline:
                if rec.design_deadline >=  rec.quotation_deadline :
                    raise ValidationError(_("Design Deadline Date Should Not Be Bigger or equal Quotation Deadline Date"))
            if rec.design_deadline:
                if rec.create_date.date() >=  rec.design_deadline :
                    raise ValidationError(_("Date of receiving Date Should Not Be Bigger or equal Design Deadline Date"))

    @api.multi
    def _compute_remaining_date(self):
        for rec in self:
            # rec.flag = self.pool.get('res.users').has_group(cr, uid, 'marcoms_updates.group_sale_top_manager') 
            if rec.design_deadline:
                delta1 = (rec.design_deadline - rec.create_date.date()).days
                rec.remaining_dates_design = delta1 + 1
            if rec.quotation_deadline and rec.design_deadline:
                delta = (rec.quotation_deadline - rec.design_deadline).days
                rec.remaining_dates = delta
            if rec.rate1 or rec.rate2 or rec.rate3 or rec.rate4 or rec.rate5 or rec.rate6 or rec.rate7 or rec.rate8 or rec.rate9 or rec.rate10 or rec.rate11 : 
                rec.rate_sum = int(rec.rate1) + int(rec.rate2) + int(rec.rate3) + int(rec.rate4) + int(rec.rate5) + int(rec.rate6) + int(rec.rate7) + int(rec.rate8) + int(rec.rate9) + int(rec.rate10) + int(rec.rate11)
                if rec.rate_sum >= 31 :
                    rec.grade = 'A'
                elif rec.rate_sum >= 19 and rec.rate_sum <= 30 :
                    rec.grade = 'B'
                elif rec.rate_sum < 19 :
                    rec.grade = 'C'
            
            x = 0
            job_obj = self.env['sale.order'].search([('lead_id','=',rec.id)])
            if job_obj:
                for l in job_obj:
                    x = x + 1
            rec.job_number = x


    # @api.multi
    # @api.onchange('eval_detail1','eval_detail2','eval_detail3','eval_detail4','eval_detail5','eval_detail6','eval_detail7','eval_detail8','eval_detail9','eval_detail10','eval_detail11')
    # def _rate_sum(self):
    #     for rec in self:
    #         rec.rate_sum = int(rec.rate1) + int(rec.rate2) + int(rec.rate3) + int(rec.rate4) + int(rec.rate5) + int(rec.rate6) + int(rec.rate7) + int(rec.rate8) + int(rec.rate9) + int(rec.rate10) + int(rec.rate11)
    #         if rec.rate_sum >= 31 :
    #             rec.grade = 'A'
    #         elif rec.rate_sum >= 19 and rec.rate_sum <= 30 :
    #             rec.grade = 'B'
    #         elif rec.rate_sum < 19 :
    #             rec.grade = 'C'


    # @api.multi
    # def _get_job_number(self):
        # x = 0
        # for rec in self:
        #     job_obj = self.env['job.estimate'].search([('lead_id','=',rec.id)])
        #     if job_obj:
        #         for l in job_obj:
        #             x = x + 1
        #     rec.job_number = x

    @api.multi
    def create_quotations(self):
        job_obj = self.env['sale.order']
        vals = {
            'default_partner_id': self.partner_id.id,
            'default_team_id':self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_lead_id': self.id,
            'default_lead_name': self.name,
            'default_opportunity_id': self.id,
            'default_project_name': self.show,
            'default_state': 'draft',
        }
        return {
                # 'name': _('Quotation'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'view_id': self.env.ref('sale.view_order_form').id,
                'type': 'ir.actions.act_window',
                'context': vals,
                'target': 'new'
            }
    
    # def quo_action_view(self):
    #     action = self.env.ref('marcoms_updates.quo_action_view_action').read()[0]
    #     return action

    
    @api.model
    def create(self, vals):
        # set up context used to find the lead's Sales Team which is needed
        # to correctly set the default stage_id
        context = dict(self._context or {})
        if vals.get('type') and not self._context.get('default_type'):
            context['default_type'] = vals.get('type')
        if vals.get('team_id') and not self._context.get('default_team_id'):
            context['default_team_id'] = vals.get('team_id')

        if vals.get('user_id') and 'date_open' not in vals:
            vals['date_open'] = fields.Datetime.now()
        if vals.get('sequence_no', _('New')) == _('New'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code('crm.lead') or 'New'   

        partner_id = vals.get('partner_id') or context.get('default_partner_id')
        onchange_values = self._onchange_partner_id_values(partner_id)
        onchange_values.update(vals)  # we don't want to overwrite any existing key
        vals = onchange_values

        # context: no_log, because subtype already handle this
        return super(crm_customize, self.with_context(context, mail_create_nolog=True)).create(vals)

class ResUsersCus(models.Model):
    _inherit = "res.users"

    team_ids = fields.Many2one('crm.team', string='Sales Team',compute='get_team_id')
    # in_sale = fields.Char('is sale',compute='get_team_id')

    @api.multi
    def get_team_id(self):
        for rec in self:
            rec.team_ids = self.env['crm.team'].sudo()._get_default_team_id(user_id=rec.id)
            # com = self.env['crm.team'].search([])
            # for l in com:
            #     if rec.in_sale == '1':
            #         break
            #     else:
            #         for x in l.member_ids:
            #             # raise UserError(_(rec.id))
            #             if x.id == rec.id :
            #                 rec.in_sale = '1'
            #                 break
                        # else:
                        #     rec.in_sale = False

class ServiceLead(models.Model):
    
    _name = "crm.lead.service"
    _description = "Lead Service"

    name = fields.Char('Name', required=True, translate=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class CRMLeadDocument(models.Model):
    _name = 'crm.lead.document'
    _description = 'CRM Documents'

    name = fields.Char(string='Document Number', required=True, copy=False, help='You can give your'
                                                                                 'Document number.')
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    lead_ref = fields.Many2one('crm.lead', invisible=1, copy=False)
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rels', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    issue_date = fields.Char(string='Issue Date', default=fields.datetime.now(), copy=False)
    active = fields.Boolean(default=True)

class CRMLeadAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_rels = fields.Many2many('crm.lead.document', 'doc_attachment_id', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)
    doc_attachs_rels = fields.Many2many('sale.order.document', 'docss_attachment_id', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)
    doc_attachs_account = fields.Many2many('account.move.document', 'docss_attachment_ids', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)
    bill_attachs_account = fields.Many2many('account.invoice.document', 'bill_attachment_ids', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)



class SaleOrderDocument(models.Model):
    _name = 'sale.order.document'
    _description = 'Sales Documents'
    
    name = fields.Char(string='Document Number', required=True, copy=False, help='You can give your'
                                                                                 'Document number.')
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    sale_ref = fields.Many2one('sale.order', invisible=1, copy=False)
    docss_attachment_id = fields.Many2many('ir.attachment', 'doc_attachs_rels', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    issue_date = fields.Char(string='Issue Date', default=fields.datetime.now(), copy=False)
    active = fields.Boolean(default=True)

class accountmoveDocument(models.Model):
    _name = 'account.move.document'
    _description = 'Journal Documents'
    
    name = fields.Char(string='Document Number', required=True, copy=False, help='You can give your'
                                                                                 'Document number.')
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    pay_ref = fields.Many2one('acount.payment', invisible=1, copy=False)
    docss_attachment_ids = fields.Many2many('ir.attachment', 'doc_attachs_account', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    issue_date = fields.Char(string='Issue Date', default=fields.datetime.now(), copy=False)
    active = fields.Boolean(default=True)

class accountinvoiceDocument(models.Model):
    _name = 'account.invoice.document'
    _description = 'Vendor bills Documents'
    
    name = fields.Char(string='Document Number', required=True, copy=False, help='You can give your'
                                                                                 'Document number.')
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    pay_ref = fields.Many2one('acount.payment', invisible=1, copy=False)
    bill_attachment_ids = fields.Many2many('ir.attachment', 'bill_attachs_account', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    issue_date = fields.Char(string='Issue Date', default=fields.datetime.now(), copy=False)
    active = fields.Boolean(default=True)


class Uom(models.Model):
    _inherit = 'uom.uom'

    show_sale = fields.Boolean('To Show in Sales')

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)
            invoicename = ''
            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                    invoicename = """Invoice %s %s : %s""" % (self.amount,'%',time.strftime('%d %m %Y'))
                else:
                    amount = self.amount
                    invoicename = """Invoice : %s""" % (time.strftime('%d %m %Y'))
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': order.partner_id.lang}
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
                so_line = sale_line_obj.create({
                    'name': invoicename,
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'tax_id': [(6, 0, tax_ids)],
                    'is_downpayment': True,
                })
                del context
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}


class SaleOrder_customize(models.Model):
    _inherit = "sale.order"


    lead_id = fields.Many2one('crm_lead',string="Opportunity Reference",invisble=True)
    lead_name = fields.Char(string="Opportunity Reference")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('approve', 'Pending Approval'),
        ('sent', 'Quotation Submittion'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    project_name = fields.Char('Show Name')
    message = fields.Text('Report Message')
    sign_man = fields.Many2one('hr.employee','Signatory Name',copy=True)
    sum_without_dis = fields.Float('Total Without Discount')
    # optional_total = fields.Float('Optional Products Total',compute="_requisition_count")
    # amount_total_venue = fields.Float('Venue Total',compute="count_discount")
    remaining_dates = fields.Char('Remaining Dates for Design',compute="message_change")
    sale_order_venue_ids = fields.One2many(
        'sale.order.venue', 'order_id', 'Venue',
        copy=True, readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_tax_venue = fields.Monetary(string='Taxes',compute="_amount_all2")
    amount_untaxed_venue = fields.Monetary(string='Untaxed Amount',compute="_amount_all2",   track_visibility='onchange', track_sequence=5)
    amount_total_venue = fields.Monetary(string='Total',compute="_amount_all2",   track_visibility='always', track_sequence=6)
    amount_tax_optional = fields.Monetary(string='Taxes',compute="_amount_all2" )
    amount_untaxed_optional = fields.Monetary(string='Untaxed Amount',compute="_amount_all2",   track_visibility='onchange', track_sequence=5)
    amount_total_optional = fields.Monetary(string='Total',compute="_amount_all2",  track_visibility='always', track_sequence=6)
    # discount_type_venue = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
    #                                            string='Discount Type', readonly=True,
    #                                            states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #                                            default='percent')
    # discount_rate_venue = fields.Float('Discount', readonly=True,
    #                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_discount_venue = fields.Monetary(string='Discount', 
                                         track_visibility='always')
    # discount_type_op = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
    #                                            string='Discount Type', readonly=True,
    #                                            states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #                                            default='percent')
    # discount_rate_op = fields.Float('Discount', readonly=True,
    #                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_discount_op = fields.Monetary(string='Discount', track_visibility='always')
    # amount_discount_op2 = fields.Float('Discount',compute='_amount_all2')
    # amount_discount_venue2 = fields.Float('Discount',compute='_amount_all2')
    # amount_untaxed2 = fields.Float('Discount',compute='_amount_all2')
    # ks_amount_discount2 = fields.Float('Discount',compute='_amount_all2')
    # Net1 = fields.Float('Discount',compute='_amount_all2')
    # amount_tax2 = fields.Float('Discount',compute='_amount_all2')
    # amount_untaxed_optional2 = fields.Float('Discount',compute='_amount_all2')
    # amount_tax_optional2 = fields.Float('Discount',compute='_amount_all2')
    # Net2 = fields.Float('Discount',compute='_amount_all2')
    # Netvat2 = fields.Float('Discount',compute='_amount_all2')
    # amount_untaxed_venue2 = fields.Float('Discount',compute='_amount_all2')
    # Net3 = fields.Float('Discount',compute='_amount_all2')
    # amount_tax_venue2 = fields.Float('Discount',compute='_amount_all2')
    # Netvat3 = fields.Float('Discount',compute='_amount_all2')
    # Netvat1 = fields.Float('Discount',compute='_amount_all2')
    # Netvat4 = fields.Float('Discount',compute='_amount_all2')
    # Net4 = fields.Float('Discount',compute='_amount_all2')
    requisition_count = fields.Integer(compute='_requisition_count', string='# Requisitions')
    contact_name = fields.Char('Contact Name',store=True,related="partner_id.name")
    comtype = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Company')],store=True,related="partner_id.company_type")
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', track_sequence=2)
    account_remark = fields.Text(string="Account Remarks")
    po_contract = fields.Boolean('LPO/Contract')
    contract_type = fields.Char('Contract Type')
    certificate_com = fields.Boolean('Completion Certificate')
    # date_today = fields.Date('today',compute='_requisition_count',invisible=True)
    partner_no = fields.Char(related="partner_id.sequence_no",store=True)
    document_count = fields.Integer(compute='_requisition_count', string='# Documents')
    pro_show = fields.Char('Quote Name')
    quo_optional = fields.Boolean('Optional Quotation')
    sec_subtotal = fields.Boolean('Section Subtotal',default=False)
    discount_value = fields.Float('Discount',compute="_amount_all")
    discount_value_op = fields.Float('Discount',compute="_amount_all2")
    discount_value_venue = fields.Float('Discount',compute="_amount_all2")
    normal_total_name = fields.Char('Main Qutation',default="Main Quotation Value")
    optional_total_name = fields.Char('Optionals',default="Optional elements")
    venue_total_name = fields.Char('Venue Charges',default="Venue charges")
    date_order = fields.Datetime(string='Order Date', required=True,readonly=False, index=True, copy=False, default=fields.Datetime.now)
    lpo_number = fields.Char('LPO Number')


    

    @api.onchange('partner_id','project_name')
    def pro_show_view(self):
        for rec in self:
            rec.pro_show = "%s@%s"%(rec.partner_id.name,rec.project_name)

    # @api.multi
    # def _document_count(self):
    #     for each in self:
    #         document_ids = self.env['sale.order.document'].sudo().search([('sale_ref', '=', each.id)])
    #         each.document_count = len(document_ids)

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [('sale_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'sale.order.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_sale_ref': '%s'}" % self.id
        }
        

    @api.multi
    def set_to_draft(self):
        self.write({
            'state':'draft',
        })


    @api.multi
    @api.onchange('project_name')
    def _get_username(self):
        for rec in self:
            if rec.project_name:
                if rec.user_id:
                    continue
                else:
                    rec.user_id = self.env.user

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            # 'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'project_name': self.project_name,
            'project': self.analytic_account_id.id,
            'LPO': self.lpo_number,
            # 'ks_global_discount_rate': self.ks_global_discount_rate,
            # 'ks_global_discount_type': self.ks_global_discount_type,
            # 'ks_amount_discount': self.ks_amount_discount,
        }
        return invoice_vals

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            # 'user_id': self.partner_id.user_id.id or self.partner_id.commercial_partner_id.user_id.id or self.env.uid
        }
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

    

    @api.multi
    # @api.depends('order_line.price_total','order_line')
    def _requisition_count(self):
        for each in self:
            document_ids = self.env['material.requisition.sales'].sudo().search([('sales_id', '=', each.id)])
            each.requisition_count = len(document_ids)
            document_idss = self.env['sale.order.document'].sudo().search([('sale_ref', '=', each.id)])
            each.document_count = len(document_idss)

            # amount_untaxed = amount_tax = 0.0
            # for line in each.order_line:
            #     amount_untaxed += line.price_subtotal
            #     amount_tax += line.price_tax
            # each.update({
            #     'amount_untaxed': amount_untaxed,
            #     'amount_tax': amount_tax,
            #     'amount_total': amount_untaxed + amount_tax,
            # })
            # if each.order_line:
            #     x = 0.0
            #     y = 0
            #     for rec in each.order_line:
            #         if rec.is_discount == True:
            #             if rec.price_unit:
            #                 x = x + abs(rec.price_subtotal)
            #             if rec.discount:
            #                 y = 1
            #                 x = (each.amount_untaxed * (rec.discount or 0.0) / 100.0)
            #                 # rec.price_subtotal = -x
            #                 rec.write({'price_subtotal':-x,'price_total':-x})
            #                 rec.update({'price_subtotal':-x,'price_total':-x})
                            
                            
            #     # each._amount_all()
            #     each.discount_value = x
                
                # each.amount_untaxed = each.amount_untaxed - x
                # # raise UserError(each.amount_untaxed)
                # each.amount_total = each.amount_untaxed + each.amount_tax

                # if y == 1:
                #     each.amount_untaxed = each.amount_untaxed - x
                #     each.amount_total = each.amount_untaxed + each.amount_tax

            # for order in self:
            
            y = 0.0
            if each.sale_order_option_ids:
                for n in each.sale_order_option_ids:
                    y = y + ((n.quantity * n.price_unit) - (n.quantity * n.price_unit) * (n.discount or 0.0) / 100.0)

                each.optional_total = y
            z = 0.0
            if each.sale_order_venue_ids:
                for n in each.sale_order_venue_ids:
                    z = z + ((n.quantity * n.price_unit) - (n.quantity * n.price_unit) * (n.discount or 0.0) / 100.0)

                each.amount_total_venue = z
            # each.date_today = date.today()
        # self.amount_change()

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:

            # if order.order_line:
            #     x = 0.0
            #     y = 0
            #     for rec in order.order_line:
            #         if rec.is_discount == True:
            #             if rec.price_unit:
            #                 x = x + abs(rec.price_subtotal)
            #             if rec.discount:
            #                 y = 1
            #                 x = (order.amount_untaxed * (rec.discount or 0.0) / 100.0)
            #                 # rec.price_subtotal = -x
            #                 rec.write({'price_subtotal':-x,'price_total':-x})
            #                 rec.update({'price_subtotal':-x,'price_total':-x})
                            
                            
            #     # each._amount_all()
            #     order.discount_value = x
            amount_untaxed = amount_tax = 0.0
            x = 0.0
            y = 0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                if line.is_discount == True:
                    if line.price_unit:
                        x = x + abs(line.price_subtotal)
                    
            
            for lines in order.order_line:
                if lines.is_discount == True and lines.discount:
                    # if order.discount_value:
                    # raise UserError(amount_untaxed)
                    if lines.discount:
                        y = 1
                        x = (amount_untaxed * (lines.discount or 0.0) / 100.0)
                        # rec.price_subtotal = -x
                        # lines.write({'price_subtotal':-x,'price_total':-x})
                        lines.update({'price_subtotal':-x,'price_total':-x})
                    amount_untaxed = amount_untaxed + lines.price_subtotal
                    # raise UserError(amount_untaxed)
            order.discount_value = x
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    # @api.multi
    # def write(self, vals):
    #     # stage change: update date_last_stage_update
        
    #     res =  super(SaleOrder_customize, self).write(vals)

    #     if self.order_line:
    #             x = 0.0
    #             y = 0
    #             for rec in self.order_line:
    #                 if rec.is_discount == True:
    #                     if rec.price_unit:
    #                         x = x + abs(rec.price_subtotal)
    #                     if rec.discount:
    #                         y = 1
    #                         x = (self.amount_untaxed * (rec.discount or 0.0) / 100.0)
    #                         # rec.price_subtotal = -x
    #                         rec.update({'price_subtotal':-x})
    #                 # # raise UserError(each.amount_untaxed)
    #                 # res['amount_total'] = 
    #     # self._amount_all()
    #     return res
    # @api.onchange('order_line')
    # def _amount_dis(self):
    #     """
    #     Compute the total amounts of the SO.
    #     """
    #     for order in self:
    #         for rec in order.order_line:
    #             if rec.discount: 
    #                 x = (order.amount_untaxed * (rec.discount or 0.0) / 100.0)
    #                 rec.price_subtotal = -x
    
    # @api.multi
    # @api.depends('discount_value')
    # def amount_change(self):
    #     for rec in self:
    #         rec.amount_untaxed = rec.amount_untaxed - rec.discount_value
            # raise UserError(rec.amount_untaxed)
    #     for order in self:
    #         amount_untaxed = amount_tax = amount_total = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #         amount_total = amount_untaxed + line.price_tax
    #         # vals['amount_untaxed'] = amount_untaxed
    #         # vals['amount_tax'] = amount_tax
    #         # vals['amount_total'] = amount_total
    #         order.update({
    #             'amount_untaxed': amount_untaxed,
    #             'amount_tax': amount_tax,
    #             'amount_total': amount_total,
    #         })

        # return super(SaleOrder_customize, self).write(vals)

    @api.multi
    def requisition_view(self):
        self.ensure_one()
        task_id = []
        for res in self:
            for line in res.order_line: 
                if line.display_type == 'line_section' or line.display_type == 'line_note':
                    continue
                else:
                    data = {
                        'product_id':line.product_id.id,
                                'description':line.name,
                                'qty':line.product_uom_qty,
                                'uom_id':line.product_uom.id
                    }
                    task_id.append((0,0,data))
            
            domain = [
                ('sales_id', '=', res.id)]
            vals = {
                'default_sales_id': res.id,
                'default_oppor_id': res.opportunity_id.id,
                'default_partner_id': res.partner_id.id,
                'default_show_name': res.project_name,
                'default_state': 'new',
                'default_requisition_line_ids': task_id,
            }
        return {
            'name': _('Requisition'),
            'domain': domain,
            'res_model': 'material.requisition.sales',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create New Price Inquiry
                        </p>'''),
            'limit': 80,
            'context': vals,
        }

    

    @api.multi
    def create_purchase_requisition_from_sales(self):
        
        purchase_req_obj = self.env['material.requisition.sales']
        # purchase_req_line_obj = self.env['material.requisition.sales.line']
        for res in self:
            task_id = []
            for line in res.order_line: 
                if line.display_type == 'line_section' or line.display_type == 'line_note':
                    continue
                else:
                    data = {
                        'product_id':line.product_id.id,
                                'description':line.name,
                                'qty':line.product_uom_qty,
                                'uom_id':line.product_uom.id
                    }
                    task_id.append((0,0,data))
            purchase_req_obj.create({
                                    'sales_id': res.id,
                                    'oppor_id': res.opportunity_id.id,
                                    'partner_id': res.partner_id.id,
                                    'show_name': res.project_name,
                                    'state':'draft',
                                    'requisition_line_ids': task_id,
                                    })
         
            
            
                # req_line_vals = purchase_req_line_obj.create({
                #     'product_id':line.product_id.id,
                #     'description':line.name,
                #     'product_qty':line.product_uom_qty,
                #     'product_uom_id':line.product_uom.id,
                #     'requisition_id':req_vals.id,
                #     })

    # @api.multi
    # def ks_calculate_discount(self):
    #     for rec in self:
    #         if rec.ks_global_discount_type == "amount":
    #             rec.ks_amount_discount = rec.ks_global_discount_rate if rec.amount_untaxed > 0 else 0

    #         elif rec.ks_global_discount_type == "percent":
    #             if rec.ks_global_discount_rate != 0.0:
    #                 rec.ks_amount_discount = rec.amount_untaxed  * rec.ks_global_discount_rate / 100
    #             else:
    #                 rec.ks_amount_discount = 0
    #         rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.ks_amount_discount

    @api.depends('sale_order_venue_ids','sale_order_option_ids')
    # @api.onchange('sale_order_venue_ids','sale_order_option_ids')
    def _amount_all2(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            # if order.discount_rate_op or order.discount_rate_venue:
            amount_untaxed = amount_tax = total = dis_venue = disc3 = disc4 = dis = 0.0
            if order.sale_order_venue_ids:
                x = 0.0
                for line in order.sale_order_venue_ids:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                    
                    if line.is_discount == True:
                        if line.price_unit:
                            x = x + abs(line.price_subtotal)
                for lines in order.sale_order_venue_ids:
                    if lines.is_discount == True and lines.discount:
                        x = (amount_untaxed * (lines.discount or 0.0) / 100.0)
                        # rec.price_subtotal = -x
                        # lines.write({'price_subtotal':-x,'price_total':-x})
                        lines.update({'price_subtotal':-x,'price_total':-x})
                        amount_untaxed = amount_untaxed + lines.price_subtotal
                total = amount_untaxed + amount_tax
                order.discount_value_venue = x
                # for rec in each.order_line:
                    
                
            # if order.discount_type_venue == 'percent':
            #     # dis = (total - total * (order.discount_rate_venue or 0.0) / 100.0)
            #     disc3 = (amount_untaxed - amount_untaxed * (order.discount_rate_venue or 0.0) / 100.0)
            #     disc4 = amount_untaxed - disc3
            #     dis = total - disc4
            #     dis_venue = amount_untaxed  - (dis - amount_tax)
            #     order.update({
            #         'amount_untaxed_venue': amount_untaxed,
            #         'amount_tax_venue': amount_tax,
            #         'amount_discount_venue': disc4,
            #         'amount_total_venue': dis,
            #     })
            # else:
            # order.update({
                
            # })

            amount_untaxed2 = amount_tax2 = total2 = dis_venue2 = disc = disc2 = dis2 = 0.0
            if order.sale_order_option_ids:
                y = 0.0
                for line in order.sale_order_option_ids:
                    amount_untaxed2 += line.price_subtotal
                    amount_tax2 += line.price_tax
                    # total2 = amount_untaxed2 + amount_tax2
                    if line.is_discount == True:
                        if line.price_unit:
                            y = y + abs(line.price_subtotal)
                for lines in order.sale_order_option_ids:
                    if lines.is_discount == True and lines.discount:
                        y = (amount_untaxed2 * (lines.discount or 0.0) / 100.0)
                        # rec.price_subtotal = -x
                        # lines.write({'price_subtotal':-x,'price_total':-x})
                        lines.update({'price_subtotal':-y,'price_total':-y})
                        amount_untaxed2 = amount_untaxed2 + lines.price_subtotal
                total2 = amount_untaxed2 + amount_tax2
                order.discount_value_op = y
                    
            # if order.discount_type_op == 'percent':
            #     # dis2 = (total2 - total2 * (order.discount_rate_op or 0.0) / 100.0)
            #     disc = (amount_untaxed2 - amount_untaxed2 * (order.discount_rate_op or 0.0) / 100.0)
            #     disc2 = amount_untaxed2 - disc
            #     dis2 = total2 - disc2
            #     dis_venue2 = amount_untaxed2  - (dis2 - amount_tax2)
            #     order.update({
            #         'amount_untaxed_optional': amount_untaxed2,
            #         'amount_tax_optional': amount_tax2,
            #         'amount_discount_op': disc2,
            #         'amount_total_optional': dis2,
            #     })
            # else:
            order.update({
                'amount_untaxed_optional': amount_untaxed2,
                'amount_tax_optional': amount_tax2,
                # 'amount_discount_op': order.discount_rate_op,
                'amount_total_optional': total2,
                'amount_untaxed_venue': amount_untaxed,
                'amount_tax_venue': amount_tax,
                # 'amount_discount_venue': order.discount_rate_venue,
                'amount_total_venue': total ,
            })
        
            # net1 = net2 = net3 = 0.0
            # net1 = order.amount_untaxed - order.ks_amount_discount
            # net2 = order.amount_untaxed_optional - order.amount_discount_op
            # net3 = order.amount_untaxed_venue - order.amount_discount_venue
            # Netvat1 = order.amount_tax + net1
            # Netvat2 = order.amount_tax_optional + net2
            # Netvat3 = order.amount_tax_venue + net3
            # order.update({
            #         'amount_discount_op2': order.amount_discount_op,
            #         'amount_discount_venue2': order.amount_discount_venue,
            #         'amount_untaxed2': order.amount_untaxed,
            #         'ks_amount_discount2': order.ks_amount_discount,
            #         'Net1': net1,
            #         'amount_tax2': order.amount_tax,
            #         'amount_untaxed_optional2': order.amount_untaxed_optional,
            #         'amount_tax_optional2': order.amount_tax_optional,
            #         'Net2': net2,
            #         'Netvat2': Netvat2,
            #         'amount_untaxed_venue2': order.amount_untaxed_venue,
            #         'Net3': net3,
            #         'amount_tax_venue2': order.amount_tax_venue,
            #         'Netvat3': Netvat3,
            #         'Netvat1': Netvat1,
            #         'Net4': net1 + net2 + net3,
            #         'Netvat4': Netvat1 + Netvat2 + Netvat3,
            #     })

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('marcoms_updates', 'email_template_edi_sale2')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
            


    

    # @api.multi
    # @api.depends('validity_date')
    # @api.onchange('validity_date')
    # def _compute_remaining_date(self):
    #     for rec in self:
    #         if rec.validity_date:
    #             tod = date.today()
    #             delta1 = (rec.validity_date - tod).days
    #             rec.remaining_dates = delta1
    #         else:
    #             rec.remaining_dates = ' '

    @api.multi
    @api.onchange('partner_id','project_name','remaining_dates','validity_date')
    def message_change(self):
        for rec in self:
            if rec.validity_date:
                tod = date.today()
                delta1 = (rec.validity_date - tod).days
                rec.remaining_dates = delta1
            else:
                rec.remaining_dates = ' '
            # raise UserError(_(rec.comtype))
            # if rec.comtype == 'company':
            rec.message = """Dear All,

Thank you for providing us with the opportunity to quote on building your stand %s@%s As per the brief and scope of work, we are enclosing here with our preliminary quotation for your consideration.

Attached you can find the stand design with specifications.

If all is in order, let us know how and when you wish to proceed. As discussed earlier. We can offer you
an assurance of our policy of best quality and sensible prices with prompt and professional services.
Please note that the prices offered in this quotation are valid for %s days from the time of receipt. Please
call us if you have any questions or require additional information.

Sincerely,"""  % (rec.partner_id.name, rec.project_name, rec.remaining_dates)
#             else:
            
#                 rec.message = """Dear All,

# Thank you for providing us with the opportunity to quote on building your stand %s@%s As per the brief and scope of work, we are enclosing here with our preliminary quotation for your
# consideration.

# Attached you can find the stand design with specifications.

# If all is in order, let us know how and when you wish to proceed. As discussed earlier. We can offer you
# an assurance of our policy of best quality and sensible prices with prompt and professional services.
# Please note that the prices offered in this quotation are valid for %s days from the time of receipt. Please
# call us if you have any questions or require additional information.

# Sincerely,"""  % (rec.partner_id.parent_id.name, rec.project_name, rec.remaining_dates)

    # @api.multi
    # def count_discount(self):
    #     for rec in self:
    #         # x = 0.0
    #         # for l in rec.order_line:
    #         #     x = x + (l.product_uom_qty * l.price_unit)

    #         # rec.sum_without_dis = x
    #         y = 0.0
    #         for n in rec.sale_order_option_ids:
    #             y = y + ((n.quantity * n.price_unit) - (n.quantity * n.price_unit) * (n.discount or 0.0) / 100.0)

    #         rec.optional_total = y
    #         z = 0.0
    #         for n in rec.sale_order_venue_ids:
    #             z = z + ((n.quantity * n.price_unit) - (n.quantity * n.price_unit) * (n.discount or 0.0) / 100.0)

    #         rec.amount_total_venue = z

    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()

        sale_order = self.env['sale.order'].search([('opportunity_id','=',self.opportunity_id.id)])
        job_obj = self.env['crm.lead'].search([('id','=',self.opportunity_id.id)])
        if job_obj:
            for sale in sale_order:
                if sale.state == 'sale':
                    for k in job_obj:
                        k.write({'stage_id': 9})
                else:
                    for l in job_obj:
                        l.write({'stage_id': 13,'probability':70})


        channel_all_employees = self.env.ref('marcoms_updates.channel_all_confirmed_sales').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_confirm_sales').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            channel_id.message_post(body='Hello, New Confirmed sale order Please Check Sale order '+str(self.name), subject='Confirmed Sale Order',subtype='mail.mt_comment')
                
        return True


    @api.multi
    def action_to_approve(self):
        job_obj = self.env['crm.lead'].search([('id','=',self.opportunity_id.id)])
        if job_obj:
            for k in job_obj:
                k.write({'stage_id': 6}) 
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_pending_approvals').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_pending_approvals').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """Hello, Quotation with number %s waiting for your approval"""% (self.name)
            channel_id.message_post(body=body, subject='Sales Pending Approval',subtype='mail.mt_comment')
        return self.write({'state': 'approve'})

    @api.multi
    def action_to_Reject(self):
        job_obj = self.env['crm.lead'].search([('id','=',self.opportunity_id.id)])
        if job_obj:
            for k in job_obj:
                k.write({'stage_id': 8}) 
        return self.write({'state': 'reject'})

    @api.multi
    def action_approved(self):
        job_obj = self.env['crm.lead'].search([('id','=',self.opportunity_id.id)])
        
        if job_obj:
            for k in job_obj:
                k.write({'stage_id': 7}) 
        com = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        return self.write({'state': 'sent'})

class SaleAdvancePaymentInvcus(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = order.fiscal_position_id.map_account(self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id).id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        del context
        taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'account_analytic_id': order.analytic_account_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id,
            # 'comment': order.note,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice
        


class SaleOrderOptioncus(models.Model):
    _inherit = "sale.order.option"

    product_id = fields.Many2one('product.product', 'Product', default=2, domain=[('sale_ok', '=', True)])
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id'], store=True, string='Currency', readonly=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    product_name = fields.Char(string='Product')
    is_discount = fields.Boolean(string='Is Discount')
    image_pro = fields.Binary('Product Image')
    name = fields.Text('Description')

    @api.multi
    def action_duplicate(self):
         self.copy(default={'order_id':self.order_id.id})

    @api.onchange('product_id', 'uom_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        product = self.product_id.with_context(lang=self.order_id.partner_id.lang)
        self.price_unit = product.list_price
        # self.name = product.get_product_multiline_description_sale()
        self.uom_id = self.uom_id or product.uom_id
        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        # If company_id is set, always filter taxes by the company
        taxes = self.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
        self.tax_id = fpos.map_tax(taxes, self.product_id, self.order_id.partner_shipping_id) if fpos else taxes
        pricelist = self.order_id.pricelist_id
        if pricelist and product:
            partner_id = self.order_id.partner_id.id
            self.price_unit = pricelist.with_context(uom=self.uom_id.id).get_product_price(product, self.quantity, partner_id)
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}

    

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.quantity, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def add_option_to_order(self):
        self.ensure_one()

        sale_order = self.order_id

        if sale_order.state not in ['draft', 'sent']:
            raise UserError(_('You cannot add options to a confirmed order.'))

        values = self._get_values_to_add_to_order()
        order_line = self.env['sale.order.line'].create(values)
        # order_line._compute_tax_id()

        self.write({'line_id': order_line.id})

    @api.multi
    def _get_values_to_add_to_order(self):
        self.ensure_one()
        tax = []
        for x in self.tax_id:
            tax.append(x.id)
        return {
            'order_id': self.order_id.id,
            'price_unit': self.price_unit,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'discount': self.discount,
            'image_pro': self.image_pro,
            'product_name': self.product_name,
            'is_discount': self.is_discount,
            'company_id': self.order_id.company_id.id,
            'tax_id':[(6, 0, tax)],
        }


class SaleOrderVenue(models.Model):
    _name = "sale.order.venue"
    _description = "Sale Venue"
    _order = 'sequence, id'

    order_id = fields.Many2one('sale.order', 'Sales Order Reference', ondelete='cascade', index=True)
    line_id = fields.Many2one('sale.order.line', on_delete="set null")
    name = fields.Text('Description')
    product_id = fields.Many2one('product.product', 'Product', default=2, domain=[('sale_ok', '=', True)])
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'))
    discount = fields.Float('Discount (%)', digits=dp.get_precision('Discount'))
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=True)
    quantity = fields.Float('Quantity', required=True, digits=dp.get_precision('Product UoS'), default=1)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of optional products.")
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id'], store=True, string='Currency', readonly=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    product_name = fields.Char(string='Product')
    is_discount = fields.Boolean(string='Is Discount')
    image_pro = fields.Binary('Product Image')

    @api.multi
    def action_duplicate(self):
         self.copy(default={'order_id':self.order_id.id})

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.quantity, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })


    @api.onchange('product_id', 'uom_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        product = self.product_id.with_context(lang=self.order_id.partner_id.lang)
        self.price_unit = product.list_price
        # self.name = product.get_product_multiline_description_sale()
        self.uom_id = self.uom_id or product.uom_id
        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        # If company_id is set, always filter taxes by the company
        taxes = self.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
        self.tax_id = fpos.map_tax(taxes, self.product_id, self.order_id.partner_shipping_id) if fpos else taxes
        pricelist = self.order_id.pricelist_id
        if pricelist and product:
            partner_id = self.order_id.partner_id.id
            self.price_unit = pricelist.with_context(uom=self.uom_id.id).get_product_price(product, self.quantity, partner_id)
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}

    # @api.multi
    # def _compute_tax_id(self):
    #     for line in self:
            

    @api.multi
    def button_add_to_order(self):
        self.add_option_to_order()
        # return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.multi
    def add_option_to_order(self):
        self.ensure_one()

        sale_order = self.order_id

        if sale_order.state not in ['draft', 'sent']:
            raise UserError(_('You cannot add options to a confirmed order.'))

        values = self._get_values_to_add_to_order()
        order_line = self.env['sale.order.line'].create(values)
        # order_line._compute_tax_id()

        self.write({'line_id': order_line.id})

    @api.multi
    def _get_values_to_add_to_order(self):
        self.ensure_one()
        tax = []
        for x in self.tax_id:
            tax.append(x.id)
        return {
            'order_id': self.order_id.id,
            'price_unit': self.price_unit,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
            'discount': self.discount,
            'image_pro': self.image_pro,
            'product_name': self.product_name,
            'is_discount': self.is_discount,
            'company_id': self.order_id.company_id.id,
            'tax_id':[(6, 0, tax)],
        }

class protemplateCus(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        for vals in vals_list:
            tools.image_resize_images(vals)
        templates = super(protemplateCus, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates.with_context(create_from_tmpl=True).create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in pycompat.izip(templates, vals_list):
            related_vals = {}
            if vals.get('barcode'):
                related_vals['barcode'] = vals['barcode']
            if vals.get('default_code'):
                related_vals['default_code'] = vals['default_code']
            if vals.get('standard_price'):
                related_vals['standard_price'] = vals['standard_price']
            if vals.get('volume'):
                related_vals['volume'] = vals['volume']
            if vals.get('weight'):
                related_vals['weight'] = vals['weight']
            # Please do forward port
            if vals.get('packaging_ids'):
                related_vals['packaging_ids'] = vals['packaging_ids']
            if related_vals:
                template.write(related_vals)

        channel_all_employees = self.env.ref('marcoms_updates.channel_all_new_product').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_new_product').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            if templates['default_code']:
                body = """Hello, there is new product created with name %s and code %s"""% (templates['name'],templates['default_code'])
            else:
                body = """Hello, there is new product created with name %s """% (templates['name'])
            channel_id.message_post(body=body, subject='New Product Created',subtype='mail.mt_comment')

        return templates

class evaluation_sheet(models.Model):
    _name = "evaluation.sheet"

    name = fields.Char('Type')
    description = fields.Char('Description')
    details_id = fields.One2many('details.sheet','detail_id',string='Details')

    @api.depends('name')
    def _name_detail(self):
        for rec in self:
            rec.details_id.detail_id = rec.id

class details_sheet(models.Model):
    _name = "details.sheet"

    detail_id = fields.Char(string="type",invisible=True)
    name = fields.Char('Code')
    description = fields.Char('Description')
    rate =  fields.Char('Rate')
#CRM Module Customize Part
# $?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$???$?$?$?$?$?$?$?$?$$??$?$?$$?$?$?$?$?$?$$?$$??$?
#product image partion
class SaleOrderLinecus(models.Model):
    _inherit = 'sale.order.line'

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], default=2, ondelete='restrict')
    product_name = fields.Char(string='Product')
    image_pro = fields.Binary('Product Image')
    is_space = fields.Boolean('Is space')
    name = fields.Text(string='Description', required=False)
    is_discount = fields.Boolean(string='Is Discount')
    # select = fields.Boolean('Select',default=False)
    sale_order_venue_ids = fields.One2many('sale.order.venue', 'line_id', 'Venue Lines')
    # price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal',readonly=False,  store=True)


    @api.multi
    def add_space(self):
        self.create({'order_id':self.order_id.id,'display_type':'line_section','is_space':True})

    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the SO line.
    #     """
    #     for line in self:
    #         if not line.is_discount and not line.discount:
    #             price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #             taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
    #             line.update({
    #                 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #                 'price_total': taxes['total_included'],
    #                 'price_subtotal': taxes['total_excluded'],
    #             })

    # @api.depends('price_unit', 'discount')
    # def _get_price_reduce(self):
    #     for line in self:
    #         if not line.is_discount and not line.discount:
    #             line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)

    @api.onchange('product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    
            
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav.product_attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        # name = self.get_sale_order_line_multiline_description_sale(product)

        # vals.update(name=name)

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result

    @api.multi
    def action_duplicate(self):
         self.copy(default={'order_id':self.order_id.id})

class SaleOrdercus(models.Model):
    _inherit = 'sale.order'

    image_product = fields.Binary('Project Image')
#product image partion

# $?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$?$???$?$?$?$?$?$?$?$?$$??$?$?$$?$?$?$?$?$?$$?$$??$?
#HR Contract and Payroll Customize Part
class Hrcontractscus(models.Model):
    _inherit = 'hr.contract'

    hr_allowance_line_ids = fields.One2many('hr.allowance.line','contract_id',string='HR Allowance')
    hr_total_wage = fields.Float('Total Salary',compute="_total_wage")

    @api.multi
    def _total_wage(self):
        for rec in self:
            x = rec.wage
            for l in rec.hr_allowance_line_ids:
                x = x + l.amt
            rec.hr_total_wage = x


class HRallowanceLine(models.Model):
    _name = 'hr.allowance.line'

    contract_id = fields.Many2one('hr.contract')
    rule_type = fields.Many2one('hr.salary.rule',string="Allowance Rule")
    code = fields.Char('Code',related="rule_type.code",store=True,readonly=True)
    amt = fields.Float('Amount')

class HRpayrolltran(models.Model):
    _name = 'hr.payroll.transactions'

    state = fields.Selection(string='Status', selection=[
        ('draft','New'),
        ('confirm','Waiting Approval'),
        ('accepted','Approved'),
        ('done','Done'),
        ('paid','Paid'),
        ('cancelled','Refused')],
        copy=False, index=True, readonly=True,default="draft")
    date_from = fields.Date('Date')
    date_to = fields.Date('To')
    date = fields.Date('Date')
    name = fields.Char('Description')
    payroll_tran_line = fields.One2many('hr.payroll.transactions.line','payroll_tran_id',string='Payroll Transactions')

    @api.multi
    def unlink(self):
        for line in self:
            if line.state in ['paid', 'done']:
                raise UserError(_('Cannot delete a transaction which is in state \'%s\'.') % (line.state,))
        return super(HRpayrolltran, self).unlink()

    @api.multi
    def loans_confirm(self):
        for rec in self:
            for l in rec.payroll_tran_line:
                l.state = 'accepted'
        return self.write({'state': 'done'})

    @api.multi
    def loans_accept(self):
        return self.write({'state': 'done'})

    @api.multi
    def loans_refuse(self):
        return self.write({'state': 'cancelled'})

    @api.multi
    def loans_set_draft(self):
        return self.write({'state': 'draft'})
            

class HRpayrolltranLine(models.Model):
    _name = 'hr.payroll.transactions.line'

    payroll_tran_id = fields.Many2one('hr.payroll.transactions')
    employee_id = fields.Many2one('hr.employee',string="Employee",required=True)
    timesheet_cost = fields.Float('Timesheet Cost')
    number_of_hours = fields.Float('No of Hours')
    tran_note = fields.Char('Transaction')
    allowance = fields.Float('Allowance')
    deduction = fields.Float('Deduction')
    payroll_item = fields.Many2one('hr.salary.rule',string="Payroll Item",required=True)
    analytic_account = fields.Many2one('account.analytic.account',string="Analytic Account")
    state = fields.Selection(string='Status', selection=[
        ('draft','New'),
        ('cancelled','Refused'),
        ('confirm','Waiting Approval'),
        ('accepted','Approved'),
        ('done','Waiting Payment'),
        ('paid','Paid')],readonly=True)

    @api.onchange('number_of_hours')
    def _get_amount(self):
        for rec in self:
            rec.timesheet_cost = rec.employee_id.timesheet_cost
            rec.allowance = rec.number_of_hours * rec.timesheet_cost

class HrSalaryRulecus(models.Model):
    _inherit = 'hr.salary.rule'

    od_payroll_item = fields.Boolean('Payroll Item',default=False)

class HrPayslipcus(models.Model):
    _inherit = 'hr.payslip'

    hr_variance_line_id = fields.One2many('hr.variance.line','payslip_id',string="Variance")

    @api.multi
    def unlink(self):
        for rec in self:
            if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
                raise UserError(_('You cannot delete a payslip which is not draft or cancelled!'))
            if rec.state == 'draft':
                if rec.hr_variance_line_id:
                    raise UserError(_('You cannot delete a payslip which have payroll transaction(Variance)!'))
        return super(HrPayslipcus, self).unlink()

class HrVarianceLine(models.Model):
    _name = 'hr.variance.line'

    payslip_id = fields.Many2one('hr.payslip')
    tran_id = fields.Many2one('hr.payroll.transactions',string="Transaction")
    rule_id = fields.Many2one('hr.salary.rule',string="Rule")
    date_value = fields.Date('Date')
    tran_note = fields.Char('Transaction Note')
    amount = fields.Float('Amount')

class HrPayslipEmployeescus(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        # add payroll transaction
        
        datas = {}
        obj = self.env['hr.payroll.transactions'].search([('date_from','>=',from_date),('date_from','<=',to_date)])
        # add payroll transaction
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            # add payroll transaction
            invoice_line = []
            for l in obj:
                if l.state == 'done':
                    for k in l.payroll_tran_line:
                        if k.state != 'paid':
                            if k.employee_id.id == employee.id :
                                datas = {
                                    'tran_id':l.id,
                                    'rule_id':k.payroll_item.id,
                                    'date_value':l.date_from,
                                    'tran_note':k.tran_note,
                                    'amount':k.allowance,
                                }
                                invoice_line.append((0, 0, datas))
                                k.state = 'paid'
                            else:
                                continue
                        else:
                            continue
                else:
                    continue

            
            
            # add payroll transaction
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'hr_variance_line_id': invoice_line,
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        # for l in obj:
        #         l.state = 'paid'
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

    # view of payroll transaction Report
class HrPayrollTranSheetView(models.Model):
    _name = 'hr.payroll.tran.sheet.view'
    _description = "Payroll transaction Report"
    _auto = False

    amount = fields.Float('Amount')
    date = fields.Date('Date')
    employee_id = fields.Many2one('hr.employee',string="Employee")
    payroll_item = fields.Many2one('hr.salary.rule',string="Payroll Item")
    tran = fields.Char('Transaction')
    description = fields.Char('Description')

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    def _select(self):
        select_str = """
                SELECT 
                    min(ptl.id) as id,
                    ptl.employee_id,
                    ptl.payroll_item,
                    ptl.tran_note as tran,
                    ptl.allowance as amount,
                    pt.date_from as date,
                    pt.name as description
                    
        """
        return select_str

    def _from(self):
        from_str = """
            hr_payroll_transactions_line ptl
                LEFT JOIN hr_payroll_transactions pt on (ptl.payroll_tran_id = pt.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                ptl.employee_id,
                ptl.payroll_item,
                ptl.tran_note,
                ptl.allowance,
                pt.date_from,
                pt.name
        """
        return group_by_str

    # view of payroll transaction Report

    # view of Salary Sheet
class HrSalarySheetView(models.Model):
    _name = 'hr.salary.sheet.view'
    _description = "Salary Sheet"
    _auto = False

    # abs_deduction = fields.Float('Absent')
    basic = fields.Float('Basic')
    hra = fields.Float('Housing')
    ot_allowance = fields.Float('OT Allowance')
    allowances_value = fields.Float('Allowances')
    additions = fields.Float('Additions')
    cvd0 = fields.Float('CVD 0%')
    cvd50 = fields.Float('CVD 50%')
    cvd30 = fields.Float('CVD 30%')
    cvd40 = fields.Float('CVD 40%')
    cvd100 = fields.Float('CVD 100%')
    deductions = fields.Float('Deductions')
    other_allowance = fields.Float('Other Allowance')
    # expenses = fields.Float('Expenses')
    fine_deduction = fields.Float('Fine')
    # food_allowance = fields.Float('FA')
    gross = fields.Float('Gross')
    loan_deduction = fields.Float('Loan')
    net_salary = fields.Float('Net Salary')
    present = fields.Float('Present')
    trans_allowance = fields.Float('Transport Allowance')
    # traveling_allowance = fields.Float('Traveling Allowance')
    payslip_days = fields.Float('Payslip Days')
    structure_id = fields.Many2one('hr.payroll.structure',string="Salary Structure")
    type_id = fields.Many2one('hr.contract.type',string="Contract Type")
    job_id = fields.Many2one('hr.job',string="Designation")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    department_id = fields.Many2one('hr.department',string="Department")
    identification = fields.Char('Identification No.')
    batch_name = fields.Char('Batch')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    def _select(self):
        select_str = """
                SELECT row_number() OVER (ORDER BY hr_payslip.id) AS id,
                    hr_payslip.employee_id,
                    hr_employee.identification_id AS identification,
                    hr_payslip.struct_id AS structure_id,
                    hr_employee.department_id,
                    hr_employee.job_id,
                    hr_contract.type_id,
                    hr_payslip.date_from,
                    hr_payslip.date_to,
                    hr_payslip.date_to - hr_payslip.date_from + 1 AS payslip_days,
                    hr_payslip_run.name AS batch_name,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'BASIC'::text) AS basic,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'HRA'::text) AS hra,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'OTH'::text) AS other_allowance,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'OT'::text) AS ot_allowance,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'ALWCE'::text) AS allowances_value,
                        
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'ADTNS'::text) AS additions,
                    
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'CVD0'::text) AS cvd0,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'CVD50'::text) AS cvd50,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'CVD30'::text) AS cvd30,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'CVD40'::text) AS cvd40,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'CV100'::text) AS cvd100,
                    


                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'DED'::text) AS deductions,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'TRA'::text) AS trans_allowance,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'LOAN'::text) AS loan_deduction,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'FINE'::text) AS fine_deduction,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'GROSS'::text) AS gross,
                    ( SELECT sum(hr_payslip_worked_days.number_of_days) AS sum
                        FROM hr_payslip_worked_days
                        WHERE hr_payslip_worked_days.payslip_id = hr_payslip.id AND hr_payslip_worked_days.code::text = 'WORK100'::text) AS present,
                    ( SELECT sum(hr_payslip_line.total) AS sum
                        FROM hr_payslip_line
                        WHERE hr_payslip_line.slip_id = hr_payslip.id AND hr_payslip_line.code::text = 'NET'::text) AS net_salary
                    
        """
        return select_str

    def _from(self):
        from_str = """
            hr_payslip
                JOIN hr_contract on (hr_contract.id = hr_payslip.contract_id)
                JOIN hr_employee on (hr_employee.id = hr_contract.employee_id)
                JOIN hr_payroll_structure on (hr_payroll_structure.id = hr_contract.struct_id)
                JOIN hr_payslip_run on (hr_payslip_run.id = hr_payslip.payslip_run_id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                hr_payslip.id,
                hr_payslip.employee_id,
                hr_payslip_run.name,
                hr_employee.department_id,
                hr_employee.job_id,
                hr_payslip.date_from,
                hr_payslip.date_to,
                hr_contract.type_id, 
                hr_employee.identification_id, 
                hr_payslip.struct_id
        """
        return group_by_str

    # view of Salary Sheet
class LeaveAnalysis(models.Model):
    _name = 'leave.analysis'
    _description = "Leaves Analysis"
    _auto = False

    # abs_deduction = fields.Float('Absent')
    employee_id = fields.Many2one('hr.employee',string='Employee Name')
    holiday_status_id = fields.Many2one('hr.leave.type',string='Leaves Type')
    # number_of_days = fields.Float('No of Days')
    # the_month = fields.Datetime('Date')
    total_leave_days = fields.Float('Total Leaves Days')
    total_allocated_days = fields.Float('Total Allocated Days')
    pending_leaves = fields.Float('Pending Leaves')

    # @api.depends('total_leave_days','total_allocated_days')
    # def _pending_leave(self):
    #     for rec in self:
    #         rec.pending_leave = rec.total_allocated_days - rec.total_leave_days

    

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr,'leave_analysis')
        self.env.cr.execute("""CREATE or REPLACE view leave_analysis as (
                SELECT row_number() over(ORDER BY e.id) as id,
                        e.id as employee_id,
                        l.holiday_status_id,
                        sum(l.number_of_days) as total_leave_days, 
                        (select sum(a.number_of_days)
                        from hr_leave_allocation a
                        where e.id = a.employee_id
                        ) as total_allocated_days,
                        ((select sum(a.number_of_days)
                            from hr_leave_allocation a
                            where e.id = a.employee_id
                            ) - sum(l.number_of_days)) as pending_leaves
                        from hr_employee e,
                            hr_leave l
                        where 	e.id=l.employee_id
                    group by e.id, l.holiday_status_id
            );""" )
   
#HR Contract and Payroll Customize Part

# Employee Master edits 
class CostCenter(models.Model):
    _name = 'cost.center'
    _inherit = 'mail.thread'

    name =  fields.Char('Name')

class SourceMaster(models.Model):
    _name = 'source.master'
    _inherit = 'mail.thread'

    name =  fields.Char('Name')

class DocumentType(models.Model):
    _name = 'document.type'
    _inherit = 'mail.thread'

    name =  fields.Char('Name')

class HrEmployeesdocumentcus(models.Model):
    _inherit = 'hr.employee.document'

    document_type = fields.Many2one('document.type',string="Document Type")

class HrEmployeescus(models.Model):
    _inherit = 'hr.employee'

    join_date = fields.Date('Date of Join')
    airfare = fields.Float('Airfare')
    fax_ch = fields.Char('Fax')
    uid_num = fields.Char('UID Number')
    pass_expiry_date = fields.Date('Passport Expiry Date')
    wp_expiry_date = fields.Date('Work Permit Expiry Date')
    airticket_count = fields.Integer(compute='_airticket_count', string='# Airtickets')
    leaves_count_2 = fields.Float('Number of Leaves', compute='_compute_leaves_count2')
    emirates_id = fields.Char('Emirates ID')
    emirates_id_expiry_date = fields.Date('Emirates ID Expiry Date')
    cost_center = fields.Many2one('cost.center',string="Cost Center")

    def _get_date_start_work(self):
        return self.join_date

    @api.multi
    def _compute_leaves_count2(self):
        for rec in self:
            x = 0.0
            all_leaves = self.env['hr.leave.report'].search([('employee_id', '=', rec.id)])
            for l in all_leaves:
                if l.number_of_days < 0.0 and l.state == 'validate':
                    x = x + l.number_of_days
            rec.leaves_count_2 = x

    @api.multi
    def _airticket_count(self):
        for each in self:
            air_ids = self.env['hr.airticket'].sudo().search([('name', '=', each.id)])
            each.airticket_count = len(air_ids)


    @api.multi
    def airticket_view(self):
        self.ensure_one()
        domain = [
            ('name', '=', self.id)]
        vals = {
            'default_name': self.id,
            'default_depart': self.department_id.id,
            'default_designation': self.job_id.id,
            'default_join_date': self.join_date,
            'default_Airfare': self.airfare
        }
        return {
            'name': _('Airtickets'),
            'domain': domain,
            'res_model': 'hr.airticket',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Airticket
                        </p>'''),
            'limit': 80,
            'context': vals,
        }

    @api.multi
    @api.onchange('country_id')
    def _airfare_value(self):
        for rec in self:
            rec.airfare = rec.country_id.airfare

    @api.multi
    def document_view(self):
        action = self.env.ref('marcoms_updates.hr_employee_document_cus_action2').read()[0]
        return action

class HRAirticket(models.Model):
    _name = 'hr.airticket'
    _description = 'HR Air Ticket'


    name = fields.Many2one('hr.employee',string="Employee Name")
    depart = fields.Many2one('hr.department',string="Department")
    designation = fields.Many2one('hr.job',string="Designation")
    join_date = fields.Date('Join Date')
    Airfare = fields.Float('Airfare')
    amount = fields.Float('Ticket Amount')
    ticket_date = fields.Date('Ticket Issued Date')
    remarks = fields.Text('Remarks')


class Countriesscus(models.Model):
    _inherit = 'res.country'

    airfare = fields.Float('Airfare')

# Employee Master edits 

#CRM Lost Reason
class CrmLeadLostcus(models.TransientModel):
    _inherit = 'crm.lead.lost'

    description = fields.Text('Description')

    @api.multi
    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'lost_reason': self.lost_reason_id.id,
                     'des_reason': self.description,
                     'stage_id': 10,})
        return leads.action_set_lost()

#CRM Lost Reason

# Purchase Customization Part
class PurchaseOrderLineCus(models.Model):
    _inherit = 'purchase.order.line'

    state_id = fields.Selection([
        ('confirm', 'Confirmd'),
        ('cancel', 'Cancelled'),
        ], string='State', readonly=True, copy=False, index=True,)
    requ = fields.Many2one('purchase.requisition',invisible=True)

    @api.multi
    def action_add_confirm(self):
        return self.write({'state_id': 'confirm'})

    @api.multi
    def action_cancel(self):
        return self.write({'state_id': 'cancel'})

    @api.multi
    def action_update_qty(self):
        return {
                # 'name': _('Quotation'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'add.qty.purchase',
                'view_id': self.env.ref('marcoms_updates.add_qty_purchase_form').id,
                'type': 'ir.actions.act_window',
                # 'context': vals,
                'target': 'new'
            }


class setting_config(models.TransientModel):
    _inherit = "res.config.settings"

    po_double_validation_amount_top = fields.Monetary(related='company_id.po_double_validation_amount_top', string="Second Level Of Approve", currency_field='company_currency_id', readonly=False)
   


class company_configcus(models.Model):
    _inherit = "res.company"

    po_double_validation_amount_top = fields.Monetary(string='Double validation amount top manager', default=50000,help="Minimum amount for which a double validation is required")   
    date_today = fields.Date('today',compute='_requisition_count',invisible=True)

    @api.multi
    def _requisition_count(self):
        for each in self:
            each.date_today = date.today()


class PurchaseOrderCus(models.Model):
    _inherit = 'purchase.order'

    # state = fields.Selection([
    #     ('draft', 'RFQ'),
    #     ('sel', 'Selected'),
    #     ('sent', 'RFQ Sent'),
    #     ('to approve', 'To Approval'),
    #     ('To approve', 'To Approval'),
    #     ('purchase', 'Purchase Order'),
    #     ('done', 'Locked'),
    #     ('cancel', 'Cancelled')
    # ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')



    # @api.multi
    # def button_confirm(self):
    #     for order in self:
    #         if order.state not in ['draft', 'sent','sel']:
    #             continue
    #         order._add_supplier_to_product()
    #         # Deal with double validation process
    #         if order.company_id.po_double_validation == 'one_step'\
    #                 or (order.company_id.po_double_validation == 'two_step'\
    #                     and order.amount_total < self.env.user.company_id.currency_id._convert(
    #                         order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
    #                 or order.user_has_groups('marcoms_updates.group_purchase_top_manager'):
    #             order.button_approve()
    #         elif  order.amount_total < self.env.user.company_id.currency_id._convert(
    #                         order.company_id.po_double_validation_amount_top, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
    #             order.write({'state': 'To approve'})
    #         else:
    #             order.write({'state': 'to approve'})
    #     return True
    text = fields.Char('Price in Text',compute="_com_price2")
    rfq_name = fields.Char('Rfq Reference', required=True, index=True, copy=False,help="Unique number of the purchase order,computed automatically when the purchase order is created.")
    interchanging_rfq_sequence = fields.Char('RFQ Sequence', copy=False)
    interchanging_po_sequence = fields.Char('Sequence', copy=False)
    received_by = fields.Char('Received by')
    delivery_location = fields.Char('Delivery Location')
                
    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
            name = self.env['ir.sequence'].next_by_code('purchase.order.quot') or 'New'
            vals['rfq_name'] = vals['name'] = name
            
        return super(PurchaseOrderCus, self).create(vals)
        
    @api.multi
    def button_confirm(self):
        res =  super(PurchaseOrderCus, self).button_confirm()
        for order in self:
            if order.interchanging_rfq_sequence:
                order.write({'name': order.interchanging_po_sequence})
            else:
                new_name = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
                order.write({'interchanging_rfq_sequence':order.name})
                order.write({'name': new_name})
            self.picking_ids.write({'origin': order.interchanging_po_sequence})
            if self.picking_ids:
                for pick in self.picking_ids:
                    pick.move_lines.write({'origin': order.interchanging_po_sequence}) 
        return res
    
    @api.multi
    def button_draft(self):
        res = super(PurchaseOrderCus, self).button_draft()
        if self.interchanging_rfq_sequence:
            self.write({'interchanging_po_sequence':self.name})
            self.write({'name':self.interchanging_rfq_sequence})
        # else:
        #     self.write({'interchanging_po_sequence':self.name})
        #     self.write({'name':self.interchanging_rfq_sequence})
            
            
        
        return res


    @api.depends('amount_total','currency_id')
    def _com_price2(self):
        for rec in self:
        # res = super(pur_order_inherit, self)._onchange_amount()
            rec.text = rec.currency_id.amount_to_text(rec.amount_total) if rec.currency_id else ''
            rec.text = rec.text.replace(' And ', ' ')

    @api.multi
    def button_approve2(self, force=False):
        self.write({'state': 'purchase', 'date_approve': fields.Date.context_today(self)})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}

    @api.multi
    @api.onchange('order_line')
    def add_req_value(self):
        for rec in self:
            if rec.requisition_id:
                for l in rec.order_line:
                    l.requ = rec.requisition_id.id
            else:
                continue

    @api.multi
    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('marcoms_updates', 'purchase_send_mail_template')[1]
            else:
                template_id = ir_model_data.get_object_reference('marcoms_updates', 'purchase_send_mail_template_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


             
   

class PurchaseRequisitionCus(models.Model):
    _inherit = 'purchase.requisition'


    requisition_so_id = fields.Many2one('material.requisition.sales',string="Requisition From Sales")

    @api.multi
    def action_compare(self):
        action = self.env.ref('marcoms_updates.purchase_order_line_cus_action').read()[0]
        return action

    @api.model
    def create(self,vals):
        """ Broadcast the welcome message to all users in the employee company. """
        
        # self.ensure_one()
        # IrModelData = self.env['ir.model.data']
        # ch_id = self.env['material.requisition'].search([('id', '=', vals['requisition_mat_po_id'])])
        # for x in ch_id:
        #     req = x.sequence
        # raise ValidationError(_(vals['name']))
        if vals['origin']:
            
            channel_all_employees = self.env.ref('marcoms_updates.channel_all_employees_pur').read()[0]
            template_new_employee = self.env.ref('marcoms_updates.email_template_data_applicant_tender').read()[0]
            # raise ValidationError(_(template_new_employee))
            if template_new_employee:
                # MailTemplate = self.env['mail.template']
                body_html = template_new_employee['body_html']
                subject = template_new_employee['subject']
                # raise ValidationError(_('%s %s ') % (body_html,subject))
                ids = channel_all_employees['id']
                channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                channel_id.message_post(body='Hello there are New Purchase Tender Created Please Check the Purchase Requisition NO is '+str(vals['origin']), subject=subject,subtype='mail.mt_comment')
                
            
        result = super(PurchaseRequisitionCus, self).create(vals)
        return result
            # self.env['mail.message'].create({'message_type':"notification",
            #     "subtype": self.env.ref("mail.mt_comment").id,
            #     'body': body_html,
            #     'subject': subject,
            #     'needaction_partner_ids': [(4, self.user_id.partner_id.id)],
            #     'model': self._name,
            #     'res_id': ids,
            #     })
        # return True

class PurchaseReportcus(models.Model):
    _inherit = "purchase.report"
   
    name = fields.Many2one('purchase.order', 'Purchase Reference', readonly=True)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
                SELECT
                    min(l.id) as id,
                    s.date_order as date_order,
                    s.state,
                    s.id as name,
                    s.date_approve,
                    s.dest_address_id,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    s.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    s.currency_id,
                    t.uom_id as product_uom,
                    sum(l.product_qty/u.factor*u2.factor) as unit_quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr_lines,
                    sum(l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0) * l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit / COALESCE(NULLIF(cr.rate, 0),1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    (sum(l.product_qty * l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    analytic_account.id as account_analytic_id,
                    sum(p.weight * l.product_qty/u.factor*u2.factor) as weight,
                    sum(p.volume * l.product_qty/u.factor*u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str


    def _group_by(self):
        group_by_str = """
            GROUP BY
                s.company_id,
                s.user_id,
                s.partner_id,
                u.factor,
                s.currency_id,
                l.price_unit,
                s.date_approve,
                l.date_planned,
                l.product_uom,
                s.dest_address_id,
                s.fiscal_position_id,
                l.product_id,
                p.product_tmpl_id,
                t.categ_id,
                s.date_order,
                s.state,
                s.id,
                u.uom_type,
                u.category_id,
                t.uom_id,
                u.id,
                u2.factor,
                partner.country_id,
                partner.commercial_partner_id,
                analytic_account.id
        """
        return group_by_str

# Purchase Customization Part

# Accounts Customization Part
class AccountInvoiceRefundCus(models.TransientModel):
    _inherit = 'account.invoice.refund'

    date_invoice = fields.Date(string='Debit Note Date', default=fields.Date.context_today, required=True)
    filter_refund = fields.Selection([('refund', 'Create a draft debit note'), ('cancel', 'Cancel: create debit note and reconcile'), ('modify', 'Modify: create debit note, reconcile and create a new draft invoice')],default='refund', string='Credit Method', required=True, help='Choose how you want to credit this invoice. You cannot Modify and Cancel if the invoice is already reconciled')

class AccountInvoiceCust(models.Model):
    _inherit = 'account.invoice'

    term = fields.Many2one('bank.details',string='Bank Details')
    LPO = fields.Char('LPO No.')
    project_name = fields.Char('Event')
    text = fields.Char('Price in Text',compute="_com_price2",invisible=True)
    project = fields.Many2one('account.analytic.account',string="project")
    document_count = fields.Integer(compute='_document_count', string='# Documents')
    comment = fields.Text('Additional Information')
    
#     @api.model
#     def _default_commentt(self,vals):
#         # picking_type_id = self._context.get('default_picking_type_id')
#         if self.type != ['in_invoice','out_refund','in_refund']:
#             return """Terms and Conditions:
# Goods will remain the property of MARCOMS until payment of this invoice is settled in full.
# Cheque Payments should be made under the name of "MARCOMS LLC".
# Official receipt should be obtained for cash payments."""
#         else:
#             return " "

    @api.model
    def create(self, vals):
        if not vals.get('journal_id') and vals.get('type'):
            vals['journal_id'] = self.with_context(type=vals.get('type'))._default_journal().id

        if vals.get('type') != ['in_invoice','out_refund','in_refund']:
            vals['comment'] = """Terms and Conditions:
Goods will remain the property of MARCOMS until payment of this invoice is settled in full.
Cheque Payments should be made under the name of "MARCOMS LLC".
Official receipt should be obtained for cash payments."""
        # else:
        #     return " "

        onchanges = self._get_onchange_create()
        for onchange_method, changed_fields in onchanges.items():
            if any(f not in vals for f in changed_fields):
                invoice = self.new(vals)
                getattr(invoice, onchange_method)()
                for field in changed_fields:
                    if field not in vals and invoice[field]:
                        vals[field] = invoice._fields[field].convert_to_write(invoice[field], invoice)

        invoice = super(AccountInvoiceCust, self.with_context(mail_create_nolog=True)).create(vals)

        if any(line.invoice_line_tax_ids for line in invoice.invoice_line_ids) and not invoice.tax_line_ids:
            invoice.compute_taxes()

        return invoice

    @api.multi
    def _document_count(self):
        for each in self:
            document_ids = self.env['account.invoice.document'].sudo().search([('pay_ref', '=', each.id)])
            each.document_count = len(document_ids)

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [('pay_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'account.invoice.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_pay_ref': '%s'}" % self.id
        }

    @api.depends('amount_total','currency_id')
    def _com_price2(self):
        for rec in self:
        # res = super(pur_order_inherit, self)._onchange_amount()
            rec.text = rec.currency_id.amount_to_text(rec.amount_total) if rec.currency_id else ''
            rec.text = rec.text.replace(' And ', ' ').replace(',',' ')
        #self.text = self.text.replace(' Dirham ', ' ')



counter_array = []
class AccountpaymentCust(models.Model):
    _inherit = 'account.payment'

    text = fields.Char('Price in Text',compute="_com_price2",invisible=True)
    # cheque_date = fields.Date('Cheque Date')
    remarks = fields.Text('Remarks')
    seal = fields.Boolean('Include Company Seal',default=False)
    pdc_account = fields.Many2one('account.account',string="PDC Account")
    release_count = fields.Integer('Count',default=0,copy=False)
    move_relase_id = fields.Integer('Move id')
    move_entry_id = fields.Integer('Move id')
    release_check = fields.Boolean('Is Release',default=False)
    # variance_id = fields.One2many('payment.variance.inv','payment_ids',string="Payment Variance")
    variance_count = fields.Integer('Count',default=0,copy=False)
    add_variance_count = fields.Integer('Count',default=0,copy=False)
    var_account = fields.Many2one('account.account',string="Variance Account")
    var_amount = fields.Float(string="Variance Amount",compute='_var_amount')
    invoice_lines_outstand = fields.One2many('payment.invoice.line.outstand', 'payment_id', string="Outstanding Line")
    accountname = fields.Many2one('account.account',string='account')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,required=True, readonly=True, states={'draft': [('readonly', False)]},default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    flag_acc = fields.Boolean('Flag',default=False)
    # prepare = fields.Char('Prepared by')
    # checked = fields.Char('Checked by')
    # received = fields.Char('Received by')
    # approved = fields.Char('Approved by')
    # verified = fields.Char('Verified by')
    
    @api.multi
    @api.depends('invoice_lines','amount','invoice_lines_outstand')
    def _var_amount(self):
        for rec in self:
            y = 0.0
            z = 0.0
            amt = rec.amount
            for x in rec.invoice_lines:
                y = y + x.allocation
            if rec.invoice_lines_outstand:
                for l in rec.invoice_lines_outstand:
                    if l.allocation:
                        z = z + l.allocation
                amt = amt + z
            rec.var_amount = amt - y

    @api.onchange('amount','currency_id')
    def _onchange_amount(self):
        res = super(AccountpaymentCust, self)._onchange_amount()
        self.check_amount_in_words = self.currency_id.amount_to_text(self.amount) if self.currency_id else ''
        self.check_amount_in_words = self.check_amount_in_words.replace(' Dirham ', ' ').replace(' Dirham',' ').replace(' And ',' ')

        return res

    @api.depends('amount','currency_id')
    def _com_price2(self):
        for rec in self:
        # res = super(pur_order_inherit, self)._onchange_amount()
            rec.text = rec.currency_id.amount_to_text(rec.amount) if rec.currency_id else ''
            rec.text = rec.text.replace(' And ', ' ').replace(',',' ').replace(' Dirham ',' ').replace(' Fils',' ').replace(' Dirham',' ')
            # rec.check_amount_in_words = rec.check_amount_in_words.replace(' Dirham ', ' ').replace(' Dirham',' ')

    

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        if self.payment_method_code == 'pdc':
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        else:
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

    
        move = self.env['account.move'].create(self._get_move_vals())
        self.move_entry_id = move.id

        ino = self.env['account.invoice']
        flag_accc = False
        # raise ValidationError(_('test'))
        if len(self.invoice_ids) != 1:
            flag_accc = True
            if self.var_amount != 0:
                amt = 0.0
                # for l in self.invoice_lines:
                    # if l.allocation :
                
                # if self.payment_method_code == 'pdc':
                # debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.effective_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
                # else:
                # debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        for l in self.invoice_lines:
                            if l.allocation:
                                
                                amt = l.allocation
                                amountss = -amt
                                if self.payment_method_code == 'pdc':
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                else:
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                counterpart_aml_dict = self._get_shared_move_line_vals(debit,credit, amount_currency, move.id, False)
                                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                counterpart_aml_dict.update({'currency_id': currency_id})
                                counterpart_aml_dict.update({'date_maturity': self.payment_date})
                            # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                # raise ValidationError(_(counterpart_aml_dict))
                                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                com = ino.search([('number','=',l.invoice)])
                                com.register_payment(counterpart_aml)

                    else:
                        if self.var_amount != 0:
                            for l in self.invoice_lines:
                                if l.allocation:
                                    
                                    amt = l.allocation
                                    amountss = -amt
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals( credit,debit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                    # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                            # raise ValidationError(_(counterpart_aml_dict))
                        else:
                            for l in self.invoice_lines:
                                if l.allocation:
                                    
                                    amt = l.allocation
                                    amountss = -amt
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals( debit,credit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                    # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                        # raise ValidationError(_(counterpart_aml_dict))
                else:
                    if self.partner_type == 'customer':
                        for l in self.invoice_lines:
                            if l.allocation:
                                
                                amt = l.allocation
                                amountss = -amt
                                if self.payment_method_code == 'pdc':
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                else:
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                counterpart_aml_dict.update({'currency_id': currency_id})
                                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                com = ino.search([('number','=',l.invoice)])
                                com.register_payment(counterpart_aml)
                        # raise ValidationError(_(counterpart_aml_dict))
                    else:
                        for l in self.invoice_lines:
                            if l.allocation:
                               
                                amt = l.allocation
                                amountss = -amt
                                if self.payment_method_code == 'pdc':
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                else:
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                counterpart_aml_dict = self._get_shared_move_line_vals(credit,debit,  amount_currency, move.id, False)
                                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                counterpart_aml_dict.update({'currency_id': currency_id})
                                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                com = ino.search([('number','=',l.invoice)])
                                com.register_payment(counterpart_aml)
                                # raise ValidationError(_(counterpart_aml_dict))
            #Write line corresponding to invoice payment
            else:
                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        for l in self.invoice_lines:
                            if l.allocation:
                                
                                if self.payment_method_code == 'pdc':
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                else:
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                counterpart_aml_dict = self._get_shared_move_line_vals(debit,credit, amount_currency, move.id, False)
                                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                counterpart_aml_dict.update({'currency_id': currency_id})
                                counterpart_aml_dict.update({'date_maturity': self.payment_date})
                            # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                com = ino.search([('number','=',l.invoice)])
                                com.register_payment(counterpart_aml)
                    else:
                        if self.var_amount != 0:
                            for l in self.invoice_lines:
                                if l.allocation:
                                    
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals( credit,debit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                    # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                    # raise ValidationError(_(counterpart_aml_dict))
                        else:
                            for l in self.invoice_lines:
                                if l.allocation:
                                    
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals( credit,debit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                    # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                    # raise ValidationError(_(counterpart_aml_dict))
                else:
                    if self.partner_type == 'customer':
                        for l in self.invoice_lines:
                            if l.allocation:
                                
                                if self.payment_method_code == 'pdc':
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                else:
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                counterpart_aml_dict.update({'currency_id': currency_id})
                                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                com = ino.search([('number','=',l.invoice)])
                                com.register_payment(counterpart_aml)
                        # raise ValidationError(_(counterpart_aml_dict))
                    else:
                        for l in self.invoice_lines:
                            if l.allocation:
                                
                                if self.payment_method_code == 'pdc':
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                else:
                                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                counterpart_aml_dict = self._get_shared_move_line_vals(credit,debit,  amount_currency, move.id, False)
                                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                counterpart_aml_dict.update({'currency_id': currency_id})
                                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                com = ino.search([('number','=',l.invoice)])
                                com.register_payment(counterpart_aml)
                                # raise ValidationError(_(counterpart_aml_dict))
        else:
            invoice_namm = ''
            amtss = 0.0
            if self.invoice_lines:
                flag_accc = True
                for l in self.invoice_lines:
                    invoice_namm = l.invoice
                    if l.allocation:
                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                        if self.var_amount != 0:
                            if self.payment_method_code == 'pdc':
                                if self.partner_type == 'customer':
                                    # for l in self.invoice_lines:
                                        # if l.allocation:
                                            
                                        amt = l.allocation
                                        amountss = -amt
                                        if self.payment_method_code == 'pdc':
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                        else:
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                        counterpart_aml_dict = self._get_shared_move_line_vals(debit,credit, amount_currency, move.id, False)
                                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                        counterpart_aml_dict.update({'currency_id': currency_id})
                                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                        # raise ValidationError(_(counterpart_aml_dict))
                                    # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                        com = ino.search([('number','=',l.invoice)])
                                        com.register_payment(counterpart_aml)

                                else:
                                    if self.var_amount != 0:
                                        # for l in self.invoice_lines:
                                        #     if l.allocation:
                                                
                                        amt = l.allocation
                                        amountss = -amt
                                        if self.payment_method_code == 'pdc':
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                        else:
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                        counterpart_aml_dict = self._get_shared_move_line_vals( credit,debit, amount_currency, move.id, False)
                                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                        counterpart_aml_dict.update({'currency_id': currency_id})
                                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                        # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                        com = ino.search([('number','=',l.invoice)])
                                        com.register_payment(counterpart_aml)
                                        # raise ValidationError(_(counterpart_aml_dict))
                                    else:
                                        # for l in self.invoice_lines:
                                            # if l.allocation:
                                                
                                        amt = l.allocation
                                        amountss = -amt
                                        if self.payment_method_code == 'pdc':
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                        else:
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                        counterpart_aml_dict = self._get_shared_move_line_vals( credit,debit, amount_currency, move.id, False)
                                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                        counterpart_aml_dict.update({'currency_id': currency_id})
                                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                        # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                        com = ino.search([('number','=',l.invoice)])
                                        com.register_payment(counterpart_aml)
                                        # raise ValidationError(_(counterpart_aml_dict))
                            else:
                                if self.partner_type == 'customer':
                                    # for l in self.invoice_lines:
                                    #     if l.allocation:
                                            
                                    amt = l.allocation
                                    amountss = -amt
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                    # raise ValidationError(_(counterpart_aml_dict))
                                else:
                                    # for l in self.invoice_lines:
                                    #     if l.allocation:
                                        
                                    amt = l.allocation
                                    amountss = -amt
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amountss, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals(credit,debit,  amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                    # raise ValidationError(_(counterpart_aml_dict))
                    #Write line corresponding to invoice payment
                        else:
                            if self.payment_method_code == 'pdc':
                                if self.partner_type == 'customer':
                                    # for l in self.invoice_lines:
                                    #     if l.allocation:
                                            
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals(debit,credit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                else:
                                    if self.var_amount != 0:
                                        # for l in self.invoice_lines:
                                        #     if l.allocation:
                                                
                                        if self.payment_method_code == 'pdc':
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                        else:
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                        counterpart_aml_dict = self._get_shared_move_line_vals( credit,debit, amount_currency, move.id, False)
                                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                        counterpart_aml_dict.update({'currency_id': currency_id})
                                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                        # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                        com = ino.search([('number','=',l.invoice)])
                                        com.register_payment(counterpart_aml)
                                        # raise ValidationError(_(counterpart_aml_dict))
                                    else:
                                        # for l in self.invoice_lines:
                                        #     if l.allocation:
                                                
                                        if self.payment_method_code == 'pdc':
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                        else:
                                            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                        counterpart_aml_dict = self._get_shared_move_line_vals( debit,credit, amount_currency, move.id, False)
                                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                        counterpart_aml_dict.update({'currency_id': currency_id})
                                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                                        # counterpart_aml_dict.update({'account_id': self.pdc_account.id})
                                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                        com = ino.search([('number','=',l.invoice)])
                                        com.register_payment(counterpart_aml)
                                        # raise ValidationError(_(counterpart_aml_dict))
                            else:
                                if self.partner_type == 'customer':
                                    # for l in self.invoice_lines:
                                    #     if l.allocation:
                                            
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                    # raise ValidationError(_(counterpart_aml_dict))
                                else:
                                    # for l in self.invoice_lines:
                                    #     if l.allocation:
                                            
                                    if self.payment_method_code == 'pdc':
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)
                                    else:
                                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-l.allocation, self.currency_id, self.company_id.currency_id)

                                    counterpart_aml_dict = self._get_shared_move_line_vals(credit,debit,  amount_currency, move.id, False)
                                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals(l.invoice))
                                    counterpart_aml_dict.update({'currency_id': currency_id})
                                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                                    com = ino.search([('number','=',l.invoice)])
                                    com.register_payment(counterpart_aml)
                                    # raise ValidationError(_(counterpart_aml_dict))
            else:
                if self.payment_method_code == 'pdc':
                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
                else:
                    debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.communication))
                        counterpart_aml_dict.update({'currency_id': currency_id})
                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                        # if self.invoice_ids:
                        #     self.invoice_ids.register_payment(counterpart_aml)
                    else:
                        counterpart_aml_dict = self._get_shared_move_line_vals( debit,credit, amount_currency, move.id, False)
                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.communication))
                        counterpart_aml_dict.update({'currency_id': currency_id})
                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                        # raise ValidationError(_(counterpart_aml_dict))
                        # if self.invoice_ids:
                        #     self.invoice_ids.register_payment(counterpart_aml)

                else:
                    if self.partner_type == 'customer':
                        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.communication))
                        counterpart_aml_dict.update({'currency_id': currency_id})
                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                        # if self.invoice_ids:
                        #     self.invoice_ids.register_payment(counterpart_aml)
                        # raise ValidationError(_(counterpart_aml_dict))
                    else:
                        counterpart_aml_dict = self._get_shared_move_line_vals( debit,credit, amount_currency, move.id, False)
                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.communication))
                        counterpart_aml_dict.update({'currency_id': currency_id})
                        counterpart_aml_dict.update({'date_maturity': self.payment_date})
                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                        # raise ValidationError(_(counterpart_aml_dict))
                        # if self.invoice_ids:
                        #     self.invoice_ids.register_payment(counterpart_aml)
                        # raise ValidationError(_(counterpart_aml_dict))


        if self.payment_method_code == 'pdc':
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        else:
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            # raise ValidationError(_(self.payment_difference))
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo
            # raise ValidationError(_(counterpart_aml))

        #Write counterpart lines
        if len(self.invoice_ids) != 1:
            if not self.currency_id.is_zero(self.amount):
                
                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit,debit,  -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
                    else:
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
                else:
                    if self.partner_type == 'customer':
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit,debit,  -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
                    else:
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
        else:
            if not self.currency_id.is_zero(self.amount):
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
                    else: 
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
                else:
                    if self.partner_type == 'customer':
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)
                        # raise ValidationError(_(liquidity_aml_dict))
                    else: 
                        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'date_maturity': self.payment_date})
                        aml_obj.create(liquidity_aml_dict)

        


    # ####################################################################################################
    # ####################################################################################################

        # if len(self.invoice_ids) != 1:
        if self.invoice_lines:
            if self.invoice_lines_outstand:
                y = 0.0
                for com in self.invoice_lines_outstand:
                    if com.allocation:
                        y = y + com.allocation

                for com in self.invoice_lines_outstand:
                    if com.allocation:
                        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(-com.allocation, self.currency_id, self.company_id.currency_id)
                        if self.partner_type == 'customer':
                            counterpart_aml_dict = self._get_shared_move_line_vals(credit,debit,  amount_currency, move.id, False)
                            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.communication))
                            counterpart_aml_dict.update({'currency_id': currency_id})
                            counterpart_aml_dict.update({'date_maturity': self.payment_date})
                            counterpart_amls = aml_obj.create(counterpart_aml_dict)
                            
                            partial_rec = self.env['account.partial.reconcile']
                            aml_model = self.env['account.move.line']

                            created_lines = self.env['account.move.line']
                            com.move_id.amount_residual = com.allocation
                            #reconcile all aml_to_fix
                            value = {'id':counterpart_amls.id,'m_id':com.move_id.id}
                            counter_array.append(value)
                            partial_rec |= partial_rec.create(
                                partial_rec._prepare_exchange_diff_partial_reconcile(
                                        aml=com.move_id,
                                        line_to_reconcile=counterpart_amls,
                                        currency=com.move_id.currency_id or False)
                            )
                            created_lines |= counterpart_amls
                            
                        else: 
                            counterpart_aml_dict = self._get_shared_move_line_vals( debit,credit, amount_currency, move.id, False)
                            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.communication))
                            counterpart_aml_dict.update({'currency_id': currency_id})
                            counterpart_aml_dict.update({'date_maturity': self.payment_date})
                            counterpart_amls = aml_obj.create(counterpart_aml_dict)
                            # value = {'id':counterpart_amls.id}
                            # counter_array.append(value)
                            partial_rec = self.env['account.partial.reconcile']
                            aml_model = self.env['account.move.line']

                            created_lines = self.env['account.move.line']
                            com.move_id.amount_residual = com.allocation
                            #reconcile all aml_to_fix
                            value = {'id':counterpart_amls.id,'m_id':com.move_id.id}
                            counter_array.append(value)
                            partial_rec |= partial_rec.create(
                                partial_rec._prepare_exchange_diff_partial_reconcile(
                                        aml=com.move_id,
                                        line_to_reconcile=counterpart_amls,
                                        currency=com.move_id.currency_id or False)
                            )
                            created_lines |= counterpart_amls
        # #################################################################################################3
        # #################################################################################################3

        # ######################################################################################################
        # #####################################################################################################
        if self.invoice_lines  or self.flag_acc == True or (self.var_amount and flag_accc):
            if self.var_account:
                # rec.write({'state': 'draft'})
                id_account = self.var_account.id
                # aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
                # com = self.env['payment.variance.inv'].search([('payment_ids','=',rec.id)])
                # y = 0.0
                amt = 0.0
                # for x in com:
                #     y = y + x.var_amount
                #     amt = amt + x.invoice_amount
                amounts = self.var_amount
                for l in self.invoice_lines:
                    if l.allocation :
                        amt = amt + l.total_amount
                total_amt = amt
                # raise ValidationError(_('Testsss'))
                invoice_la = 'Variance Amount'
                if amounts != 0:

                    debits, credits, amount_currencys, currency_ids = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amounts, self.currency_id, self.company_id.currency_id)

                    if amounts > 0:
                        #Write line corresponding to invoice payment

                        if self.partner_type == 'customer':
                            counterpart_aml_dict = self._get_shared_move_line_vals(credits,debits,  amount_currencys, move.id, False)
                            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_la))
                            counterpart_aml_dict.update({'currency_id': currency_ids})
                            counterpart_aml_dict.update({'account_id': id_account})
                            if self.payment_method_code == 'pdc':
                                counterpart_aml_dict.update({'date': self.payment_date})
                            else:
                                counterpart_aml_dict.update({'date': self.payment_date})
                            counterpart_aml = aml_obj.create(counterpart_aml_dict)
                            # raise ValidationError(_(counterpart_aml_dict))
                        else:
                            counterpart_aml_dict = self._get_shared_move_line_vals( debits,credits, amount_currencys, move.id, False)
                            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_la))
                            counterpart_aml_dict.update({'currency_id': currency_ids})
                            counterpart_aml_dict.update({'account_id': id_account})
                            if self.payment_method_code == 'pdc':
                                counterpart_aml_dict.update({'date': self.payment_date})
                            else:
                                counterpart_aml_dict.update({'date': self.payment_date})
                            counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    else:
                        if self.payment_method_code == 'pdc':
                            if self.partner_type == 'customer':
                                liquidity_aml_dict = self._get_shared_move_line_vals(credits,debits,  -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                liquidity_aml_dict.update({'account_id': id_account})
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                            # raise ValidationError(_(liquidity_aml_dict))
                            else:
                                liquidity_aml_dict = self._get_shared_move_line_vals( debits,credits, -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                liquidity_aml_dict.update({'account_id': id_account})
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                                # raise ValidationError(_(liquidity_aml_dict))
                        else:
                            if self.partner_type == 'customer':
                                liquidity_aml_dict = self._get_shared_move_line_vals(credits, debits, -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                liquidity_aml_dict.update({'account_id': id_account})
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                            else:
                                liquidity_aml_dict = self._get_shared_move_line_vals(debits,credits,  -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                liquidity_aml_dict.update({'account_id': id_account})
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                                # raise ValidationError(_(liquidity_aml_dict))
                    
                    # self.add_variance_count = 1
            else:
                invoice_la = 'Variance Amount'
                id_account = self.var_account.id
                # aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
                # com = self.env['payment.variance.inv'].search([('payment_ids','=',rec.id)])
                # y = 0.0
                amt = 0.0
                # for x in com:
                #     y = y + x.var_amount
                #     amt = amt + x.invoice_amount
                amounts = self.var_amount
                for l in self.invoice_lines:
                    if l.allocation :
                        amt = amt + l.total_amount
                total_amt = amt
                
                if amounts != 0:
                    debits, credits, amount_currencys, currency_ids = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amounts, self.currency_id, self.company_id.currency_id)
                    
                    if amounts > 0:
                        #Write line corresponding to invoice payment
                        if self.partner_type == 'customer':
                            counterpart_aml_dict = self._get_shared_move_line_vals(credits,debits,  amount_currencys, move.id, False)
                            
                            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_la))
                            
                            counterpart_aml_dict.update({'currency_id': currency_ids})
                            if self.payment_method_code == 'pdc':
                                counterpart_aml_dict.update({'date': self.payment_date})
                            else:
                                counterpart_aml_dict.update({'date': self.payment_date})
                            # counterpart_aml_dict.update({'account_id': id_account})
                            counterpart_aml = aml_obj.create(counterpart_aml_dict)
                            # raise ValidationError(_('test'))
                            # raise ValidationError(_(counterpart_aml_dict))
                        else:
                            counterpart_aml_dict = self._get_shared_move_line_vals( debits,credits, amount_currencys, move.id, False)
                            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_la))
                            counterpart_aml_dict.update({'currency_id': currency_ids})
                            # counterpart_aml_dict.update({'account_id': id_account})
                            if self.payment_method_code == 'pdc':
                                counterpart_aml_dict.update({'date': self.payment_date})
                            else:
                                counterpart_aml_dict.update({'date': self.payment_date})
                            counterpart_aml = aml_obj.create(counterpart_aml_dict)
                            # raise ValidationError(_(counterpart_aml_dict))
                    else:
                        if self.payment_method_code == 'pdc':
                            if self.partner_type == 'customer':
                                liquidity_aml_dict = self._get_shared_move_line_vals(credits,debits,  -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                                # raise ValidationError(_(liquidity_aml_dict))
                            else:
                                liquidity_aml_dict = self._get_shared_move_line_vals( debits,credits, -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                                # raise ValidationError(_(liquidity_aml_dict))
                        else:
                            if self.partner_type == 'customer':
                                liquidity_aml_dict = self._get_shared_move_line_vals(credits, debits, -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)
                                # raise ValidationError(_(liquidity_aml_dict))
                            else:
                                liquidity_aml_dict = self._get_shared_move_line_vals(debits,credits,  -amount_currencys, move.id, False)
                                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amounts))
                                if self.payment_method_code == 'pdc':
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                else:
                                    liquidity_aml_dict.update({'date': self.payment_date})
                                aml_obj.create(liquidity_aml_dict)

        # #######################################################################################################3
        # ########################################################################################################3
        #validate the payment
        # raise ValidationError(_('test'))
        # if not self.journal_id.post_at_bank_rec:
        move.post()
        

        if not len(self.invoice_ids) != 1:
            if not self.invoice_lines:
                # raise ValidationError(_('test'))
                if self.invoice_ids:
                    self.invoice_ids.register_payment(counterpart_aml)
        # 
        return move


    def _get_counterpart_move_line_vals(self, invoice=False):
        if self.payment_type == 'transfer':
            name = self.name
        else:
            name = ''
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment ")
                elif self.payment_type == 'outbound':
                    name += _("Customer Credit Note ")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Credit Note ")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment ")
            if invoice:
                name +=  invoice
                # for inv in invoice:
                #     if inv.move_id:
                #         name += inv.number + ', '
                # name = name[:len(name)-2]
        return {
            'name': name,
            'account_id': self.destination_account_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
        }

    # def _get_move_valsss(self, journal=None):
    #     """ Return dict to create the payment move
    #     """
    #     journal = journal or self.journal_id
    #     move_vals = {
    #         'date': self.payment_date,
    #         'ref': self.communication or '',
    #         'company_id': self.company_id.id,
    #         'journal_id': selfjournal_id.id,
    #     }
    #     if self.move_name:
    #         move_vals['name'] = self.move_name + 'release'
    #     return move_vals

    def _get_shared_move_line_valss(self, debit, credit, amount_currency, move_id, invoice_id=False):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """
        return {
            'partner_id': self.payment_type in ('inbound', 'outbound') and self.env['res.partner']._find_accounting_partner(self.partner_id).id or False,
            'invoice_id': invoice_id and invoice_id.id or False,
            'move_id': move_id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'payment_id': self.id,
            'journal_id': self.journal_id.id,
            'date':self.effective_date,
        }

    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id
        move_vals = {
            'date': self.payment_date,
            'ref': str(self.communication) + '/' + str(self.cheque_reference) or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
        }
        if self.move_name:
            move_vals['name'] = self.move_name
        return move_vals

    @api.multi
    def _create_payment_entry_release(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
        Return the journal entry.
    """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.effective_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        # raise ValidationError(_("Test"))
        move_vals = {
            'date': self.effective_date,
            'ref': str(self.communication) + '/' + str(self.cheque_reference) + ' Release' or '',
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
        }
        if self.move_name:
            move_vals['name'] = self.move_name
        move = self.env['account.move'].create(move_vals)
        self.move_relase_id = move.id
        if self.var_amount < 0:
            amt = 0.0
            for l in self.invoice_lines:
                if l.allocation :
                    amt = amt + l.allocation
            amount = -amt
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.effective_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
            invoice_la = 'Receivables Relase Amount'
            invoice_pa = 'Payables Relase Amount'
            if self.partner_type == 'customer':
                counterpart_aml_dict = self._get_shared_move_line_valss(credit,debit,  amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_la))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml_dict.update({'account_id': self.journal_id.default_debit_account_id.id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
            else:
                counterpart_aml_dict = self._get_shared_move_line_valss(debit,credit, amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_pa))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml_dict.update({'account_id': self.journal_id.default_credit_account_id.id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
            
            #Reconcile with the invoices
            if self.payment_difference_handling == 'reconcile' and self.payment_difference:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.effective_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.writeoff_label
                writeoff_line['account_id'] = self.writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo

            #Write counterpart lines
            if not self.currency_id.is_zero(self.amount):
                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss( debit,credit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        aml_obj.create(liquidity_aml_dict)
                    else:
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss( debit,credit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        aml_obj.create(liquidity_aml_dict)
                else:
                    if self.partner_type == 'customer':
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss( debit,credit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        aml_obj.create(liquidity_aml_dict)
                    else:
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss(credit, debit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        aml_obj.create(liquidity_aml_dict)
        else:
            invoice_la = 'Receivables Relase Amount'
            invoice_pa = 'Payables Relase Amount'
            #Write line corresponding to invoice payment
            if self.partner_type == 'customer':
                counterpart_aml_dict = self._get_shared_move_line_valss(credit,debit,  amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_la))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml_dict.update({'account_id': self.journal_id.default_debit_account_id.id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
            else:
                counterpart_aml_dict = self._get_shared_move_line_valss(credit,debit, amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_pa))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml_dict.update({'account_id': self.journal_id.default_credit_account_id.id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
            
            #Reconcile with the invoices
            if self.payment_difference_handling == 'reconcile' and self.payment_difference:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.writeoff_label
                writeoff_line['account_id'] = self.writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo

            #Write counterpart lines
            if not self.currency_id.is_zero(self.amount):
                if self.payment_method_code == 'pdc':
                    if self.partner_type == 'customer':
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss( debit,credit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        aml_obj.create(liquidity_aml_dict)
                    else:
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss( debit,credit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        liquidity_aml_dict.update({'account_id': self.pdc_account.id})
                        aml_obj.create(liquidity_aml_dict)
                else:
                    if self.partner_type == 'customer':
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss( debit,credit, -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        aml_obj.create(liquidity_aml_dict)
                    else:
                        if not self.currency_id != self.company_id.currency_id:
                            amount_currency = 0
                        liquidity_aml_dict = self._get_shared_move_line_valss(debit,credit,  -amount_currency, move.id, False)
                        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                        aml_obj.create(liquidity_aml_dict)

        #validate the payment
        # if not self.journal_id.post_at_bank_rec:
        #     move.action_release()

        #reconcile the invoice receivable/payable line(s) with the payment
        # if self.invoice_ids:
        #     self.invoice_ids.register_payment(counterpart_aml)
        self.release_count = 1
        self.release_check = True
        return move


    @api.multi
    def action_release(self):
        for rec in self:

            # if any(inv.state != 'open' for inv in rec.invoice_ids):
            #     raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry_release(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            # rec.write({'state': 'posted', 'move_name': move.name})
        return True


    @api.multi
    def button_journal_entries_release(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('move_id', '=', self.move_relase_id)],
        }

    @api.multi
    def cancel(self):
        for rec in self:
            for move in rec.move_line_ids.mapped('move_id'):
                if rec.invoice_ids:
                    move.line_ids.remove_move_reconcile()
                move.button_cancel()
                move.unlink()
            # for l in counter_array:
            #     cov  = self.env['account.move.line'].search([('id','=',l['id'])])
            #     cos  = self.env['account.move.line'].search([('id','=',l['m_id'])])
            #     cov.remove_move_reconcile()
            #     cos.remove_move_reconcile()

            if self.release_count != 0 :
                com = self.env['account.move'].search([('id','=',self.move_relase_id)])
                for mov in com:
                    if rec.invoice_ids:
                        mov.line_ids.remove_move_reconcile()
                    mov.button_cancel()
                    mov.unlink()
                self.release_count = 0
                self.release_check = False
            rec.add_variance_count = 0
            rec.state = 'cancelled'
            outstan = self.env['payment.invoice.line.outstand'].search([('amount','=',0)])
            for stan in outstan:
                if stan.amount == 0 :
                    stan.unlink()

    @api.multi
    def add_variance(self):
        for rec in self:
            if rec.var_account:
                id_account = rec.var_account.id
                amt = 0.0
                amounts = rec.var_amount
                for l in rec.invoice_lines:
                    if l.allocation :
                        amt = amt + l.total_amount
                total_amt = amt

                if amounts != 0:
                    debits, credits, amount_currencys, currency_ids = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amounts, self.currency_id, self.company_id.currency_id)

                    #Write line corresponding to invoice payment
                    if self.partner_type == 'customer':
                        counterpart_aml_dict = self._get_shared_move_line_valss(credist,debits,  amount_currencys, move.id, False)
                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                        counterpart_aml_dict.update({'currency_id': currency_id})
                        counterpart_aml_dict.update({'account_id': id_account})
                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    else:
                        counterpart_aml_dict = self._get_shared_move_line_valss(debits,credits, amount_currencys, move.id, False)
                        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                        counterpart_aml_dict.update({'currency_id': currency_id})
                        counterpart_aml_dict.update({'account_id': id_account})
                        counterpart_aml = aml_obj.create(counterpart_aml_dict)
                
                    rec.add_variance_count = 1
            else:
                raise ValidationError(_("Please add the variance account"))

    
    
    @api.multi
    def get_outstanding_info(self):
        # self.outstanding_credits_debits_widget = json.dumps(False)
        
        com = self.env['payment.invoice.line.outstand']
        # if self.state == 'open':
        if self.invoice_lines:
            for l in self.invoice_lines:
                accountname = l.account_id.id
        else:
            if self.partner_type == 'customer':
                accountname = self.partner_id.property_account_receivable_id.id
            else:
                accountname = self.partner_id.property_account_payable_id.id
        domain = [('account_id', '=', accountname),('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),('reconciled', '=', False),'|','&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),'&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)]
        # if self.type in ('out_invoice', 'in_refund'):
        #     domain.extend([('credit', '>', 0), ('debit', '=', 0)])
        #     type_payment = _('Outstanding credits')
        # else:
        #     domain.extend([('credit', '=', 0), ('debit', '>', 0)])
        #     type_payment = _('Outstanding debits')
        info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
        
        lines = self.env['account.move.line'].search(domain)
        
        currency_id = self.currency_id
        
        if len(lines) != 0:
            for line in lines:
                # raise ValidationError(_(line))
                # get the outstanding residual value in invoice currency
                if line.currency_id and line.currency_id == self.currency_id:
                    amount_to_show = abs(line.amount_residual_currency)
                else:
                    currency = line.company_id.currency_id
                    amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id, self.company_id, line.date or fields.Date.today())
                if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                    continue
                if line.ref :
                    title = '%s' % (line.move_id.name)
                else:
                    title = line.move_id.name
                # info['content'].append({
                #     'journal_name': line.ref or line.move_id.name,
                #     'title': title,
                #     'amount': amount_to_show,
                #     'currency': currency_id.symbol,
                #     'id': line.id,
                #     'position': currency_id.position,
                #     'digits': [69, self.currency_id.decimal_places],
                # })
                # if line.payment_id:
                cov = com.search([('payment_id','=',self.id),('move_id','=',line.id)])
                if cov:
                    cov.write({'open_amount':amount_to_show,'allocation':amount_to_show})

                else:
                    if line.partner_id.id == self.partner_id.id:
                        if self.partner_type == 'customer':

                            if line.credit:
                                vals = {
                                    'payment_id':self.id,
                                    'title':title,
                                    'open_amount':amount_to_show,
                                    'allocation':amount_to_show,
                                    'move_id':line.id,
                                }
                        
                                cos = com.create(vals)
                        else:
                            if line.debit:
                                vals = {
                                    'payment_id':self.id,
                                    'title':title,
                                    'open_amount':amount_to_show,
                                    'allocation':amount_to_show,
                                    'move_id':line.id,
                                }
                        
                                cos = com.create(vals)
            
            self.add_variance_count = 1

    @api.multi
    def update_invoice_lines(self):
        for inv in self.invoice_lines:
            inv.open_amount = inv.invoice_id.residual 
        self.onchange_partner_id()
        self.get_outstanding_info()
                # raise ValidationError(_(cos.id))
                # info['title'] = type_payment
                # self.outstanding_credits_debits_widget = json.dumps(info)
                # self.has_outstanding = True

# class PaymentInvoiceLineCus(models.Model):
#     _inherit = 'payment.invoice.line'

#     move_id_outstand = fields.Many2one('account.move.line', string="Move Line")
#     outstand = fields.Boolean('Outstand allocation',default=False)


class PaymentInvoiceLineOutstand(models.Model):
    _name = 'payment.invoice.line.outstand'
    
    payment_id = fields.Many2one('account.payment', string="Payment")
    # invoice_id = fields.Many2one('account.invoice', string="Invoice")
    move_id = fields.Many2one('account.move.line', string="Move Line")
    title = fields.Char('Title')
    # account_id = fields.Many2one(related="invoice_id.account_id", string="Account")
    # currency = fields.Char('Currency')
    due_date = fields.Char('Due Date', compute='_get_invoice_data')
    amount = fields.Float('Total Amount', compute='_get_invoice_data')
    open_amount = fields.Float(string='Due Amount')
    allocation = fields.Float(string='Allocation ')
    
    # @api.multi
    # @api.onchange('open_amount')
    # def _get_invoice_data(self):
    #     for data in self:
    #         data.allocation = data.open_amount


    @api.multi
    @api.depends('move_id')
    def _get_invoice_data(self):
        for data in self:
            move_id = data.move_id
            data.due_date = move_id.date_maturity
            # data.open_amount = move_id.amount_residual
            # data.title = move_id.ref
            if move_id.debit :
                data.amount = move_id.debit 
            else:
                data.amount = move_id.credit
            # data.allocation = data.open_amount



    # @api.multi
    # def action_add(self):
    #     for rec in self:
    #         if rec.invoice_id:
    #             # cos = self.env['account.invoice'].search([('id','=',rec.invoice_id.id)])
    #             com = self.env['payment.invoice.line']
    #             vals={
    #                 'payment_id':rec.payment_id.id,
    #                 'invoice_id':rec.invoice_id.id,
    #                 'allocation':rec.amount,
    #                 'outstand':True,
    #                 'move_id_outstand': rec.move_id.id
    #             }
    #             com.create(vals)
    #             # mid = rec.move_id.id
    #             # cos.assign_outstanding_credit(mid)
    #             rec.unlink()
                
    #         else:
    #             raise ValidationError(_("Please add the invoice Number"))

class AccountJournalcus(models.Model):
    _inherit = 'account.journal'

    @api.multi
    def name_get(self):
        res = []
        for journal in self:
            # currency = journal.currency_id or journal.company_id.currency_id
            name = "%s" % (journal.name)
            res += [(journal.id, name)]
        return res

class BankDetails(models.Model):
    _name = 'bank.details'
    _inherit = 'mail.thread'

    name = fields.Many2one('account.journal',string='Bank Name',required=True,track_visibility="onchange")
    bank_name = fields.Char(string='Bank Name',required=True,track_visibility="onchange")
    branch = fields.Char('Branch',required=True,track_visibility="onchange")
    currency = fields.Many2one('res.currency',string='Currency Type')
    acc_no = fields.Char(string='Account No',required=True)
    ban = fields.Many2one('res.bank',related='name.bank_id',store=True,string='Account No')
    swift_code = fields.Char('Swift Code',required=True,track_visibility="onchange")
    iban = fields.Char('IBAN',required=True,track_visibility="onchange")

    @api.onchange('name')
    def _get_accdata(self):
        for rec in self:
            rec.acc_no = rec.name.bank_acc_number
            rec.currency = rec.name.currency_id.id

    @api.onchange('ban')
    def _get_swift(self):
        for rec in self:
            if rec.ban:
                rec.swift_code = rec.ban.bic
            else:
                continue

class AccountMoveCustomize(models.Model):
    _inherit = 'account.move'

    prepare = fields.Char('Prepared by')
    checked = fields.Char('Checked by')
    received = fields.Char('Received by')
    approved = fields.Char('Approved by')
    verified = fields.Char('Verified by')
    check_amount = fields.Float('Amount')
    partner = fields.Char(string="Partner Name")
    AC_print = fields.Boolean('Print A/c Payee')
    check_amount_in_words = fields.Char('amount in word',compute="_onchange_amount")
    document_count = fields.Integer(compute='_document_count', string='# Documents')
    

    @api.multi
    def _document_count(self):
        for each in self:
            document_ids = self.env['account.move.document'].sudo().search([('pay_ref', '=', each.id)])
            each.document_count = len(document_ids)

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [('pay_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'account.move.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_pay_ref': '%s'}" % self.id
        }


    @api.depends('check_amount','currency_id')
    @api.onchange('check_amount','currency_id')
    def _onchange_amount(self):
        # res = super(AccountMoveCustomize, self)._onchange_amount()
        self.check_amount_in_words = self.currency_id.amount_to_text(self.check_amount) if self.currency_id else ''
        self.check_amount_in_words = self.check_amount_in_words.replace(' Dirham ', ' ').replace(' Dirham',' ').replace(' And ',' ')

        # return res

    @api.constrains('line_ids', 'journal_id', 'auto_reverse', 'reverse_date')
    def _validate_move_modification(self):
        if 'posted' in self.mapped('line_ids.payment_id.state'):
            y = 1

    @api.model
    def create(self, vals):
        vals['prepare'] = self.env.user.name
        move = super(AccountMoveCustomize, self.with_context(check_move_validity=False, partner_id=vals.get('partner_id'))).create(vals)
        move.assert_balanced()
        return move

    @api.multi
    def write(self, vals):
        if vals.get('state') == 'posted':
            vals['approved'] = self.env.user.name
        if 'line_ids' in vals:
            res = super(AccountMoveCustomize, self.with_context(check_move_validity=False)).write(vals)
            self.assert_balanced()
        else:
            res = super(AccountMoveCustomize, self).write(vals)
        return res
            # raise ValidationError(_("You cannot modify a journal entry linked to a posted payment."))



class AccountMoveLineCus(models.Model):
    _inherit = 'account.move.line'
    
    def _check_reconcile_validity(self):
        #Perform all checks on lines
        company_ids = set()
        all_accounts = []
        for line in self:
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.matched_debit_ids or line.matched_credit_ids) and line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled.'))
        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries.'))
        # if len(set(all_accounts)) > 1:
        #     raise UserError(_('Entries are not from the same account.'))
        if not (all_accounts[0].reconcile or all_accounts[0].internal_type == 'liquidity'):
            raise UserError(_('Account %s (%s) does not allow reconciliation. First change the configuration of this account to allow it.') % (all_accounts[0].name, all_accounts[0].code))

# Accounts Customization Part

# Requisition Screen in Sales Module
class MaterialRequisitionFromsales(models.Model):
    _name = "material.requisition.sales"
    _inherit = 'mail.thread'
    _rec_name = 'sequence'


    sequence = fields.Char(string='Sequence', readonly=True,copy =False,track_visibility="onchange")
    sales_id = fields.Many2one('sale.order',string="SO Ref",track_visibility="onchange")
    oppor_id = fields.Many2one('crm.lead',string="Opportunity Ref",track_visibility="onchange")
    partner_id = fields.Many2one('res.partner',string="Customer",track_visibility="onchange")
    show_name = fields.Char('Show Name',track_visibility="onchange")
    requisition_date = fields.Date(string="Requisition Date",default=date.today(),track_visibility="onchange")
    requisition_dead = fields.Date(string="Requisition Deadline",track_visibility="onchange")
    state = fields.Selection([
                                ('new','New'),
                                ('po_created','Purchase Department'),
                                ('back','Responded'),
                                ('cancel','Cancel')],string='Stage',default="new",track_visibility="onchange")
    requisition_line_ids = fields.One2many('material.requisition.sales.line','requisition_id',string="Requisition Line ID")    
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    total_price = fields.Float(string="Total",compute="_get_total")
    flag = fields.Boolean(string="flag",default=False)

    @api.multi
    @api.depends('requisition_line_ids')
    def _get_total(self):
        for rec in self:
            x = 0.0
            for l in rec.requisition_line_ids:
                x = x + l.total_price 
            rec.total_price = x

    @api.constrains('requisition_line_ids')
    def check_inv_date(self):
        for rec in self:
            if rec.requisition_line_ids:
                if rec.state == 'back':
                    for l in rec.requisition_line_ids:
                        if l.price:
                            continue
                        else:
                            raise ValidationError(_("add a price for product %s")% (l.product_id.name))
            else:
                raise ValidationError(_("Add some products"))
            

    @api.model
    def create(self , vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('material.requisition.sales') or '/'
        return super(MaterialRequisitionFromsales, self).create(vals)

    @api.multi
    def action_cancel(self):
        res = self.write({
                            'state':'cancel',
                        })
        return res  

    @api.multi
    def action_to_po(self):
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_employees_pur').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_applicant_tender').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            channel_id.message_post(body='Hello, there is New Price inguiry Created for you Please Check the Price Inquiry NO '+str(self.sequence), subject='New Price inquiry',subtype='mail.mt_comment')
            
        res = self.write({
                            'state':'po_created',
                        })
        return res  

    @api.multi
    def action_pricing(self):
        if self.state == 'po_created':
            for l in self.requisition_line_ids:
                if l.price:
                    continue
                else:
                    raise ValidationError(_("add a price for product %s")% (l.product_id.name))
            channel_all_employees = self.env.ref('marcoms_updates.channel_all_Price_inquiries').read()[0]
            template_new_employee = self.env.ref('marcoms_updates.email_template_data_Price_inquiries_Response').read()[0]
            # raise ValidationError(_(template_new_employee))
            if template_new_employee:
                # MailTemplate = self.env['mail.template']
                body_html = template_new_employee['body_html']
                subject = template_new_employee['subject']
                # raise ValidationError(_('%s %s ') % (body_html,subject))
                ids = channel_all_employees['id']
                channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                channel_id.message_post(body='Hello, the Purchase team response to the Price Inquiry NO '+str(self.sequence), subject='Price inquiry Response',subtype='mail.mt_comment')
                
            res = self.write({
                                'state':'back',
                            })
            return res  

    @api.multi
    def create_purchase_requisition(self):
        task_id = []
        purchase_req_obj = self.env['purchase.requisition']
        purchase_req_line_obj = self.env['purchase.requisition.line']
        for res in self:
            req_vals = purchase_req_obj.create({
                                            'requisition_so_id':res.id,
                                            'state':'draft',
                                            'origin':res.sequence,
                                            })
        for line in self.requisition_line_ids:  
            req_line_vals = purchase_req_line_obj.create({
                'product_id':line.product_id.id,
                'product_qty':line.qty,
                'product_uom_id':line.uom_id.id,
                'requisition_id':req_vals.id,
                })
        self.write({
                            'flag':True,
                        })

class RequisitionSalesLine(models.Model):
    _name = "material.requisition.sales.line"
    _rec_name = 'requisition_id'

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name


    product_id = fields.Many2one('product.product',string="Product",required=True)
    description = fields.Text(string="Description")
    qty = fields.Float(string="Quantity",default=1.0)
    uom_id = fields.Many2one('uom.uom',string="Unit Of Measure")
    requisition_id = fields.Many2one('material.requisition.sales',string="Requisition Line")
    available_qty = fields.Float(string="Available Qty")
    price = fields.Float(string="Unit price")
    total_price = fields.Float(string="Total",compute="_get_total")
    remarks = fields.Text(string="Remarks")

    @api.multi
    @api.depends('price')
    @api.onchange('price','qty')
    def _get_total(self):
        for rec in self:
            rec.total_price = rec.price * rec.qty

# class MaterialRequisitionUpdate(models.Model):
#     _inherit = "material.requisition"

    
#     @api.multi
#     def create_purchase_requisition(self):
#         task_id = []
#         purchase_req_obj = self.env['purchase.requisition']
#         purchase_req_line_obj = self.env['purchase.requisition.line']
#         for res in self:
#             req_vals = purchase_req_obj.create({
#                                             'analytic_id': res.analytic_id.id,
#                                             'task_id': res.task_id.id,
#                                             'requisition_mat_po_id':res.id,
#                                             'origin':res.sequence,
#                                             })
#         for line in self.requisition_line_ids:  
#             req_line_vals = purchase_req_line_obj.create({
#                 'product_id':line.product_id.id,
#                 'product_qty':line.qty,
#                 'product_uom_id':line.uom_id.id,
#                 'requisition_id':req_vals.id,

#                 })
#         res = self.write({
#                             'state':'po_created',
#                         })
#         return res 
# Requisition Screen in Sales Module

class mailactivityUpdate(models.Model):
    _inherit = "mail.activity"

    @api.constrains('date_deadline')
    def check_inv_date(self):
        for rec in self:
            if rec.date_deadline:
                if date.today() > rec.date_deadline:
                    raise ValidationError(_("Due Date should be equal or bigger than today date"))
            

class hrleaveUpdate(models.Model):
    _inherit = "hr.leave"

    @api.multi
    def action_approve(self):
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()

        channel_all_employees = self.env.ref('marcoms_updates.channel_all_leave_status').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_applicant_leaves').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            message = """Leave with type %s come From %s in %s department between dates  %s to %s 
            get Approved by %s """  % (self.holiday_status_id.name, self.employee_id.name, self.department_id.name,self.request_date_from,self.request_date_to,self.env.user.name)
            channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
            
        return True


    @api.multi
    def action_refuse(self):
        
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1']:
                raise UserError(_('Leave request must be confirmed or validated in order to refuse it.'))

            if holiday.state == 'validate1':
                holiday.write({'state': 'refuse', 'first_approver_id': current_employee.id})
                channel_all_employees = self.env.ref('marcoms_updates.channel_all_leave_status').read()[0]
                template_new_employee = self.env.ref('marcoms_updates.email_template_data_applicant_leaves').read()[0]
                # raise ValidationError(_(template_new_employee))
                if template_new_employee:
                    # MailTemplate = self.env['mail.template']
                    body_html = template_new_employee['body_html']
                    subject = template_new_employee['subject']
                    # raise ValidationError(_('%s %s ') % (body_html,subject))
                    ids = channel_all_employees['id']
                    channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                    message = """Leave with type %s come From %s in %s department between dates  %s to %s 
                    get Refused by %s """  % (self.holiday_status_id.name, self.employee_id.name, self.department_id.name,self.request_date_from,self.request_date_to,self.env.user.name)
                    channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
                    
            else:
                holiday.write({'state': 'refuse', 'second_approver_id': current_employee.id})
                channel_all_employees = self.env.ref('marcoms_updates.channel_all_leave_status').read()[0]
                template_new_employee = self.env.ref('marcoms_updates.email_template_data_applicant_leaves').read()[0]
                # raise ValidationError(_(template_new_employee))
                if template_new_employee:
                    # MailTemplate = self.env['mail.template']
                    body_html = template_new_employee['body_html']
                    subject = template_new_employee['subject']
                    # raise ValidationError(_('%s %s ') % (body_html,subject))
                    ids = channel_all_employees['id']
                    channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                    message = """Leave with type %s come From %s in %s department between dates  %s to %s 
                    get Refused by %s """  % (self.holiday_status_id.name, self.employee_id.name, self.department_id.name,self.request_date_from,self.request_date_to,self.env.user.name)
                    channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
                    
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        self._remove_resource_leave()
        self.activity_update()
        
        return True


class stockwarehouseorderpointUpdate(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    onhand_qty = fields.Float('Onhand',compute="_get_diff_data")
    deff_qty = fields.Float('Variance',compute="_get_diff_data")

    @api.multi
    @api.depends('product_id')
    def _get_diff_data(self):
        for rec in self:
            rec.onhand_qty = rec.product_id.qty_available
            rec.deff_qty = rec.onhand_qty - rec.product_min_qty


class respartnerUpdate(models.Model):
    _inherit = "res.partner"
    
    sequence_no = fields.Char('Partner No', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'),track_visibility="onchange")
    

    @api.model_create_multi
    def create(self, vals_list):
           
        if self.env.context.get('import_file'):
            self._check_import_consistency(vals_list)
        for vals in vals_list:
            if vals.get('sequence_no', _('New')) == _('New'):
                vals['sequence_no'] = self.env['ir.sequence'].next_by_code('res.partner') or 'New'
            if vals.get('website'):
                vals['website'] = self._clean_website(vals['website'])
            if vals.get('parent_id'):
                vals['company_name'] = False
            # compute default image in create, because computing gravatar in the onchange
            # cannot be easily performed if default images are in the way
            if not vals.get('image'):
                vals['image'] = self._get_default_image(vals.get('type'), vals.get('is_company'), vals.get('parent_id'))
            tools.image_resize_images(vals, sizes={'image': (1024, None)})
        partners = super(respartnerUpdate, self).create(vals_list)

        channel_all_employees = self.env.ref('marcoms_updates.channel_all_new_customer').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_new_customer').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """Hello, there are New Customer Added to customer lists with name %s and code %s"""% (vals['name'],vals['sequence_no'])
            channel_id.message_post(body=body, subject='New Customer Added',subtype='mail.mt_comment')
        

        if self.env.context.get('_partners_skip_fields_sync'):
            return partners

        for partner, vals in pycompat.izip(partners, vals_list):
            partner._fields_sync(vals)
            partner._handle_first_contact_creation()
        return partners

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name')
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=False, show_code=False)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            partner.display_name = names.get(partner.id)

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name

        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = "%s ,%s" % (partner.commercial_company_name or partner.parent_id.name,name)
            
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('address_inline'):
            name = name.replace('\n', ', ')
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('show_code') and partner.sequence_no:
            name = "%s - %s" % (name, partner.sequence_no)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name

# Ledger Report Updates

class AccountReportcus(models.AbstractModel):
    _inherit = 'account.report'

    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Check the security before updating the context to make sure the options are safe.
        self._check_report_security(options)

        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)
        report = {'name': self._get_report_name(),
                'summary': report_manager.summary,
                'company_name': self.env.user.company_id.name,
                'yo_date': date.today(),
                'company_zip': self.env.user.company_id.zip,
                'company_street': self.env.user.company_id.street,
                'company_currency': self.env.user.company_id.currency_id.name,
                'company_currencylabel': self.env.user.company_id.currency_id.currency_unit_label,
                'company_tel': self.env.user.company_id.phone,
                }
        lines = self._get_lines(options, line_id=line_id)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines)

        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        rcontext = {'report': report,
                    'lines': {'columns_header': self.get_header(options), 'lines': lines},
                    'options': options,
                    'context': self.env.context,
                    'model': self,
                }
        if additional_context and type(additional_context) == dict:
            rcontext.update(additional_context)
        if self.env.context.get('analytic_account_ids'):
            rcontext['options']['analytic_account_ids'] = [
                {'id': acc.id, 'name': acc.name} for acc in self.env.context['analytic_account_ids']
            ]

        render_template = templates.get('main_template', 'acc_pi.main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'acc_pi.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k,v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html

    
    def get_report_informations(self, options):
        '''
        return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        options = self._get_options(options)
        # apply date and date_comparison filter
        self._apply_date_filter(options)

        searchview_dict = {'options': options, 'context': self.env.context}
        # Check if report needs analytic
        if options.get('analytic_accounts') is not None:
            searchview_dict['analytic_accounts'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.account'].search([])] or False
            options['selected_analytic_account_names'] = [self.env['account.analytic.account'].browse(int(account)).name for account in options['analytic_accounts']]
        if options.get('analytic_tags') is not None:
            searchview_dict['analytic_tags'] = self.env.user.id in self.env.ref('analytic.group_analytic_tags').users.ids and [(t.id, t.name) for t in self.env['account.analytic.tag'].search([])] or False
            options['selected_analytic_tag_names'] = [self.env['account.analytic.tag'].browse(int(tag)).name for tag in options['analytic_tags']]
        if options.get('partner'):
            options['selected_partner_ids'] = [str(self.env['res.partner'].browse(int(partner)).name) +' ,  '+ str(self.env['res.partner'].browse(int(partner)).sequence_no) for partner in options['partner_ids']]
            options['partner_zip'] = [self.env['res.partner'].browse(int(partner)).zip for partner in options['partner_ids']]
            options['partner_code'] = [self.env['res.partner'].browse(int(partner)).sequence_no for partner in options['partner_ids']]
            options['selected_phone'] = [self.env['res.partner'].browse(int(partner)).phone for partner in options['partner_ids']]
            options['selected_street'] = [self.env['res.partner'].browse(int(partner)).street for partner in options['partner_ids']]
            options['selected_partner_categories'] = [self.env['res.partner.category'].browse(int(category)).name for category in options['partner_categories']]

        # Check whether there are unposted entries for the selected period or not (if the report allows it)
        if options.get('date') and options.get('all_entries') is not None:
            date_to = options['date'].get('date_to') or options['date'].get('date') or fields.Date.today()
            period_domain = [('state', '=', 'draft'), ('date', '<=', date_to)]
            options['unposted_in_period'] = bool(self.env['account.move'].search_count(period_domain))

        report_manager = self._get_report_manager(options)
        info = {'options': options,
                'context': self.env.context,
                'report_manager_id': report_manager.id,
                'footnotes': [{'id': f.id, 'line': f.line, 'text': f.text} for f in report_manager.footnotes_ids],
                'buttons': self._get_reports_buttons(),
                'main_html': self.get_html(options),
                'searchview_html': self.env['ir.ui.view'].render_template(self._get_templates().get('search_template', 'account_report.search_template'), values=searchview_dict),
                }
        return info


# class report_account_general_ledgercus(models.AbstractModel):
#     _inherit = "account.general.ledger"

#     @api.model
#     def _get_report_name(self):
#         return _("STATEMENT OF ACCOUNTS")



class ReportPartnerLedgercus(models.AbstractModel):
    _inherit = "account.partner.ledger"

    @api.model
    def _get_report_name(self):
        return _('STATEMENT OF ACCOUNTS')

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Project Name')},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Days')},
            {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})
        

        return columns


    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        if line_id:
            line_id = int(line_id.split('_')[1]) or None
        elif options.get('partner_ids') and len(options.get('partner_ids')) == 1:
            #If a default partner is set, we only want to load the line referring to it.
            partner_id = options['partner_ids'][0]
            line_id = partner_id
        if line_id:
            if 'partner_' + str(line_id) not in options.get('unfolded_lines', []):
                options.get('unfolded_lines', []).append('partner_' + str(line_id))

        grouped_partners = self._group_by_partner_id(options, line_id)
        sorted_partners = sorted(grouped_partners, key=lambda p: p.name or '')
        unfold_all = context.get('print_mode') and not options.get('unfolded_lines')
        total_initial_balance = total_debit = total_credit = total_balance = 0.0
        for partner in sorted_partners:
            debit = grouped_partners[partner]['debit']
            credit = grouped_partners[partner]['credit']
            balance = grouped_partners[partner]['balance']
            initial_balance = grouped_partners[partner]['initial_bal']['balance']
            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance
            days = 'days'
            columns = [self.format_value(initial_balance), self.format_value(debit), self.format_value(credit)]
            if self.user_has_groups('base.group_multi_currency'):
                columns.append('')
            columns.append(self.format_value(balance))
            
            # don't add header for `load more`
            if offset == 0:
                lines.append({
                    'id': 'partner_' + str(partner.id),
                    'name': partner.name,
                    'columns': [{'name': v} for v in columns],
                    'level': 2,
                    'trust': partner.trust,
                    'unfoldable': True,
                    'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
                    'colspan': 8,
                })
            user_company = self.env.user.company_id
            used_currency = user_company.currency_id
            if 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all:
                if offset == 0:
                    progress = initial_balance
                else:
                    progress = float(options.get('lines_progress', initial_balance))
                domain_lines = []
                amls = grouped_partners[partner]['lines']

                remaining_lines = 0
                if not context.get('print_mode'):
                    remaining_lines = grouped_partners[partner]['total_lines'] - offset - len(amls)

                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    date = amls.env.context.get('date') or fields.Date.today()
                    line_currency = line.company_id.currency_id
                    line_debit = line_currency._convert(line_debit, used_currency, user_company, date)
                    line_credit = line_currency._convert(line_credit, used_currency, user_company, date)
                    progress_before = progress
                    progress = progress + line_debit - line_credit
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'

                    if line.invoice_id:
                        if line.invoice_id.project:
                            project_name = """[%s]%s""" % (line.invoice_id.project.code,line.invoice_id.project.name)
                        else:
                            project_name = ''
                    else:
                        if line.analytic_account_id.code or line.analytic_account_id.name:
                            project_name = ''
                            project_name = """[%s]%s""" % (line.analytic_account_id.code,line.analytic_account_id.name)
                        else:
                            project_name = ''
                    days =  (line.date_maturity - line.move_id.date).days
                    domain_columns = [line.journal_id.code, line.account_id.code,self._format_aml_name(line),project_name, 
                                      line.date_maturity and format_date(self.env, line.date_maturity) or '',days,
                                      line.full_reconcile_id.name or '', self.format_value(progress_before),
                                      line_debit != 0 and self.format_value(line_debit) or '',
                                      line_credit != 0 and self.format_value(line_credit) or '']
                    if self.user_has_groups('base.group_multi_currency'):
                        domain_columns.append(self.with_context(no_format=False).format_value(line.amount_currency, currency=line.currency_id) if line.amount_currency != 0 else '')
                    domain_columns.append(self.format_value(progress))
                    columns = [{'name': v} for v in domain_columns]
                    columns[3].update({'class': 'date'})
                    domain_lines.append({
                        'id': line.id,
                        'parent_id': 'partner_' + str(partner.id),
                        'name': format_date(self.env, line.date),
                        'class': 'date',
                        'columns': columns,
                        'caret_options': caret_type,
                        'level': 4,
                    })

                # load more
                if remaining_lines > 0:
                    domain_lines.append({
                        'id': 'loadmore_%s' % partner.id,
                        'offset': offset + self.MAX_LINES,
                        'progress': progress,
                        'class': 'o_account_reports_load_more text-center',
                        'parent_id': 'partner_%s' % partner.id,
                        'name': _('Load more... (%s remaining)') % remaining_lines,
                        'colspan': 10 if self.user_has_groups('base.group_multi_currency') else 9,
                        'columns': [{}],
                    })
                lines += domain_lines

        if not line_id:
            total_columns = ['', '', '', '', '','', '', self.format_value(total_initial_balance), self.format_value(total_debit), self.format_value(total_credit)]
            if self.user_has_groups('base.group_multi_currency'):
                total_columns.append('')
            total_columns.append(self.format_value(total_balance))
            lines.append({
                'id': 'grouped_partners_total',
                'name': _('Total'),
                'level': 0,
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in total_columns],
            })
        return lines



# expense changes
class hrexpenseUpdate(models.Model):
    _inherit = "hr.expense"

    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', states={'done': [('readonly', True)], 'post': [('readonly', True)], 'submitted': [('readonly', True)]}, string="Paid By")
    is_vendor = fields.Boolean('Is Vendor Expense',default=False)
    vendor_id = fields.Many2one('res.partner','Vendor')
    # employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_employee_id, domain=lambda self: self._get_employee_id_domain())
    
    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_is_vendor': self.is_vendor,
                'default_vendor_id': self.vendor_id.id,
                'default_name': todo[0].name if len(todo) == 1 else ''
            }
        }

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            if expense.is_vendor == False:
                move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
                partner_id = expense.employee_id.address_home_id.commercial_partner_id.id
            else:
                move_line_name = expense.vendor_id.name + ': ' + expense.name.split('\n')[0][:64]
                partner_id = expense.vendor_id.id
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount -= move_line_src['debit']
            total_amount_currency -= move_line_src['amount_currency'] or move_line_src['debit']

            # taxes move lines
            for tax in taxes['taxes']:
                amount = tax['amount']
                amount_currency = False
                if different_currency:
                    amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                    amount_currency = tax['amount']
                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                    'amount_currency': amount_currency if different_currency else 0.0,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_line_id': tax['id'],
                    'expense_id': expense.id,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id if different_currency else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense



    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                if expense.is_vendor == False:
                    payment = self.env['account.payment'].create({
                        'payment_method_id': payment_methods and payment_methods[0].id or False,
                        'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                        'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                        'partner_type': 'supplier',
                        'journal_id': journal.id,
                        'payment_date': expense.date,
                        'state': 'reconciled',
                        'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                        'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                        'name': expense.name,
                    })
                else:
                    payment = self.env['account.payment'].create({
                        'payment_method_id': payment_methods and payment_methods[0].id or False,
                        'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                        'partner_id': expense.vendor_id.id,
                        'partner_type': 'supplier',
                        'journal_id': journal.id,
                        'payment_date': expense.date,
                        'state': 'reconciled',
                        'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                        'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                        'name': expense.name,
                    })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.with_context(dont_create_taxes=True).write({
                'line_ids': [(0, 0, line) for line in move_line_values]
            })
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

        # post the moves
        for move in move_group_by_sheet.values():
            move.post()

        return move_group_by_sheet

class hrexpenseSheetUpdate(models.Model):
    _inherit = "hr.expense.sheet"

    is_vendor = fields.Boolean('Is Vendor Expense',default=False)
    vendor_id = fields.Many2one('res.partner','Vendor')
# expense changes

# Accounts report changes
class report_account_aged_partner_cus(models.AbstractModel):
    _inherit = "account.aged.partner"

    def _get_columns_name(self, options):
        columns = [{}]
        columns += [
            {'name': v, 'class': 'number', 'style': 'white-space:nowrap;'}
            for v in [_("JRNL"), _("Account"),_("Project Name"), _("Reference"), _("Not due on: %s") % format_date(self.env, options['date']['date']),
                      _("1 - 30"), _("31 - 60"), _("61 - 90"), _("91 - 120"), _("Older"), _("Total")]
        ]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 4 + [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'],
                                                                                                 values['3'], values['2'],
                                                                                                 values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    if aml.invoice_id:
                        if aml.invoice_id.project:
                            project_name = """[%s]%s""" % (aml.invoice_id.project.code,aml.invoice_id.project.name)
                        else:
                            project_name = ''
                    else:
                        if aml.analytic_account_id.code or aml.analytic_account_id.name:
                            project_name = ''
                            project_name = """[%s]%s""" % (aml.analytic_account_id.code,aml.analytic_account_id.name)
                        else:
                            project_name = ''
                    vals = {
                        'id': aml.id,
                        'name': format_date(self.env, aml.date_maturity or aml.date),
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [aml.journal_id.code, aml.account_id.code,project_name , self._format_aml_name(aml)]] +\
                                   [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7)]],
                        'action_context': aml.get_action_context(),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 4 + [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines


class report_account_general_ledger_cus(models.AbstractModel):
    _inherit = "account.general.ledger"

    def _get_columns_name(self, options):
        return [{'name': ''},
                {'name': _("Date"), 'class': 'date'},
                {'name': _("Communication")},
                {'name': _("Partner")},
                {'name': _("Project Name")},
                {'name': _("Currency"), 'class': 'number'},
                {'name': _("Debit"), 'class': 'number'},
                {'name': _("Credit"), 'class': 'number'},
                {'name': _("Balance"), 'class': 'number'}]

    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        lines = []
        context = self.env.context
        company_id = self.env.user.company_id
        used_currency = company_id.currency_id
        dt_from = options['date'].get('date_from')
        line_id = line_id and int(line_id.split('_')[1]) or None
        aml_lines = []
        # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
        grouped_accounts = self.with_context(date_from_aml=dt_from, date_from=dt_from and company_id.compute_fiscalyear_dates(fields.Date.from_string(dt_from))['date_from'] or None)._group_by_account_id(options, line_id)
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        unfold_all = context.get('print_mode') and len(options.get('unfolded_lines')) == 0
        sum_debit = sum_credit = sum_balance = 0
        for account in sorted_accounts:
            display_name = account.code + " " + account.name
            if options.get('filter_accounts'):
                #skip all accounts where both the code and the name don't start with the given filtering string
                if not any([display_name_part.lower().startswith(options['filter_accounts'].lower()) for display_name_part in display_name.split(' ')]):
                    continue
            debit = grouped_accounts[account]['debit']
            credit = grouped_accounts[account]['credit']
            balance = grouped_accounts[account]['balance']
            sum_debit += debit
            sum_credit += credit
            sum_balance += balance
            amount_currency = '' if not account.currency_id else self.with_context(no_format=False).format_value(grouped_accounts[account]['amount_currency'], currency=account.currency_id)
            # don't add header for `load more`
            if offset == 0:
                lines.append({
                    'id': 'account_%s' % (account.id,),
                    'name': len(display_name) > 40 and not context.get('print_mode') and display_name[:40]+'...' or display_name,
                    'title_hover': display_name,
                    'columns': [{'name': v} for v in [amount_currency, self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': 'account_%s' % (account.id,) in options.get('unfolded_lines') or unfold_all,
                    'colspan': 5,
                })
            if 'account_%s' % (account.id,) in options.get('unfolded_lines') or unfold_all:
                initial_debit = grouped_accounts[account]['initial_bal']['debit']
                initial_credit = grouped_accounts[account]['initial_bal']['credit']
                initial_balance = grouped_accounts[account]['initial_bal']['balance']
                initial_currency = '' if not account.currency_id else self.with_context(no_format=False).format_value(grouped_accounts[account]['initial_bal']['amount_currency'], currency=account.currency_id)

                domain_lines = []
                if offset == 0:
                    domain_lines.append({
                        'id': 'initial_%s' % (account.id,),
                        'class': 'o_account_reports_initial_balance',
                        'name': _('Initial Balance'),
                        'parent_id': 'account_%s' % (account.id,),
                        'columns': [{'name': v} for v in ['', '', '', initial_currency, self.format_value(initial_debit), self.format_value(initial_credit), self.format_value(initial_balance)]],
                    })
                    progress = initial_balance
                else:
                    # for load more:
                    progress = float(options.get('lines_progress', initial_balance))

                amls = grouped_accounts[account]['lines']

                remaining_lines = 0
                if not context.get('print_mode'):
                    remaining_lines = grouped_accounts[account]['total_lines'] - offset - len(amls)


                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    date = amls.env.context.get('date') or fields.Date.today()
                    line_debit = line.company_id.currency_id._convert(line_debit, used_currency, company_id, date)
                    line_credit = line.company_id.currency_id._convert(line_credit, used_currency, company_id, date)
                    progress = progress + line_debit - line_credit
                    currency = "" if not line.currency_id else self.with_context(no_format=False).format_value(line.amount_currency, currency=line.currency_id)

                    name = line.name and line.name or ''
                    if line.ref:
                        name = name and name + ' - ' + line.ref or line.ref
                    name_title = name
                    # Don't split the name when printing
                    if len(name) > 35 and not self.env.context.get('no_format') and not self.env.context.get('print_mode'):
                        name = name[:32] + "..."
                    partner_name = line.partner_id.name
                    partner_name_title = partner_name
                    if partner_name and len(partner_name) > 35  and not self.env.context.get('no_format') and not self.env.context.get('print_mode'):
                        partner_name = partner_name[:32] + "..."
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    if line.invoice_id:
                        if line.invoice_id.project:
                            project_name = """[%s]%s""" % (line.invoice_id.project.code,line.invoice_id.project.name)
                        else:
                            project_name = ''
                    else:
                        if line.analytic_account_id.code or line.analytic_account_id.name:
                            project_name = ''
                            project_name = """[%s]%s""" % (line.analytic_account_id.code,line.analytic_account_id.name)
                        else:
                            project_name = ''
                    columns = [{'name': v} for v in [format_date(self.env, line.date), name, partner_name,project_name, currency,
                                    line_debit != 0 and self.format_value(line_debit) or '',
                                    line_credit != 0 and self.format_value(line_credit) or '',
                                    self.format_value(progress)]]
                    columns[1]['class'] = 'whitespace_print'
                    columns[2]['class'] = 'whitespace_print'
                    columns[1]['title'] = name_title
                    columns[2]['title'] = partner_name_title
                    line_value = {
                        'id': line.id,
                        'caret_options': caret_type,
                        'class': 'top-vertical-align',
                        'parent_id': 'account_%s' % (account.id,),
                        'name': line.move_id.name if line.move_id.name else '/',
                        'columns': columns,
                        'level': 4,
                    }
                    aml_lines.append(line.id)
                    domain_lines.append(line_value)

                # load more
                if remaining_lines > 0:
                    domain_lines.append({
                        'id': 'loadmore_%s' % account.id,
                        # if MAX_LINES is None, there will be no remaining lines
                        # so this should not cause a problem
                        'offset': offset + self.MAX_LINES,
                        'progress': progress,
                        'class': 'o_account_reports_load_more text-center',
                        'parent_id': 'account_%s' % (account.id,),
                        'name': _('Load more... (%s remaining)') % remaining_lines,
                        'colspan': 8,
                        'columns': [{}],
                    })
                # don't add total line for `load more`
                if offset == 0:
                    domain_lines.append({
                        'id': 'total_' + str(account.id),
                        'class': 'o_account_reports_domain_total',
                        'parent_id': 'account_%s' % (account.id,),
                        'name': _('Total '),
                        'columns': [{'name': v} for v in ['', '', '','', amount_currency, self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                    })

                lines += domain_lines

        if not line_id:

            lines.append({
                'id': 'general_ledger_total_%s' % company_id.id,
                'name': _('Total'),
                'class': 'total',
                'level': 1,
                'columns': [{'name': v} for v in ['', '', '', '','', self.format_value(sum_debit), self.format_value(sum_credit), self.format_value(sum_balance)]],
            })

        journals = [j for j in options.get('journals') if j.get('selected')]
        if len(journals) == 1 and journals[0].get('type') in ['sale', 'purchase'] and not line_id:
            lines.append({
                'id': 0,
                'name': _('Tax Declaration'),
                'columns': [{'name': v} for v in ['', '', '', '', '', '', '']],
                'level': 1,
                'unfoldable': False,
                'unfolded': False,
            })
            lines.append({
                'id': 0,
                'name': _('Name'),
                'columns': [{'name': v} for v in ['', '', '', '', _('Base Amount'), _('Tax Amount'), '']],
                'level': 2,
                'unfoldable': False,
                'unfolded': False,
            })
            journal_currency = self.env['account.journal'].browse(journals[0]['id']).company_id.currency_id
            for tax, values in self._get_taxes(journals[0]).items():
                base_amount = journal_currency._convert(values['base_amount'], used_currency, company_id, options['date']['date_to'])
                tax_amount = journal_currency._convert(values['tax_amount'], used_currency, company_id, options['date']['date_to'])
                lines.append({
                    'id': '%s_tax' % (tax.id,),
                    'name': tax.name + ' (' + str(tax.amount) + ')',
                    'caret_options': 'account.tax',
                    'unfoldable': False,
                    'columns': [{'name': v} for v in [self.format_value(base_amount), self.format_value(tax_amount), '']],
                    'colspan': 5,
                    'level': 4,
                })

        if self.env.context.get('aml_only', False):
            return aml_lines
        return lines


# Accounts report changes

class account_abstract_payment_cus(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            if self.payment_type == 'inbound' and not self.payment_type == 'outbound':
                payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids 
                payment_methods_list = payment_methods.ids
            if self.payment_type == 'outbound' and not self.payment_type == 'inbound':
                payment_methods = self.payment_type == 'outbound' and self.journal_id.outbound_payment_method_ids
                payment_methods_list = payment_methods.ids
            # if self.payment_type == 'outbound' and self.payment_type == 'inbound':
            #     payment_methods = self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            #     payment_methods_list = payment_methods.ids

            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                # Ensure the domain will accept the provided default value
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False

            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}}
        return {}

class AssetsTracking(models.Model):
    _name = "asset.tracking"
    _inherit = 'mail.thread'

    name = fields.Char('Sequence' ,required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'),track_visibility="onchange")
    asset_name = fields.Many2one('account.asset.asset',string='Asset Name',track_visibility="onchange")
    asset_category = fields.Many2one('account.asset.category',string='Asset Category')
    transfer_date = fields.Date('Transfer Date',default=date.today(),track_visibility="onchange")
    asset_responsible = fields.Many2one('hr.employee',string='Asset Responsible',track_visibility="onchange")
    from_project = fields.Many2one('account.analytic.account',string='From',track_visibility="onchange")
    to_project = fields.Many2one('account.analytic.account',string='To',track_visibility="onchange")
    Remarks = fields.Text('Remarks')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    @api.onchange('asset_name')
    def get_category(self):
        for rec in self:
            rec.asset_category = rec.asset_name.category_id.id

    @api.multi
    def action_confirm(self):
        self.write({
            'state':'confirm'
        })

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.tracking') or 'New'   
        return super(AssetsTracking, self).create(vals)


class AssetsCus(models.Model):
    _inherit = 'account.asset.asset'

    tracking_id = fields.One2many('asset.tracking','asset_name',string="Tracking Line")

class PaymentRequest(models.Model):
    _name = 'payment.request'
    _inherit = 'mail.thread'

    name = fields.Char('Sequence' ,required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'),track_visibility="onchange")    
    lpo_num = fields.Many2one('purchase.order',string="LPO")
    company = fields.Many2one('res.partner',string="Company")
    payment_term = fields.Many2one('account.payment.term',string="Payment Term")
    amount = fields.Float('Amount')
    prepared = fields.Many2one('res.users',string="Prepared By")
    approved = fields.Many2one('res.users',string="Approved By")
    account_approve = fields.Many2one('res.users',string="Accounts Approved By")
    project = fields.Many2one('account.analytic.account',string="Projects")
    department_manager_comment = fields.Text(string="Department Manager Comment")
    account_comment = fields.Text(string="Accounts Comment")
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Department Approval', 'Department Manager Approval'),
        ('Accounts Approval', 'Accounts Approval'),
        ('Department Reject', 'Department Manager Rejected'),
        ('Accounts Reject', 'Accounts Rejected'),
        ('Approved', 'Approved'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='Draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('payment.request') or 'New'   
        return super(PaymentRequest, self).create(vals)

    @api.onchange('lpo_num')
    def _get_data(self):
        for rec in self:
            rec.company = rec.lpo_num.partner_id.id
            rec.payment_term = rec.lpo_num.payment_term_id.id
            rec.amount = rec.lpo_num.amount_total
            rec.project = rec.lpo_num.analytic_id.id

    @api.multi
    def action_confirm(self):
        self.write({'state':'Department Approval','prepared':self.env.user.id})
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """Hello, Payment Request with number %s Sending to purchase department approval"""% (self.name)
            channel_id.message_post(body=body, subject='Payment Request',subtype='mail.mt_comment')

    @api.multi
    def action_department_approve(self):
        self.write({'state':'Accounts Approval','approved':self.env.user.id})
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_to_approve_payment_request').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_to_approve_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s waiting for accounts approval"""% (self.name)
            channel_id.message_post(body=body, subject='Payment Request',subtype='mail.mt_comment')

    @api.multi
    def action_department_reject(self):
        self.write({'state':'Department Reject'})
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s get rejected by the purchase department manager"""% (self.name)
            channel_id.message_post(body=body, subject='Payment Request',subtype='mail.mt_comment')

    @api.multi
    def action_accounts_approve(self):
        self.write({'state':'Approved','account_approve':self.env.user.id})
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s is approved by the accounts team"""% (self.name)
            channel_id.message_post(body=body, subject='Payment Request',subtype='mail.mt_comment')

    @api.multi
    def action_accounts_reject(self):
        self.write({'state':'Accounts Reject'})
        channel_all_employees = self.env.ref('marcoms_updates.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('marcoms_updates.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s is rejected by the accounts team"""% (self.name)
            channel_id.message_post(body=body, subject='Payment Request',subtype='mail.mt_comment')

    @api.multi
    def set_to_draft(self):
        self.write({'state':'Draft','account_approve':False,'approved':False})