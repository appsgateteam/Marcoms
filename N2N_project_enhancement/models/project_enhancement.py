# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import html2plaintext
from odoo.exceptions import Warning


class ProjectTask(models.Model):
	_inherit = "project.task"

	material_estimation_ids = fields.One2many('material.estimate','material_id','Material Estimation', readonly=True, states={'draft': [('readonly', False)]})
	labour_estimation_ids = fields.One2many('labour.estimate','labour_id','Labour Estimation',  readonly=True, states={'draft': [('readonly', False)]})
	overhead_estimation_ids = fields.One2many('overhead.estimate','overhead_id','Overhead Estimation',  readonly=True, states={'draft': [('readonly', False)]})
	total_material_estimate = fields.Float(compute='_calculate_total',string='Total Material Estimate',default=0.0,readonly=True,store=True)
	total_labour_estimate = fields.Float(compute='_calculate_total',string='Total Labour Estimate',default=0.0,readonly=True,store=True)
	total_overhead_estimate = fields.Float(compute='_calculate_total',string='Total Overhead Estimate',default=0.0,readonly=True,store=True)
	total_job_estimate = fields.Float(compute='_calculate_total',string='Total Job Estimate',default=0.0,readonly=True,store=True)
	state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancel')],'Status',default="draft")
	material_job_cost_line_ids = fields.One2many('materal.cost.line','material_job_cost_sheet_id','Material Job Cost Line')
	overhead_job_cost_line_ids = fields.One2many('overhead.cost.line','overhead_job_cost_sheet_id','Overhead Job Cost Line')
	overhead_line_ids = fields.One2many('account.analytic.line','task_id','Overhead Job Cost Line', domain=[('nn_overhead_id','!=',False)])
	total_material_cost = fields.Float(compute='_compute_total_material_cost',string="Total Material Cost",default=0.0)
	# total_labour_cost = fields.Float(compute='_compute_total_labour_cost',string='Total Labour Cost',default=0.0)
	total_overhead_cost = fields.Float(compute='_compute_total_overhead_cost',string='Total Overhead Cost',default=0.0)
	total_cost = fields.Float(compute='_compute_total_cost',string='Total Cost',default=0.0)
	timesheet_ids = fields.One2many('account.analytic.line', 'task_id', 'Timesheets', domain=[('nn_sheet_id','!=',False)])
	
	@api.depends('material_estimation_ids.subtotal','labour_estimation_ids.subtotal','overhead_estimation_ids.subtotal')
	def _calculate_total(self):
		total_job_cost = 0.0
		for order in self:
			for line in order.material_estimation_ids:
				material_price =  (line.quantity * line.unit_price) - (line.quantity * line.unit_price) * (line.discount or 0.0) / 100.0
				order.total_material_estimate += material_price

				total_job_cost += material_price
		
			for line in order.labour_estimation_ids:
				labour_price =  (line.quantity * line.unit_price * line.hours) - (line.quantity * line.unit_price * line.hours) * (line.discount or 0.0) / 100.0
				order.total_labour_estimate += labour_price

				total_job_cost += labour_price
			
			for line in order.overhead_estimation_ids:
				overhead_price =  (line.quantity * line.unit_price) - (line.quantity * line.unit_price) * (line.discount or 0.0) / 100.0
				order.total_overhead_estimate += overhead_price
				total_job_cost += overhead_price
		
		order.total_job_estimate = total_job_cost

	@api.multi
	def task_confirm(self):
		self.write({'state':'confirmed'}) 

	@api.multi
	def task_draft(self):
		self.write({'state':'draft'})

	@api.multi
	def action_cancel(self):
		self.write({'state':'cancel'}) 

	@api.multi
	def _compute_total_material_cost(self):
		total = 0.0
		for line in self.material_job_cost_line_ids:
			total += line.subtotal
		self.total_material_cost = total
		
	# @api.multi
	# def _compute_total_labour_cost(self):
	#     total = 0.0
	#     for line in self.labour_job_cost_line_ids:
	#         total += line.subtotal
	#     self.total_labour_cost = total
		
	@api.multi
	def _compute_total_overhead_cost(self):
		total = 0.0
		for line in self.overhead_job_cost_line_ids:
			total += line.subtotal
		self.total_overhead_cost = total   
		
	def _compute_total_cost(self):
		total = 0.0
		for sheet in self:
			total = sheet.total_material_cost +  sheet.total_overhead_cost
			sheet.total_cost = total 
		
	@api.multi
	def actual_material(self):
		if self.name:
			self.material_job_cost_line_ids.unlink()
			vals = {}
			loc = []
			location_obj = self.env['stock.location']
			task =self.id
			project = self.project_id.analytic_account_id.id
			sour_loc = location_obj.search([('usage','=','internal'),('barcode','=','WH-STOCK')])
			loc.append(sour_loc.id)
			dest_loc = location_obj.search([('usage','=','production')])
			loc.append(dest_loc.id)
			res = self.env['n2n.stock.move.analysis.view'].search([('analytic_id','=',project),('task_id','=',task),('source','in',loc),('destination','in',loc)])
			# query = """SELECT sv.product_id as product,sv.qty as qty,
			#             sv.uom_id as uom,
			#             sv.price_unit as price
			#             FROM n2n_stock_move_analysis_view sv
			#             WHERE sv.analytic_id=%s AND sv.task_id = %s AND (sv.source = %s AND sv.destination = %s) OR (sv.source = %s AND sv.destination = %s)
			#         """
			# self.env.cr.execute(query,(project,task,sour_loc.id,dest_loc.id,dest_loc.id,sour_loc.id,))
			# res = self.env.cr.dictfetchall() 
			for i in res:
				self.env['materal.cost.line'].create({
					'product_id': i.product_id.id, 
					'quantity': i.qty, 
					'uom_id': i.uom_id.id, 
					'task_id':i.task_id.id,
					'unit_price': i.price_unit,
					'reference': i.picking_name,
					'material_job_cost_sheet_id':self.id
					})

	@api.multi
	def open_estimation_comparison(self):
		view_mode = 'tree,pivot'
		view_tree_id = self.env.ref('N2N_project_enhancement.n2n_material_estimate_combine_tree').id
		view_pivot_id = self.env.ref('N2N_project_enhancement.n2n_material_estimate_combine_pivot').id
		domain = [('parent_id','=',self.id)]

		return {
			'name':'Estimation Comparison Analysis',
			'type': 'ir.actions.act_window',
			'res_model': 'n2n.material.estimate.combine.view',
			'view_mode': view_mode,
			'views' : [(view_tree_id, 'tree'),
					  (view_pivot_id, 'pivot')],
			'res_id': False,
			'target': 'self',
			'domain': domain,
		}

	@api.multi
	def open_labour_comparison(self):
		view_mode = 'tree,pivot'
		view_tree_id = self.env.ref('N2N_project_enhancement.n2n_labour_estimate_combine_tree').id
		view_pivot_id = self.env.ref('N2N_project_enhancement.n2n_labour_estimate_combine_pivot').id
		domain = [('task_id','=',self.id)]

		return {
			'name':'Labour Comparison Analysis',
			'type': 'ir.actions.act_window',
			'res_model': 'n2n.labour.estimate.combine.view',
			'view_mode': view_mode,
			'views' : [(view_tree_id, 'tree'),
					  (view_pivot_id, 'pivot')],
			'res_id': False,
			'target': 'self',
			'domain': domain,
		}

	@api.multi
	def open_overhead_comparison(self):
		view_mode = 'tree,pivot'
		view_tree_id = self.env.ref('N2N_project_enhancement.n2n_overhead_estimate_combine_tree').id
		view_pivot_id = self.env.ref('N2N_project_enhancement.n2n_overhead_estimate_combine_pivot').id
		domain = [('task_id','=',self.id)]

		return {
			'name':'Labour Comparison Analysis',
			'type': 'ir.actions.act_window',
			'res_model': 'n2n.overhead.estimate.combine.view',
			'view_mode': view_mode,
			'views' : [(view_tree_id, 'tree'),
					  (view_pivot_id, 'pivot')],
			'res_id': False,
			'target': 'self',
			'domain': domain,
		}

	# @api.multi
	# def open_estimation_comparison(self):
	#     action = self.env.ref('N2N_project_enhancement.action_n2n_material_estimate_combine').read()[0]
	#     # ctx = self.env.context.copy()
	#     # ctx.update({
	#     #     'default_parent_id': self.id,
	#     #     'default_project_id': self.env.context.get('project_id', self.project_id.id),
	#     #     'default_name': self.env.context.get('name', self.name) + ':',
	#     #     'default_partner_id': self.env.context.get('partner_id', self.partner_id.id),
	#     #     'search_default_project_id': self.env.context.get('project_id', self.project_id.id),
	#     # })
	#     # action['context'] = ctx
	#     # action['domain'] = [('id', 'child_of', self.id), ('id', '!=', self.id)]
	#     return action

