# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools
from odoo.exceptions import UserError, AccessError
from datetime import datetime, timedelta

class n2n_stock_move_analysis_wizard(models.TransientModel):
	_name = 'n2n.st.move.analysis.wizard'
	_description = 'N2N Stock Move Analysis'

	product_id = fields.Many2one('product.product', string='Product')
	quantity = fields.Float(string='Quantity')
	value = fields.Float(string='Value')
	date_from = fields.Date(string='Date From',required=True,default=fields.Date.context_today)
	date_to = fields.Date(string='Date To',required=True,default=fields.Date.context_today)
	location_id = fields.Many2one('stock.location',string='Location')
	analytic_id =fields.Many2one('account.analytic.account',string="Project")
	task_id = fields.Many2one('project.task', string='Task')
	# nn_pdt_group_id = fields.Many2one('nn.product.group',string='Group')
	# nn_pdt_sub_group_id = fields.Many2one('nn.product.sub.group',string='Sub Group')
	# nn_pdt_type_id = fields.Many2one('nn.product.type',string='Type')
	categ_id = fields.Many2one('product.category',string='Category')
	nn_type = fields.Selection([('Sales', 'Sales'),('Sales Return', 'Sales Return'),('Purchase', 'Purchase'),('Purchase Return', 'Purchase Return'),('Material Issue','Material Issue'),('Material Issue Return','Material Issue Return'),('Inventory Adjustment','Inventory Adjustment')],"Operation Type")
	#with_value = fields.Boolean(string='With Value')    



	@api.multi
	def generate(self):
		data = {}
		domain_filter = []
		if self.date_to < self.date_from:
			raise UserError(_('Invalid date selection'))
		datefrom = datetime.strptime(str(self.date_from),'%Y-%m-%d')
		dateto = datetime.strptime(str(self.date_to),'%Y-%m-%d')
		end_date = dateto + timedelta(days=1)
		domain_filter.append(('date','>=',datefrom))
		domain_filter.append(('date','<=',end_date))
		if self.product_id:
			domain_filter.append(('product_id','=',self.product_id.id))
		if self.quantity:
			domain_filter.append(('quantity','=',self.quantity))
		if self.value:
			domain_filter.append(('value','=',self.value))
		if self.location_id:
			domain_filter.append(('location','=',self.location_id.id))
		if self.analytic_id:
			domain_filter.append(('analytic_id','=',self.analytic_id.id))
		if self.task_id:
			domain_filter.append(('task_id','=',self.task_id.id))
		# if self.nn_pdt_group_id:
		# 	domain_filter.append(('nn_pdt_group_id','=',self.nn_pdt_group_id.id))
		# if self.nn_pdt_sub_group_id:
		# 	domain_filter.append(('nn_pdt_sub_group_id','=',self.nn_pdt_sub_group_id.id))
		# if self.nn_pdt_type_id:
		# 	domain_filter.append(('nn_pdt_type_id','=',self.nn_pdt_type_id.id))
		if self.categ_id:
			domain_filter.append(('categ_id','=',self.categ_id.id))
		if self.nn_type:
			domain_filter.append(('type','=',self.nn_type))
		action = self.env.ref('N2N_project_enhancement.action_n2n_stock_move_analysis_new')
		result = action.read()[0]
		result['domain'] = str(domain_filter)
		# result['context']['default_with_value'] = True
		return result
	# 
