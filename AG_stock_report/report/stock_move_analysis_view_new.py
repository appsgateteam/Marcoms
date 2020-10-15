# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools
from odoo.exceptions import UserError, AccessError

class N2NStockMoveAnalysisView(models.Model):
	_name = "n2n.stock.move.analysis.view"
	_description = "N2N Stock Move Analysis"
	_auto = False
	_order = 'date'
	_rec_name = 'date'

	date = fields.Date(string="Date")
	move_id = fields.Many2one('stock.move',string='Stock  Move')
	product_id = fields.Many2one('product.product', string='Product')
	location = fields.Many2one('stock.location',string='Location')
	qty = fields.Float(string='Quantity')
	value = fields.Float(string='Value')
	origin = fields.Char(string='Origin')
	warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
	batch_name = fields.Char(string="Batch Name")
	source = fields.Many2one('stock.location', string='Source')
	destination = fields.Many2one('stock.location', string='Destination')
	categ_id = fields.Many2one('product.category',string='Category')
	# nn_pdt_group_id = fields.Many2one('nn.product.group',string='Group')
	# nn_pdt_sub_group_id = fields.Many2one('nn.product.sub.group',string='Sub Group')
	# nn_pdt_type_id = fields.Many2one('nn.product.type',string='Type')
	src_usage = fields.Char(string='Src Usage')
	des_usage = fields.Char(sring='Des Usage')
	move = fields.Char(string='Move')
	type = fields.Char(string='Operation Type')
	uom_id = fields.Many2one('uom.uom',string='UOM')
	partner_id = fields.Many2one('res.partner',string='Partner')
	analytic_id =fields.Many2one('account.analytic.account',string="Project")
	task_id = fields.Many2one('project.task', string="Task")
	price_unit = fields.Float(string='Unit Price')

	 

 
	@api.model_cr
	def init(self):
		# cr = self.env.cr   
		tools.drop_view_if_exists(self._cr, 'n2n_stock_move_analysis_view')
		self._cr.execute("""
			CREATE OR REPLACE VIEW n2n_stock_move_analysis_view AS
			SELECT row_number() over() AS id,
			sm.date::DATE as date,
			sm.id as move_id,
			sm.product_id as product_id,
			sp.analytic_id as analytic_id,
			sp.task_id as task_id,
			sm.product_qty as qty,
			sm.value as value,
			sm.origin as origin,
			sm.warehouse_id as warehouse_id,
			sml.lot_name as batch_name,
			sm.location_id as source,
			sm.location_dest_id as destination,
			sp.partner_id as partner_id,
			pt.categ_id as categ_id,
			sm.price_unit as price_unit,
			-- pt.nn_pdt_group_id as nn_pdt_group_id,
			-- pt.nn_pdt_sub_group_id as nn_pdt_sub_group_id,
			-- pt.nn_pdt_type_id as nn_pdt_type_id,
			sm.location_id as location,
			pt.uom_id as uom_id,
			srcloc.usage as src_usage,
			desloc.usage as des_usage,
			CASE
			WHEN sm.product_qty < 0::numeric THEN 'OUT'
			ELSE 'IN'
			END AS move,
			CASE
			WHEN srcloc.usage='internal' AND desloc.usage='production' AND sm.product_qty>0 THEN 'Internal Transfer'
			WHEN srcloc.id='24' AND desloc.usage='internal' AND sm.product_qty>0 THEN 'Restaurant Return'
			/*WHEN srcloc.usage='internal' AND desloc.usage='internal' AND sm.product_qty>0 THEN 'Transfer In'*/
			WHEN srcloc.usage='internal' AND desloc.usage='customer' THEN 'Sales'
			WHEN srcloc.usage='customer' AND desloc.usage='internal' THEN 'Sales Return'
			WHEN srcloc.usage='supplier' AND desloc.usage='internal' THEN 'Central Purchase'
			WHEN srcloc.usage='internal' AND desloc.usage='supplier' THEN 'Central Purchase Return'
			WHEN srcloc.usage='supplier' AND desloc.id ='24'  THEN 'Restaurant Purchase'
			WHEN srcloc.id='24' AND desloc.usage='supplier' THEN 'Restaurant Purchase Return'
			WHEN srcloc.usage='internal' AND desloc.usage='inventory' THEN 'Inventory Adjustment'
			/*WHEN srcloc.usage='inventory' AND desloc.usage='internal' THEN 'Adjustment In'*/
			/*WHEN srcloc.usage='internal' AND desloc.scrap_location='True' THEN 'Wastage Adjustment'*/

			/*WHEN srcloc.usage='internal' AND desloc.usage='production' THEN 'Production RM'
			WHEN srcloc.usage='production' AND desloc.usage='internal' THEN 'Production FP'
			WHEN srcloc.usage='internal' AND desloc.usage='transit' THEN 'Transit In'
			WHEN srcloc.usage='transit' AND desloc.usage='internal' THEN 'Transit Out'*/
			ELSE 'Wastage Adjustment'
			END AS type
			FROM stock_move sm
			LEFT JOIN stock_location srcloc ON sm.location_id=srcloc.id
			LEFT JOIN stock_location desloc ON sm.location_dest_id=desloc.id
			LEFT JOIN stock_picking sp ON sm.picking_id=sp.id
			LEFT JOIN stock_move_line sml ON sm.id=sml.move_id
			INNER JOIN product_product pp ON sm.product_id=pp.id
			INNER JOIN product_template pt ON pp.product_tmpl_id=pt.id
			GROUP BY sm.product_id,sm.date,sm.id,desloc.id,srcloc.id,
			sm.product_id,
			sm.product_qty,
			sm.value,
			sm.origin,
			sm.warehouse_id,
			sml.lot_name,
			sm.location_id,
			sm.location_dest_id,
			sp.partner_id,
			pt.categ_id,
			sp.analytic_id,
			sp.task_id,
			-- pt.nn_pdt_group_id,
			-- pt.nn_pdt_sub_group_id,
			-- pt.nn_pdt_type_id,
			pt.uom_id,
			srcloc.usage,
			desloc.usage
					""")