class MaterialEstimate(models.Model):
	_name = "material.estimate"

	@api.multi
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.uom_id = self.product_id.uom_id.id
		self.quantity = 1.0
		self.unit_price = self.product_id.standard_price
		
	@api.multi
	def get_currency_id(self):
		user_id = self.env.uid
		res_user_id = self.env['res.users'].browse(user_id)
		for line in self:
			line.currency_id = res_user_id.company_id.currency_id
			
	@api.onchange('quantity', 'unit_price','discount')
	def onchange_quantity(self):
		price = 0.0
		for line in self:
			price =  (line.quantity * line.unit_price) - (line.quantity * line.unit_price) * (line.discount or 0.0) / 100.0
			line.subtotal = price
			
	material_id = fields.Many2one('project.task','Material' )
	type = fields.Selection([('material','Material')],string='Type',default='material', readonly=1)
	product_id = fields.Many2one('product.product','Product',required=True)
	description = fields.Text('Description')
	quantity = fields.Float('Quantity',default=0.0)
	uom_id = fields.Many2one('uom.uom','Unit Of Measure')
	unit_price = fields.Float('Unit Price',defaut=0.0)
	discount = fields.Float('Discount (%)',default=0.0)
	subtotal = fields.Float('Sub Total',defalut=0.0)
	currency_id = fields.Many2one('res.currency', compute='get_currency_id', string="Currency")
	
