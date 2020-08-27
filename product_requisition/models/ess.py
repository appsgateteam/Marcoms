# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools ,_
from odoo.exceptions import except_orm, ValidationError,UserError
from odoo.exceptions import  AccessError, UserError, RedirectWarning,Warning
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.exceptions
import re 

class PurchaseRequisitionCus2(models.Model):
    _inherit = 'purchase.requisition'


    requisition_pr_id = fields.Many2one('product.requisition',string="Product Requisition")
    pro_requi = fields.Boolean('product Requisition',default=False)
    pr_sequence = fields.Many2one('product.requisition',string='Sequence', readonly=True)
    creator_name = fields.Many2one('res.users',string='Requester Name',readonly=True)
    pr_sequence_id = fields.Integer(string='Sequence',compute='_get_id', readonly=True)
    creator_name_id = fields.Integer(string='Requester Name',compute='_get_id',readonly=True)
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    co_box = fields.Boolean(string="Actionable by Coordinator",default=False)
    req_name = fields.Many2one('hr.employee',string='Requester Name')
    project_manager = fields.Boolean('Created by project manager',default=False)
    

    @api.multi
    def _get_id(self):
        for rec in self:
            rec.pr_sequence_id = rec.pr_sequence.id
            rec.creator_name_id = rec.creator_name.id

    # @api.multi
    # def create_purchase_order(self):
    #     task_ids = []
    #     purchase_req_obj = self.env['purchase.order']
    #     # purchase_req_line_obj = self.env['purchase.requisition.line']
    #     for res in self:
    #         for line in res.line_ids:  
    #             data = {
    #                         'product_id':line.product_id.id,
    #                         'name':line.name,
    #                         'product_qty':line.product_qty,
    #                         'date_planned': line.schedule_date if line.schedule_date else fields.Date.today(),
    #                         'product_uom':line.product_uom_id.id,    
    #                     }
    #             task_ids.append((0,0,data))
    #         context = {
    #                     'default_requisition_id':res.id,
    #                     'default_state':'draft',
    #                     'default_origin':res.name,
    #                     'default_order_line':task_ids,
    #                     'default_analytic_id':res.analytic_id.id,
    #                     'default_task_id':res.task_id.id,
    #                     'default_pro_requi':res.pro_requi,
    #                     'default_pr_sequence':res.pr_sequence.id,
    #                     'default_creator_name':res.creator_name.id,
    #                     }
    #         view_id = self.env.ref('purchase.purchase_order_form').id
    #         return {
    #             'name':'Purchase Order',
    #             'view_type':'form',
    #             'view_mode':'tree',
    #             'views' : [(view_id,'form')],
    #             'res_model':'purchase.order',
    #             'view_id':view_id,
    #             'type':'ir.actions.act_window',
    #             'target':'new',
    #             'context':context,
    #         }

