# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project.project'

    issue_count = fields.Integer(compute='_compute_issue_count', string="Issues")
    issue_ids = fields.One2many('project.issue', 'project_id', string="Issues", domain=['|', ('stage_id.fold', '=', False), ('stage_id', '=', False)])
    issue_needaction_count = fields.Integer(compute="_issue_needaction_count", string="Issues")
    job_order_count = fields.Integer('Job Order', compute='_get_job_order_count')
    purchase_order_line_count = fields.Integer('Purchase Order', compute='_get_purchase_order_line_count')
    purchase_order_count = fields.Integer('Purchase Order',compute='_get_purchase_count')
    project_id = fields.One2many('purchase.order','project_id')
    purchase_id = fields.One2many('purchase.order.line','order_id')

    @api.multi
    def _get_purchase_count(self):
        count = 0.0
        for job_cost_sheet in self:
            project_ids = self.env['job.cost.sheet'].search([('project_id', '=', job_cost_sheet.id)])
            for purchase in project_ids:
                purchase_line_ids = self.env['purchase.order.line'].search([('job_cost_sheet_id', '=', purchase.id)])
                for purchase in purchase_line_ids:
                    purchase_ids = self.env['purchase.order'].search([('id', 'in', purchase.order_id.ids)])
                    count = count + len(purchase_ids)
            job_cost_sheet.purchase_order_count = count
        return True


    @api.multi
    def purchase_order_count_button(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain':  [('id', 'in', self.purchase_id.ids)],
        }


    @api.multi
    def _get_job_order_count(self):
        for order in self:
            order_ids = self.env['job.order'].search([('project_id', '=', order.id)])
            order.job_order_count = len(order_ids)
        return

    @api.multi
    def project_job_order_button(self):
        self.ensure_one()
        return {
            'name': 'Job Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'job.order',
            'domain': [('project_id', '=', self.id)],
        }

    @api.multi
    def _compute_issue_count(self):
        for project_id in self:
            issue_ids = self.env['project.issue'].search([('project_id','=',project_id.id)])
            count = len(issue_ids)
            project_id.issue_count = count
        return
    
    @api.multi
    def button_view_issue(self):
        issue = {}
        issue_obj = self.env['project.issue']
        issue_ids = issue_obj.search([('project_id','=',self.id)])
        total_issue = []
        for issue_id in issue_ids:
            total_issue.append(issue_id.id)
        if total_issue:
            project_project = self.env['ir.actions.act_window'].for_xml_id('bi_odoo_job_costing_management', 'project_issue_categ_act0')
            project_project['domain'] = [('id', 'in', total_issue)]
        return project_project
        
    @api.model
    def _get_alias_models(self):
        res = super(Project, self)._get_alias_models()
        res.append(("project.issue", "Issues"))
        return res

    def _issue_needaction_count(self):
        issue_data = self.env['project.issue'].read_group([('project_id', 'in', self.ids), ('message_needaction', '=', True)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in issue_data)
        for project in self:
            project.issue_needaction_count = int(result.get(project.id, 0))

    @api.multi
    def write(self, vals):
        res = super(Project, self).write(vals)
        if 'active' in vals:
            # archiving/unarchiving a project does it on its issues, too
            issues = self.with_context(active_test=False).mapped('issue_ids')
            issues.write({'active': vals['active']})
        return res