class LabourEstimate(models.Model):
	_name = "labour.estimate"

	@api.multi
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.uom_id = self.product_id.uom_id.id
		self.quantity = 1.0
		self.unit_price = self.product_id.standard_price
		
	@api.multi
	def get_currency_id(self):
		user_id = self.env.uid
		res_user_id = self.env['res.users'].browse(user_id)
		for line in self:
			line.currency_id = res_user_id.company_id.currency_id


	@api.onchange('hours', 'unit_price', 'discount')
	def onchange_quantity(self):
		price = 0.0
		for line in self:
			price = (line.hours * line.unit_price) - (line.hours * line.unit_price) * (
						line.discount or 0.0) / 100.0
			line.subtotal = price

	labour_id = fields.Many2one('project.task','Labour', )
	type = fields.Selection([('labour','Labour')],string='Type',  default='labour', readonly=1)
	product_id = fields.Many2one('product.product','Product',required=True)
	description = fields.Text('Description')
	quantity = fields.Float('Quantity',default=0.0)
	uom_id = fields.Many2one('uom.uom','Unit Of Measure')
	unit_price = fields.Float('Unit Price',defaut=0.0)
	discount = fields.Float('Discount (%)',default=0.0)
	subtotal = fields.Float('Sub Total',defalut=0.0)
	currency_id = fields.Many2one('res.currency', compute='get_currency_id', string="Currency")
	hours = fields.Float('Hours', digits=(2,2))

	@api.one
	@api.constrains('hours')
	def _check_values(self):
		if self.hours <= 0.0 :
			raise Warning(_('Working hours should not be zero or Negative.'))


class OverheadEstimate(models.Model):
	_name = "overhead.estimate"
	
	@api.multi
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.uom_id = self.product_id.uom_id.id
		self.quantity = 1.0
		self.unit_price = self.product_id.standard_price
		
	@api.multi
	def get_currency_id(self):
		user_id = self.env.uid
		res_user_id = self.env['res.users'].browse(user_id)
		for line in self:
			line.currency_id = res_user_id.company_id.currency_id
			
	@api.onchange('quantity', 'unit_price','discount')
	def onchange_quantity(self):
		price = 0.0
		for line in self:
			price =  (line.quantity * line.unit_price) - (line.quantity * line.unit_price) * (line.discount or 0.0) / 100.0
			line.subtotal = price
			
	overhead_id = fields.Many2one('project.task','Overhead')
	type = fields.Selection([('overhead','Overhead')],string='Type',default='overhead', readonly=1)
	product_id = fields.Many2one('product.product','Product',required=True)
	description = fields.Text('Description')
	quantity = fields.Float('Quantity',default=0.0)
	uom_id = fields.Many2one('uom.uom','Unit Of Measure')
	unit_price = fields.Float('Unit Price',defaut=0.0)
	discount = fields.Float('Discount (%)',default=0.0)
	subtotal = fields.Float('Sub Total',defalut=0.0)
	currency_id = fields.Many2one('res.currency', compute='get_currency_id', string="Currency")