class PurchaseorderCus2(models.Model):
    _inherit = 'purchase.order'


    pro_requi = fields.Boolean('product Requisition',default=False)
    pr_sequence = fields.Many2one('product.requisition',string='Sequence')
    creator_name = fields.Many2one('res.users',string='Requester Name')
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sel', 'Selected'),
        ('sent', 'RFQ Sent'),
        ('account', 'Accounts Approval'),
        ('req', 'Requester Approval'),
        ('top', 'Management Approval'),
        ('to approve', 'To Approval'),
        ('To approve', 'To Approval'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    test_requester = fields.Boolean('Test2',compute='_req_count',default=False)
    pr_sequence_id = fields.Integer(string='Sequence')
    creator_name_id = fields.Integer(string='Requester Name')
    co_box = fields.Boolean(string="Actionable by Coordinator",default=False)
    req_name = fields.Many2one('hr.employee',string='Requester Name')
    project_manager = fields.Boolean('Created by project manager',default=False)
    check_man = fields.Boolean('Check',compute='_req_count',default=True)
    hide_button = fields.Boolean('Hide',compute="_get_hide_button",default=False)

    @api.multi
    def _get_hide_button(self):
        for rec in self:
            if rec.project_manager == False:
                rec.hide_button = True

    @api.model
    def create(self,vals):
        res = super(PurchaseorderCus2, self).create(vals)
        if res.project_manager == False:
            res.hide_button = True

        return res

    # @api.multi
    @api.onchange('order_line')
    def _change_price(self):
        for rec in self:
            if rec.project_manager == True:
                channel_all_employees = self.env.ref('product_requisition.channel_all_pro_project_manager').read()[0]
                template_new_employee = self.env.ref('product_requisition.email_template_data_pro_project_manager').read()[0]
                # raise ValidationError(_(template_new_employee))
                if template_new_employee:
                    # MailTemplate = self.env['mail.template']
                    body_html = template_new_employee['body_html']
                    subject = template_new_employee['subject']
                    # raise ValidationError(_('%s %s ') % (body_html,subject))
                    ids = channel_all_employees['id']
                    channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                    message = """Hello, the Purchase team edit the price for this RFQ %s that the requisition created by %s"""  % (rec.name, rec.req_name.name)
                    channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')

    @api.multi
    @api.onchange('pr_sequence_id','creator_name_id')
    def _get_id(self):
        for rec in self:
            rec.pr_sequence = rec.pr_sequence_id 
            rec.creator_name = rec.creator_name_id


    @api.multi
    def _req_count(self):
        for rec in self:
            com = self.env['hr.employee'].search([('id','=',rec.req_name.id)])
            if com:
                if com.user_id.id == rec.env.uid:
                    rec.test_requester = True
                else:
                    rec.test_requester = False
            if rec.project_manager == True and rec.test_requester == True:
                rec.check_man = False
            else:
                rec.check_man = True

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.pro_requi == True:
                if self.user_has_groups('product_requisition.group_project_manager'):
                    order.write({'state': 'top'})
                    channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
                    template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
                    # raise ValidationError(_(template_new_employee))
                    if template_new_employee:
                        # MailTemplate = self.env['mail.template']
                        body_html = template_new_employee['body_html']
                        subject = template_new_employee['subject']
                        # raise ValidationError(_('%s %s ') % (body_html,subject))
                        ids = channel_all_employees['id']
                        channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                        message = """Hello, this PO number %s from product requisition No %s confirmed by project manager %s and now waiting for management approve"""  % (order.name, order.pr_sequence.sequence,self.env.user.name)
                        channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
                    com = self.env['product.requisition'].search([('id', '=', order.pr_sequence.id)])
                    com.write({'state': 'top'})
                else:
                    order.write({'state': 'account'})
                    channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
                    template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
                    # raise ValidationError(_(template_new_employee))
                    if template_new_employee:
                        # MailTemplate = self.env['mail.template']
                        body_html = template_new_employee['body_html']
                        subject = template_new_employee['subject']
                        # raise ValidationError(_('%s %s ') % (body_html,subject))
                        ids = channel_all_employees['id']
                        channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                        message = """Hello, the Purchase team assign this PO %s from product requisition no %s to accounts team
                                    To approve it and send it to the Requster approval"""  % (order.name, order.pr_sequence.sequence)
                        channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
                    com = self.env['product.requisition'].search([('id', '=', order.pr_sequence.id)])
                    com.write({'state': 'account'})
            else:  
                if order.state not in ['draft', 'sent','sel']:
                    continue
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step'\
                        or (order.company_id.po_double_validation == 'two_step'\
                            and order.amount_total < self.env.user.company_id.currency_id._convert(
                                order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                        or order.user_has_groups('marcoms_updates.group_purchase_top_manager'):
                    # order.button_approve()
                    order.write({'state': 'account'})
                    channel_all_employees = self.env.ref('product_requisition.channel_all_pro_approve').read()[0]
                    template_new_employee = self.env.ref('product_requisition.email_template_data_pro_approve').read()[0]
                    # raise ValidationError(_(template_new_employee))
                    if template_new_employee:
                        # MailTemplate = self.env['mail.template']
                        body_html = template_new_employee['body_html']
                        subject = template_new_employee['subject']
                        # raise ValidationError(_('%s %s ') % (body_html,subject))
                        ids = channel_all_employees['id']
                        channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                        message = """Hello, the Purchase team assign this PO %s to Accounts team
                                    To approve it"""  % (order.name)
                        channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')


                elif  order.amount_total < self.env.user.company_id.currency_id._convert(
                                order.company_id.po_double_validation_amount_top, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    order.write({'state': 'To approve'})
                else:
                    order.write({'state': 'to approve'})
                return True

    @api.multi
    def action_return_requester(self):
        for order in self:
            if order.pro_requi == True:
                channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
                template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
                # raise ValidationError(_(template_new_employee))
                if template_new_employee:
                    # MailTemplate = self.env['mail.template']
                    body_html = template_new_employee['body_html']
                    subject = template_new_employee['subject']
                    # raise ValidationError(_('%s %s ') % (body_html,subject))
                    ids = channel_all_employees['id']
                    channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                    message = """Hello, the accounts team send this PO %s from product requisition %s to the requester %s
                    To approve it"""  % (order.name,order.pr_sequence.sequence, order.creator_name.name)
                    channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')

                com = self.env['product.requisition'].search([('id', '=', order.pr_sequence.id)])
                com.write({'state': 'back'})
                    
                res = order.write({
                                    'state':'req',
                                })
                return res  
            else:
                order.button_approve()

    @api.multi
    def action_reject(self):
        res = self.write({
                            'state':'cancel',
                        })
        return res  

    @api.multi
    def action_requester_approve(self):
        for order in self:
            com = self.env['product.requisition'].search([('id', '=', order.pr_sequence.id)])
            com.action_requester_app()
            res = self.write({
                            'state':'top',
                        })
            return res 

    @api.multi
    def action_mana_approve(self):
        for order in self:
            com = self.env['product.requisition'].search([('id', '=', order.pr_sequence.id)])
            com.write({'state': 'app'})
            order.button_approve()
            channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
            template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
            # raise ValidationError(_(template_new_employee))
            if template_new_employee:
                # MailTemplate = self.env['mail.template']
                body_html = template_new_employee['body_html']
                subject = template_new_employee['subject']
                # raise ValidationError(_('%s %s ') % (body_html,subject))
                ids = channel_all_employees['id']
                channel_id = self.env['mail.channel'].search([('id', '=', ids)])
                message = """Hello All, %s approve the PO %s that coming from requisition %s ,now purchase team can continue the process"""  % (self.env.user.name,order.name,order.pr_sequence.sequence)
                channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')


class productRequisitionFromsales(models.Model):
    _name = "product.requisition"
    _inherit = 'mail.thread'
    _rec_name = 'sequence'


    sequence = fields.Char(string='Sequence', readonly=True,copy =False,track_visibility="onchange")
    req_name = fields.Many2one('hr.employee',string='Requester Name',default=lambda self: self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id)
    creator_name = fields.Many2one('res.users',string='Created By',readonly=True,default=lambda self: self.env.uid)
    # sales_id = fields.Many2one('sale.order',string="SO Ref",track_visibility="onchange")
    oppor_id = fields.Many2one('account.analytic.account',string="Project",track_visibility="onchange")
    partner_id = fields.Many2one('res.partner',string="Customer",track_visibility="onchange")
    task_id = fields.Many2one('project.task',string="Task",track_visibility="onchange")
    show_name = fields.Char('Show Name',track_visibility="onchange")
    requisition_date = fields.Date(string="Requisition Date",default=date.today(),track_visibility="onchange")
    requisition_dead = fields.Date(string="Requisition Deadline",track_visibility="onchange")
    state = fields.Selection([
                                ('new','New'),
                                ('po_created','Purchase Department'),
                                ('account','Accounts Department'),
                                ('back','Requester Approval'),
                                ('top','Management Approval'),
                                ('re','rejected by requester'),
                                ('rej','rejected by Management'),
                                ('app','Approved'),
                                ('cancel','Cancel')],string='State',default="new",track_visibility="onchange")
    requisition_line_ids = fields.One2many('product.requisition.line','requisition_id',string="Requisition Line ID")    
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    total_price = fields.Float(string="Total",compute="_get_total")
    flag = fields.Boolean(string="flag",default=False)
    req_number = fields.Integer(compute='_req_count', string='# Requisitions')
    po_number = fields.Integer(compute='_req_count', string='# Po')
    test_requester = fields.Boolean('Test2',compute='_req_count',default=True)
    pro_requi = fields.Boolean('product Requisition',default=True)
    co_box = fields.Boolean(string="Actionable by Coordinator",default=False)
    project_manager = fields.Boolean('Created by project manager',default=False)

    @api.constrains('requisition_date','requisition_dead')
    def check_inv_date(self):
        for rec in self:
            if rec.requisition_dead:
                if rec.requisition_date > rec.requisition_dead:
                    raise ValidationError(_("Requisition Deadline Date should be equal or bigger than requisition date"))

    @api.multi
    @api.onchange('creator_name')
    def _emp_name(self):
        for res in self:
            com = self.env['hr.employee'].search([('user_id','=',res.creator_name.id)])
            res.req_name = com.id



    @api.multi
    def _req_count(self):
        for rec in self:
            document_ids = self.env['purchase.requisition'].sudo().search([('requisition_pr_id', '=', rec.id)])
            rec.req_number = len(document_ids)
            document_idss = self.env['purchase.order'].sudo().search([('pr_sequence', '=', rec.id)])
            rec.po_number = len(document_idss)
            com = self.env['hr.employee'].search([('id','=',rec.req_name.id)])
            if com:
                if com.user_id.id == rec.env.uid:
                    rec.test_requester = True
                else:
                    rec.test_requester = False

    @api.multi
    @api.depends('requisition_line_ids')
    def _get_total(self):
        for rec in self:
            x = 0.0
            for l in rec.requisition_line_ids:
                x = x + l.total_price 
            rec.total_price = x

    # @api.constrains('requisition_line_ids')
    # def check_inv_date(self):
    #     for rec in self:
    #         if rec.requisition_line_ids:
    #             if rec.state == 'po_created':
    #                 for l in rec.requisition_line_ids:
    #                     if l.price:
    #                         continue
    #                     else:
    #                         raise ValidationError(_("add a price for product %s")% (l.product_id.name))
    #         else:
    #             raise ValidationError(_("Add some products"))
            

    @api.model
    def create(self , vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('product.requisition') or '/'
        # com = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        # vals['req_name'] = com.id
        return super(productRequisitionFromsales, self).create(vals)

    @api.multi
    def action_cancel(self):
        res = self.write({
                            'state':'cancel',
                        })
        return res 

    @api.multi
    def set_to_draft(self):
        res = self.write({
                            'state':'new',
                        })
        return res   

    @api.multi
    def action_return_requester(self):
        channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
        template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            message = """Hello, the accounts team send this requisition %s to the requester %s
            To approve it"""  % (self.sequence, self.creator_name.name)
            channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
            
        res = self.write({
                            'state':'back',
                        })
        return res  

    @api.multi
    def action_requester_app(self):
        channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
        template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            channel_id.message_post(body='Hello, the Requester approve this requisition and send it to the management approval '+str(self.sequence), subject=subject,subtype='mail.mt_comment')
            
        res = self.write({
                            'state':'top',
                        })
        return res  

    @api.multi
    def action_requester_rej(self):
        res = self.write({
                            'state':'re',
                        })
        return res  

    @api.multi
    def action_management_app(self):
        res = self.write({
                            'state':'app',
                        })
        return res  

    @api.multi
    def action_management_rej(self):
        res = self.write({
                            'state':'rej',
                        })
        return res  

    @api.multi
    def action_to_po(self):
        channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
        template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            if self.user_has_groups('product_requisition.group_project_manager'):
                message = """Hello, there is New Product requisition assigned to purchase team that was created by a project manager(%s) with number %s"""  % (self.req_name.name,self.sequence)
            else:
                message = """Hello, there is New Product requisition assigned to purchase team with number %s"""  % (self.sequence)
            channel_id.message_post(body=message, subject=subject,subtype='mail.mt_comment')
            
        self.create_purchase_requisition()
        res = self.write({
                            'state':'po_created',
                        })
        return res  

    @api.multi
    def action_pricing(self):
        # if self.state == 'po_created':
        #     for l in self.requisition_line_ids:
        #         if l.price:
        #             continue
        #         else:
        #             raise ValidationError(_("add a price for product %s")% (l.product_id.name))
        channel_all_employees = self.env.ref('product_requisition.channel_all_pro_requisi').read()[0]
        template_new_employee = self.env.ref('product_requisition.email_template_data_pro_requisi').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            channel_id.message_post(body='Hello, the Purchase team send to accounts this requisition with number '+str(self.sequence), subject=subject,subtype='mail.mt_comment')
            
        res = self.write({
                            'state':'account',
                        })
        return res  

    @api.multi
    def create_purchase_requisition(self):
        task_ids = []
        purchase_req_obj = self.env['purchase.requisition']
        # purchase_req_line_obj = self.env['purchase.requisition.line']
        for res in self:
            if self.user_has_groups('product_requisition.group_project_manager'):
                for line in res.requisition_line_ids:  
                    data = {
                                'product_id':line.product_id.id,
                                'name':line.description,
                                'account_analytic_id':res.oppor_id.id,
                                'product_qty':line.qty,
                                'product_uom_id':line.uom_id.id,    
                            }
                    task_ids.append((0,0,data))
                purchase_req_obj.create({
                                                'requisition_pr_id':res.id,
                                                'state':'draft',
                                                'origin':res.sequence,
                                                'line_ids':task_ids,
                                                'analytic_id':res.oppor_id.id,
                                                'task_id':res.task_id.id,
                                                'pro_requi':res.pro_requi,
                                                'pr_sequence':res.id,
                                                'creator_name':res.creator_name.id,
                                                'reason_for_requisition':res.reason_for_requisition,
                                                'co_box':res.co_box,
                                                'req_name':res.req_name.id,
                                                'user_id':False,
                                                'project_manager':True,
                                                })
            else:
                for line in res.requisition_line_ids:  
                    data = {
                                'product_id':line.product_id.id,
                                'name':line.description,
                                'account_analytic_id':res.oppor_id.id,
                                'product_qty':line.qty,
                                'product_uom_id':line.uom_id.id,    
                            }
                    task_ids.append((0,0,data))
                purchase_req_obj.create({
                                                'requisition_pr_id':res.id,
                                                'state':'draft',
                                                'origin':res.sequence,
                                                'line_ids':task_ids,
                                                'analytic_id':res.oppor_id.id,
                                                'task_id':res.task_id.id,
                                                'pro_requi':res.pro_requi,
                                                'pr_sequence':res.id,
                                                'creator_name':res.creator_name.id,
                                                'reason_for_requisition':res.reason_for_requisition,
                                                'co_box':res.co_box,
                                                'req_name':res.req_name.id,
                                                'user_id':False,
                                                'project_manager':False,
                                                })
        # for line in self.requisition_line_ids:  
        #     req_line_vals = purchase_req_line_obj.create({
        #         'product_id':line.product_id.id,
        #         'product_qty':line.qty,
        #         'product_uom_id':line.uom_id.id,
        #         'requisition_id':req_vals.id,
        #         })
        self.write({
                            'flag':True,
                        })

    @api.multi
    def req_view(self):
        self.ensure_one()
        task_ids = []
        for res in self:
            if self.user_has_groups('product_requisition.group_project_manager'):
                for line in res.requisition_line_ids:  
                    data = {
                                'product_id':line.product_id.id,
                                'product_qty':line.qty,
                                'name':line.description,
                                'account_analytic_id':res.oppor_id.id,
                                'product_uom_id':line.uom_id.id,    
                            }
                    task_ids.append((0,0,data))
                datas = {
                                                'default_requisition_pr_id':res.id,
                                                'default_user_id':False,
                                                'default_state':'draft',
                                                'default_origin':res.sequence,
                                                'task_id':res.task_id.id,
                                                'default_line_ids':task_ids,
                                                'default_analytic_id':res.oppor_id.id,
                                                'default_pro_requi':res.pro_requi,
                                                'default_pr_sequence':res.id,
                                                'default_creator_name':res.creator_name.id,
                                                'default_reason_for_requisition':res.reason_for_requisition,
                                                'default_co_box':res.co_box,
                                                'default_req_name':res.req_name.id,
                                                'default_project_manager':True,
                                                }
                domain = [
                    ('requisition_pr_id', '=', res.id)]
            else:
                for line in res.requisition_line_ids:  
                    data = {
                                'product_id':line.product_id.id,
                                'product_qty':line.qty,
                                'name':line.description,
                                'account_analytic_id':res.oppor_id.id,
                                'product_uom_id':line.uom_id.id,    
                            }
                    task_ids.append((0,0,data))
                datas = {
                                                'default_requisition_pr_id':res.id,
                                                'default_user_id':False,
                                                'default_state':'draft',
                                                'default_origin':res.sequence,
                                                'task_id':res.task_id.id,
                                                'default_line_ids':task_ids,
                                                'default_analytic_id':res.oppor_id.id,
                                                'default_pro_requi':res.pro_requi,
                                                'default_pr_sequence':res.id,
                                                'default_creator_name':res.creator_name.id,
                                                'default_reason_for_requisition':res.reason_for_requisition,
                                                'default_co_box':res.co_box,
                                                'default_req_name':res.req_name.id,
                                                'default_project_manager':False,
                                                }
                domain = [
                    ('requisition_pr_id', '=', res.id)]
        view_tree_id = self.env.ref('product_requisition.purchase_requisition_tree_cus2').id
        view_form_id = self.env.ref('purchase_requisition.view_purchase_requisition_form').id
        return {
            'name': _('Purchase Tender'),
            'domain': domain,
            'res_model': 'purchase.requisition',
            'type': 'ir.actions.act_window',
            # 'view_id': False,
            'view_mode': 'tree,form',
            'views' : [(view_tree_id, 'tree'),
					  (view_form_id, 'form')],
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           there is no Purchase tender for this requisition
                        </p>'''),
            'limit': 80,
            'context': datas
        }

    @api.multi
    def po_view(self):
        self.ensure_one()
        for res in self:
            domain = [
                ('pr_sequence', '=', res.id)]
        return {
            'name': _('Purchase Orders'),
            'domain': domain,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           there is no Purchase order for this requisition
                        </p>'''),
            'limit': 80,
        }
class PurchaseRequisitionLinecus(models.Model):
    _inherit = "purchase.requisition.line"

    name = fields.Text(string="Description")

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        requisition = self.requisition_id
        if requisition.schedule_date:
            date_planned = datetime.combine(requisition.schedule_date, time.min)
        else:
            date_planned = datetime.now()
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': date_planned,
            'account_analytic_id': self.account_analytic_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or []
        }

class productRequisitionLine(models.Model):
    _name = "product.requisition.line"
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
    requisition_id = fields.Many2one('product.requisition',string="Requisition Line")
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