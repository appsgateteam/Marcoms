# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import html2plaintext

class EmployeeTimesheet(models.Model):
    _name = "employee.timesheet"
    _inherit = 'mail.thread'
    _rec_name = 'project_id'

    date = fields.Date(string="Date", readonly=True, states={'draft': [('readonly', False)]},track_visibility='always')
    project_id = fields.Many2one('project.project', string="Project", readonly=True, states={'draft': [('readonly', False)]},track_visibility='always')
    task_id = fields.Many2one('project.task', string="Task", readonly=True, states={'draft': [('readonly', False)]},track_visibility='always')
    nn_analytic_id = fields.One2many('account.analytic.line', 'nn_sheet_id', string="Analytic", readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed')],'Status',default="draft")

    @api.multi
    def action_confirm(self):
    	self.write({'state':'confirmed'})

    @api.multi
    def action_draft(self):
    	self.write({'state':'draft'})

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    nn_sheet_id = fields.Many2one('employee.timesheet', string="Timesheet")
    # lab_type = fields.Selection([('labour','Labour')],string='Type',  default='labour', readonly=1)