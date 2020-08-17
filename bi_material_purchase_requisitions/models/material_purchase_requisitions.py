# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math
from odoo.exceptions import Warning

class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _rec_name = 'sequence'
    _order = 'sequence desc'
    _description = "Material Purchase Requisition"

    @api.model
    def create(self , vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('material.purchase.requisition') or '/'
        return super(MaterialPurchaseRequisition, self).create(vals)

    @api.onchange('employee_id')
    def get_emp_dest_location(self):
        if self.employee_id:
            self.destination_location_id = self.employee_id.destination_location_id.id

    @api.model 
    def default_get(self, flds): 
        result = super(MaterialPurchaseRequisition, self).default_get(flds)
        #result['employee_id'] = self.env.user.partner_id.id
        result['requisition_date'] = datetime.now()
        return result        

    @api.multi
    def confirm_requisition(self):
        res = self.write({
                            'state':'department_approval',
                            'confirmed_by_id':self.env.user.id,
                            'confirmed_date' : datetime.now()
                        })
        template_id = self.env['ir.model.data'].get_object_reference(
                                              'bi_material_purchase_requisitions',
                                              'email_employee_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.employee_id.work_email
            values['email_to'] = self.requisition_responsible_id.email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])           
        return res

    @api.multi
    def department_approve(self):
        res = self.write({
                            'state':'ir_approve',
                            'department_manager_id':self.env.user.id,
                            'department_approval_date' : datetime.now()
                        })
        template_id = self.env['ir.model.data'].get_object_reference(
                                              'bi_material_purchase_requisitions',
                                              'email_manager_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.env.user.partner_id.email
            values['email_to'] = self.employee_id.work_email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])        
        return res  

    @api.multi
    def action_cancel(self):
        for res in self:
            stock_req = self.env['stock.picking'].search([('origin','=',res.sequence)])
            if stock_req:
                for stock in stock_req:
                    stock.action_cancel()
                    stock.unlink()
            purchase_req = self.env['purchase.order'].search([('origin', '=', res.sequence)])
            if purchase_req:
                for purchase in purchase_req:
                    purchase.button_cancel()
                    purchase.unlink()
        res = self.write({
                            'state':'cancel',
                        })
        return res          

    @api.multi
    def action_received(self):
        res = self.write({
                            'state':'received',
                            'received_date' : datetime.now()
                        })
        return res         

    @api.multi
    def action_reject(self):
        for res in self:
            stock_req = self.env['stock.picking'].search([('origin','=',res.sequence)])
            if stock_req:
                for stock in stock_req:
                    stock.action_cancel()
                    stock.unlink()
            purchase_req = self.env['purchase.order'].search([('origin', '=', res.sequence)])
            if purchase_req:
                for purchase in purchase_req:
                    purchase.button_cancel()
                    purchase.unlink()
        res = self.write({
                            'state':'cancel',
                            'rejected_date' : datetime.now(),
                            'rejected_by' : self.env.user.id
                        })
        return res 

    @api.multi
    def action_reset_draft(self):
        for res in self:
            stock_req = self.env['stock.picking'].search([('origin','=',res.sequence)])
            if stock_req:
                for stock in stock_req:
                    stock.action_cancel()
                    stock.unlink()
            purchase_req = self.env['purchase.order'].search([('origin', '=', res.sequence)])
            if purchase_req:
                for purchase in purchase_req:
                    purchase.button_cancel()
                    purchase.unlink()
            res.write({
                            'state':'new',
                        })
        return res 


    @api.multi
    def action_approve(self):
        res = self.write({
                            'state':'approved',
                            'approved_by_id':self.env.user.id,
                            'approved_date' : datetime.now()
                        })
        template_id = self.env['ir.model.data'].get_object_reference(
                                              'bi_material_purchase_requisitions',
                                              'email_user_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.employee_id.work_email
            values['email_to'] = self.employee_id.work_email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])         
        return res 

    def create_picking_po(self):
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        for requisition in self:
            for line in requisition.requisition_line_ids:
                if line.requisition_action == 'purchase_order':
                    for vendor in line.vendor_id:
                        pur_order = purchase_order_obj.search([('requisition_po_id','=',requisition.id),('partner_id','=',vendor.id)])
                        if pur_order:
                            po_line_vals = {
                                'product_id' : line.product_id.id,
                                'product_qty': line.qty,
                                'name' : line.description,
                                'price_unit' : line.product_id.list_price,
                                'date_planned' : datetime.now(),
                                'product_uom' : line.uom_id.id,
                                'order_id' : pur_order.id,
                            }
                            purchase_order_line = purchase_order_line_obj.create(po_line_vals)
                        else:
                            vals = {
                                'partner_id' : vendor.id,
                                'date_order' : datetime.now(),
                                'requisition_po_id' : requisition.id,
                                'origin': requisition.sequence,
                                'job_id':requisition.job_order_id.id,
                                'state' : 'draft',
                                'picking_type_id' : requisition.picking_type_id.id                                
                            }
                            purchase_order = purchase_order_obj.create(vals)
                            po_line_vals = {
                                'product_id' : line.product_id.id,
                                'product_qty': line.qty,
                                'name' : line.description,
                                'price_unit' : line.product_id.list_price,
                                'date_planned' : datetime.now(),
                                'product_uom' : line.uom_id.id,
                                'order_id' : purchase_order.id,
                            }
                            purchase_order_line = purchase_order_line_obj.create(po_line_vals)
                else:
                    stock_picking_obj = self.env['stock.picking']
                    stock_move_obj = self.env['stock.move']
                    stock_picking_type_obj = self.env['stock.picking.type']
                    picking_type_id = False

