# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools

class n2n_overhead_estimate_combine_view(models.Model):
	_name = "n2n.overhead.estimate.combine.view"
	_description = "N2N Overhead Combine View"
	_auto = False

	product_id = fields.Many2one('product.product', string="Product")
	task_id = fields.Many2one('project.task', string="Task")
	estimate_qty = fields.Float(string="Estimate Qty")
	estimate_value = fields.Float(string="Estimate Value")
	actual_qty = fields.Float(string="Actual Qty")
	actual_value = fields.Float(string="Actual Value")
	deviation_qty = fields.Float(string="Deviation Qty")
	deviation_value = fields.Float(string="Deviation Value")

	@api.model_cr
	def init(self):
		tools.drop_view_if_exists(self._cr, 'n2n_overhead_estimate_combine_view')
		self._cr.execute("""
			CREATE OR REPLACE VIEW n2n_overhead_estimate_combine_view AS
			
			SELECT row_number() over() AS id, 
			foo.product_id AS product_id,
			foo.task_id AS task_id,
			sum(foo.estimated_over_qty) as estimate_qty,
			sum(foo.actual_over_qty)as actual_qty,
			sum(foo.estimated_over_value) as estimate_value,
			sum(foo.actual_over_value) as actual_value,
			sum((foo.estimated_over_qty)-(foo.actual_over_qty)) as deviation_qty,
			sum((foo.estimated_over_value)-(foo.actual_over_value)) as deviation_value
			FROM (select account.product_id AS product_id,
			account.task_id AS task_id,
			CASE
			 WHEN account.id >0::numeric THEN 0::numeric
			END AS estimated_over_qty,
			CASE
			WHEN account.id >0::numeric THEN account.unit_amount::numeric
			ELSE 0::numeric
			END AS actual_over_qty,
			CASE
			WHEN account.id >0::numeric THEN 0::numeric
			END AS estimated_over_value,
			CASE
			WHEN account.id >0::numeric THEN account.amount::numeric
			ELSE 0::numeric
			END AS actual_over_value
			from account_analytic_line account
			UNION ALL
			select over.product_id AS product_id,
			over.overhead_id AS task_id,
			CASE
			 WHEN over.id >0::numeric THEN over.quantity::numeric
			ELSE 0::numeric
			END AS estimated_over_qty,
			CASE
			WHEN over.id >0::numeric THEN 0::numeric
			ELSE 0::numeric
			END AS actual_over_qty,
			CASE
			WHEN over.id >0::numeric THEN over.unit_price::numeric
			ELSE 0::numeric
			END AS estimated_over_value,
			CASE
			WHEN over.id >0::numeric THEN 0::numeric
			ELSE 0::numeric
			END AS actual_over_value
			from overhead_estimate over)foo
			GROUP BY foo.product_id, foo.task_id

		""")