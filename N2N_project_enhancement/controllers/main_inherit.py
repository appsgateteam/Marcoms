# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.sale_timesheet.controllers.main import SaleTimesheetController
from ast import literal_eval
from odoo.addons.web.controllers.main import clean_action

class SaleTimesheetControllerInherit(SaleTimesheetController):

	#@http.route('/timesheet/plan', type='json', auth="user")
	# def material_details(self , **kwargs):
	# 		material_details = request.env['material.estimate'].sudo().search([])
	# 		request.httprequest.material_details)
	# 		print(data)
	# 		return  request.render('N2N_project_enhancement.material_details_page', {'my_details': material_details})
	@http.route('/timesheet/plan', type='json', auth="user")
	def plan(self, domain):
		res = super(SaleTimesheetControllerInherit,self).plan(domain)
		return res
	
	def _plan_prepare_values(self, projects):
		res = super(SaleTimesheetControllerInherit,self)._plan_prepare_values(projects)
		# print("inherited _plan_prepare_values",res)
		material_est_values = {
			'estimate_qty': 0.0,
			'estimate_value': 0.0,
			'actual_qty': 0.0,
			'actual_value': 0.0,
			'dev_qty': 0.0,
			'dev_value': 0.0,
		}
		labour_est_values = {
			'estimate_lab_qty': 0.0,
			'estimate_lab_value': 0.0,
			'actual_lab_qty': 0.0,
			'actual_lab_value': 0.0,
			'dev_lab_qty': 0.0,
			'dev_lab_value': 0.0,
		}
		over_est_values = {
			'estimate_ovr_qty': 0.0,
			'estimate_ovr_value': 0.0,
			'actual_ovr_qty': 0.0,
			'actual_ovr_value': 0.0,
			'dev_ovr_qty': 0.0,
			'dev_ovr_value': 0.0,
		}
		task_ids = request.env['project.task'].sudo().search([('project_id', 'in', projects.ids)])
		for task in task_ids:
			material_data = request.env['material.estimate'].sudo().search([('material_id','=', task.id)])
			for material in material_data:
				print("material_data",material.quantity)
				material_est_values['estimate_qty']+=material.quantity
				material_est_values['estimate_value']+=material.unit_price
			actual_data = request.env['materal.cost.line'].sudo().search([('task_id','=', task.id)])
			for actual in actual_data:
				material_est_values['actual_qty']+=actual.quantity
				material_est_values['actual_value']+=actual.unit_price
			labour_data = request.env['labour.estimate'].sudo().search([('labour_id','=', task.id)])
			for labour in labour_data:
				labour_est_values['estimate_lab_qty']+=labour.quantity
				labour_est_values['estimate_lab_value']+=labour.unit_price
			actual_labour = request.env['account.analytic.line'].sudo().search([('task_id','=', task.id),('nn_sheet_id','!=',False)])
			for actlab in actual_labour:
				labour_est_values['actual_lab_qty']+=actlab.unit_amount
				labour_est_values['actual_lab_value']+=actlab.amount
			over_data = request.env['overhead.estimate'].sudo().search([('overhead_id','=', task.id)])
			for over in over_data:
				over_est_values['estimate_ovr_qty']+=over.quantity
				over_est_values['estimate_ovr_value']+=over.unit_price
			actual_over = request.env['account.analytic.line'].sudo().search([('task_id','=', task.id),('nn_overhead_id','!=',False)])
			for actover in actual_over:
				over_est_values['actual_ovr_qty']+=actover.unit_amount
				over_est_values['actual_ovr_value']+=actover.amount
		material_est_values['dev_qty'] = material_est_values['estimate_qty'] - material_est_values['actual_qty'] 
		material_est_values['dev_value'] = material_est_values['estimate_value'] - material_est_values['actual_value'] 
		labour_est_values['dev_lab_qty'] = labour_est_values['estimate_lab_qty'] - labour_est_values['actual_lab_qty'] 
		labour_est_values['dev_lab_value'] = labour_est_values['estimate_lab_value'] - labour_est_values['actual_lab_value'] 
		over_est_values['dev_ovr_qty'] = over_est_values['estimate_ovr_qty'] - over_est_values['actual_ovr_qty'] 
		over_est_values['dev_ovr_value'] = over_est_values['estimate_ovr_value'] - over_est_values['actual_ovr_value'] 
		res['material'] = material_est_values
		res['labour'] = labour_est_values
		res['overhead'] = over_est_values
		return res

	def _plan_get_stat_button(self, projects):
		results = super(SaleTimesheetControllerInherit,self)._plan_get_stat_button(projects)
		print("inherited_plan_get_stat_button",results)
		po_id = request.env['purchase.order'].search([('analytic_id','in',[project.analytic_account_id.id for project in projects]),('state','in',('purchase', 'done'))])        
		po_lines = request.env['purchase.order'].browse(po_id).ids
		results.append({
			'name': _('Purchase Orders'),
			'count': len(po_lines),
			'res_model': 'purchase.order',
			'domain': [('id', 'in', [line.id for line in po_lines]),('state','in',('purchase', 'done'))],
			'icon': 'fa fa-book',
		})
		line_id1 = request.env['account.invoice'].search([('analytic_id','in',[project.analytic_account_id.id for project in projects]),('type','=','in_invoice')])        
		inv_lines1 = request.env['account.invoice'].browse(line_id1).ids
		print('inv_lines1',[line.id for line in inv_lines1])
		results.append({
			'name': _('Vendor Bills'),
			'count': len(inv_lines1),
			'res_model': 'account.invoice',
			'domain': [('id', 'in', [line.id for line in inv_lines1])],
			'icon': 'fa fa-book',
		})
		line_id = request.env['account.invoice.line'].search([('account_analytic_id','in',[project.analytic_account_id.id for project in projects]),('invoice_id.type','=','out_invoice')])        
		inv_lines = request.env['account.invoice.line'].browse(line_id).ids
		print('inv_lines',[line.invoice_id.id for line in inv_lines])
		results.append({
			'name': _('Customer Invoices'),
			'count': len(inv_lines),
			'res_model': 'account.invoice',
			'domain': [('id', 'in', [line.invoice_id.id for line in inv_lines])],
			'icon': 'fa fa-book',
		})
		return results

	
	@http.route('/timesheet/plan/action', type='json', auth="user")
	def plan_stat_button(self, domain=[], res_model='account.analytic.line', res_id=False):
		action = {
			'type': 'ir.actions.act_window',
			'view_id': False,
			'view_mode': 'tree,form',
			'view_type': 'list',
			'domain': domain,
		}
		if res_model == 'project.project':
			view_form_id = request.env.ref('project.edit_project').id
			action = {
				'name': _('Project'),
				'type': 'ir.actions.act_window',
				'res_model': res_model,
				'view_mode': 'form',
				'view_type': 'form',
				'views': [[view_form_id, 'form']],
				'res_id': res_id,
			}
		elif res_model == 'account.analytic.line':
			ts_view_tree_id = request.env.ref('hr_timesheet.hr_timesheet_line_tree').id
			ts_view_form_id = request.env.ref('hr_timesheet.hr_timesheet_line_form').id
			action = {
				'name': _('Timesheets'),
				'type': 'ir.actions.act_window',
				'res_model': res_model,
				'view_mode': 'tree,form',
				'view_type': 'form',
				'views': [[ts_view_tree_id, 'list'], [ts_view_form_id, 'form']],
				'domain': domain,
			}
		elif res_model == 'project.task':
			action = request.env.ref('project.action_view_task').read()[0]
			action.update({
				'name': _('Tasks'),
				'domain': domain,
				'context': dict(request.env.context),  # erase original context to avoid default filter
			})
			# if only one project, add it in the context as default value
			tasks = request.env['project.task'].sudo().search(literal_eval(domain))
			if len(tasks.mapped('project_id')) == 1:
				action['context']['default_project_id'] = tasks.mapped('project_id')[0].id
		elif res_model == 'sale.order':
			action = clean_action(request.env.ref('sale.action_orders').read()[0])
			action['domain'] = domain
			action['context'] = {'create': False, 'edit': False, 'delete': False}  # No CRUD operation when coming from overview
		elif res_model == 'account.invoice':
			account_type = request.env['account.invoice'].sudo().search([])
			for account in account_type:
				print('invoice domain1',action.get(domain))
				if account.type == 'in_invoice':
					action = clean_action(request.env.ref('account.action_vendor_bill_template').read()[0])
					action['domain'] = domain
					action['context'] = {'create': False, 'delete': False}  # only edition of invoice from overview
				elif account.type == 'out_invoice':
					action = clean_action(request.env.ref('account.action_invoice_tree1').read()[0])
					print('invoice domain1',domain)
					action['domain'] = domain
					action['context'] = {'create': False, 'delete': False}
		elif res_model == 'purchase.order':
			action = clean_action(request.env.ref('purchase.purchase_form_action').read()[0])
			action['domain'] = domain
			action['context'] = {'create': False, 'edit': False, 'delete': False}
		return action