#                    if requisition.picking_type_id.id:
#                        raise Warning(_('Please define Internal Picking.'))
                    if not requisition.use_manual_locations:
                        picking_type_id = requisition.internal_picking_id
                    else:
                        picking_type_id = stock.stock_picking_type_obj.search([('code','=','internal')], order="id desc", limit=1)

                    if line.vendor_id:                    
                        for vendor in line.vendor_id:
                        
                            #employee_id = self.env['hr.employee'].search('id','=',self.env.user.name)
                            pur_order = stock_picking_obj.search([('requisition_picking_id','=',requisition.id),('partner_id','=',vendor.id)])
                            
                            if pur_order:
                                if requisition.use_manual_locations:
                                    pic_line_val = {
                                        'name': line.product_id.name,
                                        'product_id' : line.product_id.id,
                                        'product_uom_qty' : line.qty,
                                        'picking_id' : picking_type_id.id,
                                        'product_uom' : line.uom_id.id,
                                        'location_id': requisition.source_location_id.id,
                                        'location_dest_id' : requisition.destination_location_id.id,
                                    }
                                else:
                                    pic_line_val = {
                                        'name': line.product_id.name,
                                        'product_id' : line.product_id.id,
                                        'product_uom_qty' : line.qty,
                                        'picking_id' : picking_type_id.id,
                                        'product_uom' : line.uom_id.id,
                                        'location_id': picking_type_id.default_location_src_id.id,
                                        'location_dest_id' : picking_type_id.default_location_dest_id.id,
                                    }                                    


                                stock_move = stock_move_obj.create(pic_line_val)
                            else:
                                if requisition.use_manual_locations:
                                    val = {
                                        'partner_id' : vendor.id,
                                        'location_id'  : requisition.source_location_id.id,
                                        'location_dest_id' : requisition.destination_location_id.id,
                                        'picking_type_id' : picking_type_id.id,
                                        'material_requisition_id':requisition.job_order_id.id,
                                        'construction_project_id' : requisition.construction_project_id.id,
                                        'analytic_account_id' : requisition.analytic_id.id,                                        
                                        'company_id': requisition.env.user.company_id.id,
                                        'requisition_picking_id' : requisition.id,
                                        'origin':requisition.sequence
                                    }
                                else:
                                    val = {
                                        'partner_id' : vendor.id,
                                        'location_id'  : picking_type_id.default_location_src_id.id,
                                        'location_dest_id' :picking_type_id.default_location_src_id.id,
                                        'picking_type_id' : picking_type_id.id,
                                        'material_requisition_id':requisition.job_order_id.id,
                                        'construction_project_id' : requisition.construction_project_id.id,
                                        'analytic_account_id' : requisition.analytic_id.id,                                        
                                        'company_id': requisition.env.user.company_id.id,
                                        'requisition_picking_id' : requisition.id,
                                        'origin':requisition.sequence
                                    }                                    

                                stock_picking = stock_picking_obj.create(val)
                                if requisition.use_manual_locations:
                                    pic_line_val = {
                                                    'partner_id' : vendor.id,
                                                    'name': line.product_id.name,
                                                    'product_id' : line.product_id.id,
                                                    'product_uom_qty' : line.qty,
                                                    'product_uom' : line.uom_id.id,
                                                    'location_id': requisition.source_location_id.id,
                                                    'location_dest_id' : requisition.destination_location_id.id,
                                                    'picking_id' : stock_picking.id,
                                                    'origin': requisition.sequence

                                    }
                                else:
                                    pic_line_val = {
                                                    'partner_id' : vendor.id,
                                                    'name': line.product_id.name,
                                                    'product_id' : line.product_id.id,
                                                    'product_uom_qty' : line.qty,
                                                    'product_uom' : line.uom_id.id,
                                                    'location_id': picking_type_id.default_location_src_id.id,
                                                    'location_dest_id' : picking_type_id.default_location_dest_id.id,
                                                    'picking_id' : stock_picking.id,
                                                    'origin': requisition.sequence

                                    }                                    
                                stock_move = stock_move_obj.create(pic_line_val)
                    else:
                        pur_order = stock_picking_obj.search([('requisition_picking_id','=',requisition.id)])                     

                        if pur_order:
                            if requisition.use_manual_locations:
                                pic_line_val = {
                                    'name': line.product_id.name,
                                    'product_id' : line.product_id.id,
                                    'product_uom_qty' : line.qty,
                                    'picking_id' : stock_picking.id,
                                    'product_uom' : line.uom_id.id,
                                    'location_id': requisition.source_location_id.id,
                                    'location_dest_id' : requisition.destination_location_id.id,
                                }
                            else:
                                pic_line_val = {
                                    'name': line.product_id.name,
                                    'product_id' : line.product_id.id,
                                    'product_uom_qty' : line.qty,
                                    'picking_id' : stock_picking.id,
                                    'product_uom' : line.uom_id.id,
                                    'location_id': picking_type_id.default_location_src_id.id,
                                    'location_dest_id' : picking_type_id.default_location_dest_id.id,
                                }                                

                            stock_move = stock_move_obj.create(pic_line_val)
                        else:
                            if requisition.use_manual_locations:
                                val = {
                                    'location_id'  : requisition.source_location_id.id,
                                    'location_dest_id' : requisition.destination_location_id.id,
                                    'picking_type_id' : picking_type_id.id,
                                    'material_requisition_id':requisition.job_order_id.id,
                                    'construction_project_id' : requisition.construction_project_id.id,
                                    'analytic_account_id' : requisition.analytic_id.id,                                    
                                    'company_id': requisition.env.user.company_id.id,
                                    'requisition_picking_id' : requisition.id,
                                    'origin':requisition.sequence
                                }
                            else:
                                val = {
                                    'location_id'  : picking_type_id.default_location_src_id.id,
                                    'location_dest_id' : picking_type_id.default_location_dest_id.id,
                                    'picking_type_id' : picking_type_id.id,
                                    'material_requisition_id':requisition.job_order_id.id,
                                    'construction_project_id' : requisition.construction_project_id.id,
                                    'analytic_account_id' : requisition.analytic_id.id,
                                    'company_id': requisition.env.user.company_id.id,
                                    'requisition_picking_id' : requisition.id,
                                    'origin':requisition.sequence
                                }                                


                            stock_picking = stock_picking_obj.create(val)
                            if requisition.use_manual_locations:
                                pic_line_val = {
                                                'name': line.product_id.name,
                                                'product_id' : line.product_id.id,
                                                'product_uom_qty' : line.qty,
                                                'product_uom' : line.uom_id.id,
                                                'location_id': requisition.source_location_id.id,
                                                'location_dest_id' : requisition.destination_location_id.id,
                                                'picking_id' : stock_picking.id,
                                                'origin': requisition.sequence

                                }
                            else:
                                pic_line_val = {
                                                'name': line.product_id.name,
                                                'product_id' : line.product_id.id,
                                                'product_uom_qty' : line.qty,
                                                'product_uom' : line.uom_id.id,
                                                'location_id': picking_type_id.default_location_src_id.id,
                                                'location_dest_id' : picking_type_id.default_location_dest_id.id,
                                                'picking_id' : stock_picking.id,
                                                'origin': requisition.sequence

                                }
                            stock_move = stock_move_obj.create(pic_line_val)
            requisition.write({
                'state':'po_created',
            }) 



    @api.multi
    def _get_internal_picking_count(self):
        for picking in self:
            picking_ids = self.env['stock.picking'].search([('requisition_picking_id','=',picking.id)])
            picking.internal_picking_count = len(picking_ids)
            
    @api.multi
    def internal_picking_button(self):
        self.ensure_one()
        return {
            'name': 'Internal Picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_picking_id', '=', self.id)],
        }

    @api.multi
    def _get_purchase_order_count(self):
        for po in self:
            po_ids = self.env['purchase.order'].search([('requisition_po_id','=',po.id)])
            po.purchase_order_count = len(po_ids)
            
    @api.multi
    def purchase_order_button(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_po_id', '=', self.id)],
        }

    # @api.multi
    # def _get_emp_destination(self):
    #     if not self.employee_id.destination_location_id:
    #         return 
    #     self.destination_location_id = self.employee_id.destination_location_id

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]


    @api.model
    def _default_picking_internal_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    sequence = fields.Char(string='Sequence', readonly=True,copy =False)
    employee_id = fields.Many2one('hr.employee',string="Employee",required=True)
    department_id = fields.Many2one('hr.department',string="Department",required=True)
    requisition_responsible_id  = fields.Many2one('res.users',string="Requisition Responsible")
    requisition_date = fields.Date(string="Requisition Date",required=True)
    received_date = fields.Date(string="Received Date",readonly=True)
    requisition_deadline_date = fields.Date(string="Requisition Deadline")
    state = fields.Selection([
                                ('new','New'),
                                ('department_approval','Waiting Department Approval'),
                                ('ir_approve','Waiting User Approved'),
                                ('approved','Approved'),
                                ('po_created','Purchase Order Created'),
                                ('received','Received'),
                                ('cancel','Cancel')],string='Stage',default="new")
    requisition_line_ids = fields.One2many('requisition.line','requisition_id',string="Requisition Line ID")    
    confirmed_by_id = fields.Many2one('res.users',string="Confirmed By", copy=False)
    department_manager_id = fields.Many2one('res.users',string="Department Manager", copy=False)
    approved_by_id = fields.Many2one('res.users',string="Approved By", copy=False)
    rejected_by = fields.Many2one('res.users',string="Rejected By", copy=False)
    confirmed_date = fields.Date(string="Confirmed Date",readonly=True , copy=False)
    department_approval_date = fields.Date(string="Department Approval Date",readonly=True, copy=False)
    approved_date = fields.Date(string="Approved Date",readonly=True, copy=False)
    rejected_date = fields.Date(string="Rejected Date",readonly=True , copy=False)
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    source_location_id = fields.Many2one('stock.location',string="Source Location")
    destination_location_id = fields.Many2one('stock.location',string="Destination Location")
    internal_picking_id = fields.Many2one('stock.picking.type',string="Internal Picking", default=_default_picking_internal_type)
    internal_picking_count = fields.Integer('Internal Picking', compute='_get_internal_picking_count')
    purchase_order_count = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
    company_id = fields.Many2one('res.company',string="Company" , default=lambda self: self.env.user.company_id)
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True, default=_default_picking_type)
    use_manual_locations = fields.Boolean(string="Select Manual Locations")
    




