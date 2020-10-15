# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools

class n2n_labour_estimate_combine_view(models.Model):
	_name = "n2n.labour.estimate.combine.view"
	_description = "N2N Labour Combine View"
	_auto = False

	product_id = fields.Many2one('product.product', string="Product")
	employee_id = fields.Many2one('hr.employee', string="Employee")
	task_id = fields.Many2one('project.task', string="Task")
	estimate_qty = fields.Float(string="Estimate Qty")
	estimate_value = fields.Float(string="Estimate Value")
	actual_qty = fields.Float(string="Actual Qty")
	actual_value = fields.Float(string="Actual Value")
	deviation_qty = fields.Float(string="Deviation Qty")
	deviation_value = fields.Float(string="Deviation Value")

	@api.model_cr
	def init(self):
		tools.drop_view_if_exists(self._cr, 'n2n_labour_estimate_combine_view')
		self._cr.execute("""
			CREATE OR REPLACE VIEW n2n_labour_estimate_combine_view AS
			SELECT row_number() over() AS id, 
		    foo.product_id AS product_id,
		    foo.task_id AS task_id,
		    foo.employee_id AS employee_id,
		    sum(foo.estimated_lab_qty) as estimate_qty,
		    sum(foo.actual_lab_qty)as actual_qty,
		    sum(foo.estimated_lab_value) as estimate_value,
		    sum(foo.actual_lab_value) as actual_value,
		    sum((foo.estimated_lab_qty)-(foo.actual_lab_qty)) as deviation_qty,
		    sum((foo.estimated_lab_value)-(foo.actual_lab_value)) as deviation_value
		    
		   FROM (  SELECT
		            labour.labour_id AS task_id,
			     CASE
		             WHEN labour.id >0 THEN NULL
		             END AS employee_id,
		            CASE
		             WHEN (labour.id)::integer >0::integer THEN labour.product_id
		             ELSE NULL
		             END AS product_id,		            
		            CASE
		             WHEN labour.id >0::numeric THEN labour.quantity::numeric
		             ELSE 0::numeric
		             END AS estimated_lab_qty,
		            CASE
		             WHEN labour.id >0::numeric THEN 0::numeric
		             END AS actual_lab_qty,
		            CASE
		             WHEN labour.id >0::numeric THEN labour.unit_price::numeric
		             ELSE 0::numeric
		             END AS estimated_lab_value,
		            CASE
		             WHEN labour.id >0::numeric THEN 0::numeric
		             END AS actual_lab_value	
		             
		             FROM labour_estimate labour
		   		            
		         UNION 
		         SELECT 
		            account.task_id AS task_id,
		            CASE
		            WHEN account.id >0 THEN NULL
		            END AS product_id,
		            CASE
		             WHEN (account.id)::integer >0::integer THEN account.employee_id
		             ELSE NULL
		             END AS employee_id, 
		            CASE
		             WHEN account.id >0::numeric THEN 0::numeric
		             END AS estimated_lab_qty,
		            CASE
		             WHEN account.id >0::numeric THEN account.unit_amount::numeric
		             ELSE 0::numeric
		             END AS actual_lab_qty,
		            CASE
		             WHEN account.id >0::numeric THEN 0::numeric
		             END AS estimated_lab_value,
		            CASE
		             WHEN account.id >0::numeric THEN account.amount::numeric
		             ELSE 0::numeric
		             END AS actual_lab_value		             
		            FROM account_analytic_line account) foo
		          --where foo.task_id=33
		  GROUP BY foo.product_id, foo.task_id, foo.employee_id

					""")