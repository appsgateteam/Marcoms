# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math
from odoo.exceptions import Warning

class MaterialRequisition(models.Model):
	_name = "material.requisition"
	_inherit = 'mail.thread'
	_rec_name = 'sequence'

	@api.model
	def create(self , vals):
		vals['sequence'] = self.env['ir.sequence'].next_by_code('material.requisition') or '/'
		return super(MaterialRequisition, self).create(vals)

	# @api.onchange('employee_id')
	# def get_emp_dest_location(self):
	#     if self.employee_id:
	#         self.destination_location_id = self.employee_id.destination_location_id.id

	@api.model 
	def default_get(self, flds): 
		result = super(MaterialRequisition, self).default_get(flds)
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
											  'N2N_project_enhancement',
											  'email_employee_purchase_requisition_new')[1]
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
	def product_available(self):
		for line in self.requisition_line_ids:
			avail_qty = line.product_id.with_context({'location' : self.source_location_id.id}).qty_available
			line.write({'available_qty':avail_qty})    
   
	@api.multi
	def department_approve(self):
		res = self.write({
							'state':'ir_approve',
							'department_manager_id':self.env.user.id,
							'department_approval_date' : datetime.now()
						})
		template_id = self.env['ir.model.data'].get_object_reference(
											  'N2N_project_enhancement',
											  'email_manager_purchase_requisition_new')[1]
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
		for picking in self.env['stock.picking'].search([('origin','=',self.sequence),('backorder_id','=',False)]):
			if picking.state == 'done':
				self.write({
								'state':'received',
								'received_date' : datetime.now()
							})
			else:
				raise Warning(_('You cant received the product,because picking is not completed'))

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
											  'N2N_project_enhancement',
											  'email_user_purchase_requisition_new')[1]
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

	@api.multi
	def _get_internal_picking_count(self):
		for picking in self:
			picking_ids = self.env['stock.picking'].search([('requisition_mat_picking_id','=',picking.id)])
			picking.internal_picking_count = len(picking_ids)
	
	@api.multi
	def create_picking(self):
		for line in self.requisition_line_ids.filtered(lambda r: r.available_qty < r.qty):
			raise Warning(_('Please create purchase tender,because available qty is less than that of actual qty'))
		else:
			self.sudo().create_picking_new()

	@api.multi
	def create_picking_new(self):
		stock_picking_obj = self.env['stock.picking']
		stock_move_obj = self.env['stock.move']
		stock_picking_type_obj = self.env['stock.picking.type']
		picking_type_ids = stock_picking_type_obj.search([('code','=','outgoing')])
		if not picking_type_ids:
			raise Warning(_('Please define Internal Picking.'))
		for res in self:            
			val = {
					'origin': res.sequence,
					'picking_type_id' : picking_type_ids[0].id,
					'company_id': self.env.user.company_id.id,
					'location_id' : res.source_location_id.id,
					'location_dest_id' : res.destination_location_id.id,
					'requisition_mat_picking_id' : res.id,
					'analytic_id': res.analytic_id.id,
					'task_id': res.task_id.id
			}
			stock_picking = stock_picking_obj.create(val)
		for line in self.requisition_line_ids:
			pic_line_val = {
							'name': line.product_id.name,
							'product_id' : line.product_id.id,
							'product_uom_qty' : line.qty,
							'product_uom' : line.uom_id.id,
							'location_id' : res.source_location_id.id,
							# 'location_id': self.source_location_id.id,
							'location_dest_id' : res.destination_location_id.id,
							'picking_id' : stock_picking.id

			}
			stock_move = stock_move_obj.create(pic_line_val)
		res = self.write({
							'state':'io_created',
						})
		return res 
		
	
	@api.multi
	def internal_picking_button(self):
		self.ensure_one()
		return {
			'name': 'Internal Picking',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'stock.picking',
			'domain': [('requisition_mat_picking_id', '=', self.id)],
		}

	@api.multi
	def _get_purchase_order_count(self):
		for po in self:
			po_ids = self.env['purchase.requisition'].search([('requisition_mat_po_id','=',po.id)])
			po.purchase_order_count = len(po_ids)
			
	@api.multi
	def purchase_order_button(self):
		self.ensure_one()
		return {
			'name': 'Purchase Tender',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'purchase.requisition',
			'domain': [('requisition_mat_po_id', '=', self.id)],
		}

	@api.multi
	def _get_emp_destination(self):
		if not self.employee_id.destination_location_id:
			return 
		self.destination_location_id = self.employee_id.destination_location_id

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
		types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)])
		if not types:
			types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
		return types[:1]

	@api.multi
	def create_purchase_requisition(self):
		task_id = []
		purchase_req_obj = self.env['purchase.requisition']
		purchase_req_line_obj = self.env['purchase.requisition.line']
		for res in self:
			req_vals = purchase_req_obj.create({
											'analytic_id': res.analytic_id.id,
											'task_id': res.task_id.id,
											'requisition_mat_po_id':res.id,
											'origin':res.sequence,
											})
		#raise Warning(_('You cant received the product,because picking is not completed'))
		for line in self.requisition_line_ids.filtered(lambda r: r.available_qty < r.qty):
			req_line_vals = purchase_req_line_obj.create({
				'product_id':line.product_id.id,
				'name':line.description, 
				'account_analytic_id':res.analytic_id.id,
				'product_qty':line.qty,
				'product_uom_id':line.uom_id.id,
				'requisition_id':req_vals.id,

				})
		self.sudo().create_picking_new()
		res = self.write({
							'state':'po_created',
						})
		return res 

	def _default_destination_location(self):
		location_dest_id = self.env['stock.location'].search([('usage','=','production')],limit=1)
		return location_dest_id

	def _default_source_location(self):
		location_id = self.env['stock.location'].search([('usage','=','internal')],limit=1)
		return location_id

	sequence = fields.Char(string='Sequence', readonly=True,copy =False)
	employee_id = fields.Many2one('hr.employee',string="Employee",required=True, track_visibility='always')
	requisition_responsible_id  = fields.Many2one('res.users',string="Requisition Responsible")
	requisition_date = fields.Date(string="Requisition Date",required=True,track_visibility='always')
	received_date = fields.Date(string="Received Date",readonly=True)
	requisition_deadline_date = fields.Date(string="Requisition Deadline")
	state = fields.Selection([
								('new','New'),
								('department_approval','Waiting Department Approval'),
								('ir_approve','Waiting IR Approved'),
								# ('approved','Approved'),
								('po_created','Tender Created'),
								('io_created','Picking Created'),
								('received','Received'),
								('cancel','Cancel')],string='Stage',default="new")
	requisition_line_ids = fields.One2many('material.requisition.line','requisition_id',string="Requisition Line ID")    
	confirmed_by_id = fields.Many2one('res.users',string="Confirmed By")
	department_manager_id = fields.Many2one('res.users',string="Department Manager")
	approved_by_id = fields.Many2one('res.users',string="Approved By")
	rejected_by = fields.Many2one('res.users',string="Rejected By")
	confirmed_date = fields.Date(string="Confirmed Date",readonly=True)
	department_approval_date = fields.Date(string="Department Approval Date",readonly=True)
	approved_date = fields.Date(string="Approved Date",readonly=True)
	rejected_date = fields.Date(string="Rejected Date",readonly=True)
	reason_for_requisition = fields.Text(string="Reason For Requisition")
	source_location_id = fields.Many2one('stock.location',string="Source Location", default=_default_source_location)
	destination_location_id = fields.Many2one('stock.location',string="Destination Location", default=_default_destination_location)
	internal_picking_id = fields.Many2one('stock.picking.type',string="Delivery Order", default=_default_picking_internal_type)
	internal_picking_count = fields.Integer('Internal Picking', compute='_get_internal_picking_count')
	purchase_order_count = fields.Integer('Purchase Tender', compute='_get_purchase_order_count')
	company_id = fields.Many2one('res.company',string="Company")
	picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True, default=_default_picking_type)
	analytic_id =fields.Many2one('account.analytic.account',string="Project", required=True,track_visibility='always')
	task_id = fields.Many2one('project.task', string="Task", required=True,track_visibility='always')
	# picking_id = fields.One2many('stock.picking', 'requisition_picking_id')