class RequisitionLine(models.Model):
    _name = "requisition.line"
    _rec_name = 'requisition_id'
    _description = "Requisition Line"

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name


    product_id = fields.Many2one('product.template',string="Product",domain="[('type','not in',['service'])]")
    description = fields.Text(string="Description")
    qty = fields.Float(string="Quantity",default=1.0)
    uom_id = fields.Many2one('uom.uom',string="Unit Of Measure")
    requisition_id = fields.Many2one('material.purchase.requisition',string="Requisition Line")
    requisition_action = fields.Selection([('purchase_order','Purchase Order'),('internal_picking','Internal Picking')],string="Requisition Action" , default = "purchase_order")
    vendor_id = fields.Many2many('res.partner',string="Vendors")

class StockPicking(models.Model):      
    _inherit = 'stock.picking'

    requisition_picking_id = fields.Many2one('material.purchase.requisition',string="Purchase Requisition")

class PurchaseOrder(models.Model):      
    _inherit = 'purchase.order'    

    requisition_po_id = fields.Many2one('material.purchase.requisition',string="Purchase Requisition")

class HrEmployee(models.Model):      
    _inherit = 'hr.employee'    

    destination_location_id = fields.Many2one('stock.location',string="Destination Location")    

class HrDepartment(models.Model):      
    _inherit = 'hr.department'    

    destination_location_id = fields.Many2one('stock.location',string="Destination Location")    


    
