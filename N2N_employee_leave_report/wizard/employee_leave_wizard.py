# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EmployeeLeaveReport(models.TransientModel):
	_name = 'employee.leave.report'
	_description = 'employee leave report'

	date = fields.Date('Leave Date')
	employee_id = fields.Many2one('hr.employee', string="Employee")

	@api.multi
	def generate(self):
		domain_filter = []
		if self.employee_id:
			domain_filter.append(('employee_id','=',self.employee_id.id))
		action = self.env.ref('N2N_employee_leave_report.action_leave_report_analysis')
		result = action.read()[0]
		result['domain'] = str(domain_filter)
		return result
		