class ActualMaterialLine(models.Model):
	_name = "materal.cost.line"
	
	material_job_cost_sheet_id = fields.Many2one('project.task','Material Job Cost Sheet')
	date = fields.Datetime('Date',default=datetime.now())
	# job_type_id = fields.Many2one('job.type',string='Job Type')
	product_id = fields.Many2one('product.product','Product')
	description = fields.Text('Description')
	reference = fields.Char('Reference')
	quantity = fields.Float('Quantity',default=1.0)
	uom_id = fields.Many2one('uom.uom','Unit Of Measure')
	unit_price = fields.Float('Cost/Unit Price',defaut=0.0)
	# actual_purchase_qty = fields.Float(compute='_compute_purchase_quantity',string='Actual Purchased Quantity',default=0.0)
	# actual_invoice_qty = fields.Float(compute='_compute_invoice_quantity',string='Actual Invoice Quantity',default=0.0)
	subtotal = fields.Float(compute='onchange_quantity',string='Sub Total',defalut=0.0)
	currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
	job_type = fields.Selection([('material','Material'),('labour','Labour'),('overhead','Overhead')],string="Job Cost Order Type")
	#Labour
	task_id = fields.Many2one('project.task', string="Task")
	hours = fields.Float('Hours',default=0.0)
	actual_timesheet_hours = fields.Float('Actual Timesheet Hours',default=0.0)
	#Overhead
	basis = fields.Char('Basis')


	@api.onchange('quantity', 'unit_price')
	def onchange_quantity(self):
		for line in self:
			price = line.quantity * line.unit_price
			if line.hours:
				price = line.hours * line.unit_price
			line.subtotal = price
			
	@api.multi
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.uom_id = self.product_id.uom_id.id
		self.description = self.product_id.name
		
	@api.multi
	def get_currency_id(self):
		user_id = self.env.uid
		res_user_id = self.env['res.users'].browse(user_id)
		for line in self:
			line.currency_id = res_user_id.company_id.currency_id

class ActualOverheadLine(models.Model):
	_name = "overhead.cost.line"
	
	overhead_job_cost_sheet_id = fields.Many2one('project.task','Overhead Job Cost Sheet')
	date = fields.Datetime('Date',default=datetime.now())
	# job_type_id = fields.Many2one('job.type',string='Job Type')
	product_id = fields.Many2one('product.product','Product')
	description = fields.Text('Description')
	reference = fields.Char('Reference')
	quantity = fields.Float('Quantity',default=1.0)
	uom_id = fields.Many2one('uom.uom','Unit Of Measure')
	unit_price = fields.Float('Cost/Unit Price',defaut=0.0)
	# actual_purchase_qty = fields.Float(compute='_compute_purchase_quantity',string='Actual Purchased Quantity',default=0.0)
	# actual_invoice_qty = fields.Float(compute='_compute_invoice_quantity',string='Actual Invoice Quantity',default=0.0)
	subtotal = fields.Float(compute='onchange_quantity',string='Sub Total',defalut=0.0)
	currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
	job_type = fields.Selection([('material','Material'),('labour','Labour'),('overhead','Overhead')],string="Job Cost Order Type")
	#Labour
	hours = fields.Float('Hours',default=0.0)
	actual_timesheet_hours = fields.Float('Actual Timesheet Hours',default=0.0)
	#Overhead
	basis = fields.Char('Basis')


	@api.onchange('quantity', 'unit_price')
	def onchange_quantity(self):
		for line in self:
			price = line.quantity * line.unit_price
			if line.hours:
				price = line.hours * line.unit_price
			line.subtotal = price
			
	@api.multi
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.uom_id = self.product_id.uom_id.id
		self.description = self.product_id.name
		
	@api.multi
	def get_currency_id(self):
		user_id = self.env.uid
		res_user_id = self.env['res.users'].browse(user_id)
		for line in self:
			line.currency_id = res_user_id.company_id.currency_id


class AccountAnalyticLine(models.Model):
	_inherit = "account.analytic.line"   

	product_id = fields.Many2one('product.product','Product')
	# over_head = fields.Boolean(string="Overhead", default=False)