class RequisitionLine(models.Model):
	_name = "material.requisition.line"
	_rec_name = 'requisition_id'

	@api.multi
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.uom_id = self.product_id.uom_id.id
		self.description = self.product_id.name


	product_id = fields.Many2one('product.product',string="Product")
	description = fields.Text(string="Description")
	qty = fields.Float(string="Quantity",default=1.0)
	uom_id = fields.Many2one('uom.uom',string="Unit Of Measure")
	requisition_id = fields.Many2one('material.requisition',string="Requisition Line")
	available_qty = fields.Float(string="Available Qty")

class StockPicking(models.Model):      
	_inherit = 'stock.picking'

	@api.multi
	def action_confirm(self):
		pick = super(StockPicking, self).action_confirm()
		for line in self.move_lines:
			avail_qty = line.product_id.with_context({'location' : self.location_id.id}).qty_available
			line.write({'available_qty':avail_qty})
		return pick 

	requisition_mat_picking_id = fields.Many2one('material.requisition',string="Purchase Requisition", ondelete="cascade")
	analytic_id =fields.Many2one('account.analytic.account',string="Project")
	task_id = fields.Many2one('project.task', string="Task")

class PurchaseRequisition(models.Model):      
	_inherit = 'purchase.requisition'    

	requisition_mat_po_id = fields.Many2one('material.requisition',string="Purchase Requisition")
	analytic_id =fields.Many2one('account.analytic.account',string="Project")
	task_id = fields.Many2one('project.task', string="Task")

class PurchaseOrder(models.Model):      
	_inherit = 'purchase.order'   

	analytic_id =fields.Many2one('account.analytic.account',string="Project")
	task_id = fields.Many2one('project.task', string="Task") 
	requisition_mat_po_id = fields.Many2one('material.requisition',string="Purchase Requisition")
	
class StockMove(models.Model):
	_inherit = "stock.move"

	def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id):
		res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id)
		if self.picking_id.analytic_id:
			res['credit_line_vals']['analytic_account_id'] = self.picking_id.analytic_id.id
		return res 

	available_qty = fields.Float(string="Available Qty")