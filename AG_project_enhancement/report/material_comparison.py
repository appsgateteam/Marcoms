# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools

class n2n_material_estimate_base_view(models.Model):
	_name = "n2n.material.estimate.base.view"
	_description = "N2N Material Base View"
	_auto = False

	product_id = fields.Many2one('product.product', string="Product")
	task_id = fields.Many2one('project.task', string="Task")

	@api.model_cr
	def init(self):
		tools.drop_view_if_exists(self._cr, 'n2n_material_estimate_base_view')
		self._cr.execute("""
			CREATE OR REPLACE VIEW n2n_material_estimate_base_view AS
			((SELECT 
			me.product_id as product_id,
			me.material_id as task_id
			FROM material_estimate me)
			UNION ALL
			(SELECT 
			ns.product_id as product_id,
			ns.task_id as task_id
			FROM N2N_stock_move_analysis_view ns))
			""")



class n2n_material_estimate_combine_view(models.Model):
	_name = "n2n.material.estimate.combine.view"
	_description = "N2N Material Combine View"
	_auto = False

	product_id = fields.Many2one('product.product', string="Product")
	task_id = fields.Many2one('project.task', string="Task")
	project_id = fields.Many2one('project.project', string="Project")
	estimate_qty = fields.Float(string="Estimate Qty")
	estimate_value = fields.Float(string="Estimate Value")
	actual_qty = fields.Float(string="Actual Qty")
	actual_value = fields.Float(string="Actual Value")
	deviation_qty = fields.Float(string="Deviation Qty")
	deviation_value = fields.Float(string="Deviation Value")
	parent_id = fields.Char(string="Parent")
	project_id = fields.Many2one('project.project', string="Project")
	

	@api.model_cr
	def init(self):
		tools.drop_view_if_exists(self._cr, 'n2n_material_estimate_combine_view')
		self._cr.execute("""
			CREATE OR REPLACE VIEW n2n_material_estimate_combine_view AS
			SELECT row_number() over() AS id, 
			-- mbv.product_id AS product_id,
			-- mbv.task_id AS task_id,
			-- mv.analytic_id AS project_id,
			-- me.quantity AS estimate_qty,
			-- me.unit_price AS estimate_value,
			-- mv.qty AS actual_qty,
			-- mv.price_unit AS actual_value,
			-- (me.quantity-mv.qty) AS deviation_qty,
			-- (me.unit_price-(-mv.price_unit)) AS deviation_value
			-- FROM n2n_material_estimate_base_view mbv
			-- LEFT JOIN N2N_stock_move_analysis_view mv ON (mv.task_id = mbv.task_id  and mv.product_id = mbv.product_id)
			-- LEFT JOIN material_estimate me ON me.material_id = mbv.task_id
			

		    foo.product_id AS product_id,
		    foo.task_id AS task_id,
		    foo.parent_id AS parent_id,
		    foo.project_id AS project_id,
		    sum(foo.estimated_qty) as estimate_qty,
		    sum(foo.actual_qty)as actual_qty,
		    sum(foo.estimated_value) as estimate_value,
		    sum(foo.actual_value) as actual_value,
		    sum((foo.estimated_qty)-(foo.actual_qty)) as deviation_qty,
		    sum((foo.estimated_value)-(foo.actual_value)) as deviation_value
		    
		   FROM ( SELECT
		            estimate.material_id AS task_id,
		            estimate.product_id AS product_id,
		            pt.project_id AS project_id,
		            CASE
		             WHEN pt.parent_id IS NULL THEN pt.id
		             ELSE pt.parent_id
		             END AS parent_id,
		            CASE
		             WHEN estimate.id >0::numeric THEN estimate.quantity::numeric
		             ELSE '0'::numeric
		             END AS estimated_qty,
		            CASE
		             WHEN estimate.id >0::numeric THEN '0'::numeric
		             END AS actual_qty,
		            CASE
		             WHEN estimate.id >0::numeric THEN estimate.subtotal::numeric
		             ELSE '0'::numeric
		             END AS estimated_value,
		            CASE
		             WHEN estimate.id >0::numeric THEN '0'::numeric
		             END AS actual_value
		             
		            FROM material_estimate estimate
		            LEFT JOIN project_task pt ON pt.id = estimate.material_id 
		            
		         UNION ALL
		         
		         SELECT
		            actual.task_id AS task_id,
		            actual.product_id AS product_id,
		            pt.project_id AS project_id,
		            CASE
		             WHEN pt.parent_id IS NULL THEN pt.id
		             ELSE pt.parent_id
		             END AS parent_id,
		            
		            CASE
		             WHEN actual.id >0::numeric THEN '0'::numeric
		             END AS estimated_qty,
		             
		            CASE
		             WHEN actual.id >0::numeric THEN actual.qty::numeric
		             ELSE '0'::numeric
		             END AS actual_qty,
		             
		             CASE
		             WHEN actual.id >0::numeric THEN '0'::numeric
		             END AS estimated_value,
		             
		            CASE
		             WHEN actual.id >0::numeric THEN (actual.value)*-1::numeric
		             ELSE '0'::numeric
		             END AS actual_value
		             
		             FROM n2n_stock_move_analysis_view actual
		             LEFT JOIN project_task pt ON pt.id = actual.task_id
		             WHERE actual.source in (12,7) AND actual.destination in (12,7)) foo
		          -- where foo.task_id=36
		  GROUP BY foo.product_id, foo.task_id, foo.parent_id, foo.project_id

					""")