class ProjectProject(models.Model):
	_inherit = 'project.project'

	@api.model
	def create(self , vals):
		vals['sequence'] = self.env['ir.sequence'].next_by_code('project.project') or '/'
		return super(ProjectProject, self).create(vals)

	@api.multi
	def write(self, vals):
		res = super(ProjectProject, self).write(vals)
		for rec in self:
			analytic = self.env['account.analytic.account'].search([('name','=',rec.name)])
			analytic.code = rec.sequence
		return res

	@api.multi
	def open_pro_estimation_comparison(self):
		view_mode = 'tree,pivot'
		view_tree_id = self.env.ref('N2N_project_enhancement.n2n_material_estimate_combine_tree').id
		view_pivot_id = self.env.ref('N2N_project_enhancement.n2n_material_estimate_combine_pivot').id
		domain = [('project_id','=',self.analytic_account_id.id)]

		return {
			'name':'Estimation Comparison Analysis',
			'type': 'ir.actions.act_window',
			'res_model': 'n2n.material.estimate.combine.view',
			'view_mode': view_mode,
			'views' : [(view_tree_id, 'tree'),
					  (view_pivot_id, 'pivot')],
			'res_id': False,
			'target': 'self',
			'domain': domain,
		}

	@api.multi
	def _get_purchase_order_count(self):
		for po in self:
			po_ids = self.env['purchase.order'].search([('analytic_id','=',po.analytic_account_id.id)])
			po.purchase_order_count_1 = len(po_ids)

	@api.multi
	def purchase_order_button(self):
		self.ensure_one()
		return {
			'name': 'Purchase Order',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'purchase.order',
			'domain': [('analytic_id', '=', self.analytic_account_id.id)],
		}

	@api.multi
	def _get_bill_count(self):
		for po in self:
			po_ids = self.env['account.invoice'].search([('analytic_id','=',po.analytic_account_id.id),('type','in',['in_invoice','in_refund'])])
			po.bill_order_count = len(po_ids)

	@api.multi
	def bill_order_button(self):
		self.ensure_one()
		return {
			'name': 'Vendor Bills',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'account.invoice',
			'domain': [('analytic_id', '=', self.analytic_account_id.id)],
		}

	@api.multi
	def _get_invoice_count(self):
		for so in self:
			line_id = self.env['account.invoice.line'].search([('account_analytic_id','=',so.analytic_account_id.id),('invoice_id.type','=','out_invoice')])
			inv_lines = self.env['account.invoice.line'].browse(line_id).ids
			if len(inv_lines) > 0:
				ids = [inv_line.invoice_id.id for inv_line in inv_lines]
				self.invoice_count = len(self.env['account.invoice'].search([('id','in',ids)]))
	
	@api.multi
	def invoice_order_button(self):
		self.ensure_one()
		line_id = self.env['account.invoice.line'].search([('account_analytic_id','=',self.analytic_account_id.id),('invoice_id.type','=','out_invoice')])
		inv_lines = self.env['account.invoice.line'].browse(line_id).ids
		return {
			'name': 'Invoices',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'account.invoice',
			'views' : [(self.env.ref('account.invoice_tree').id, 'tree'), (self.env.ref('account.invoice_form').id, 'form')],
			'domain': [('id', 'in', [line.invoice_id.id for line in inv_lines])],
		}

	purchase_order_count_1 = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
	bill_order_count = fields.Integer('Vendor Bill', compute='_get_bill_count')
	invoice_count = fields.Integer('Invoices', compute='_get_invoice_count')
	stand_name = fields.Text(string="Stand Name")
	venue = fields.Char(string="Venue")
	date_from = fields.Datetime(string="From Date")
	date_to = fields.Datetime(string="To Date")
	sequence = fields.Char(string='Sequence', readonly=True,copy =False)

class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	analytic_id =fields.Many2one('account.analytic.account',string="Project", readonly=True, states={'draft': [('readonly', False)]})
	task_id = fields.Many2one('project.task', string="Task", readonly=True, states={'draft': [('readonly', False)]})

	def _prepare_invoice_line_from_po_line(self, line):
		res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
		self.analytic_id = line.order_id.analytic_id.id
		self.task_id = line.order_id.task_id.id
		return res

# class AccountAnalyticAccount(models.Model):
#     _inherit = 'account.analytic.account'

#     @api.model
# 	def create(self , vals):
# 		vals['sequence'] = self.env['ir.sequence'].next_by_code('project.project') or '/'
# 		return super(ProjectProject, self).create(vals)

#     sequence = fields.Char(string='Sequence', readonly=True)


