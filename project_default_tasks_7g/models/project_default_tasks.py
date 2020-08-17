from datetime import timedelta, date
from odoo import api, fields, models


class ProjectDefaultTasks(models.Model):
    _name = 'project.default_tasks'

    name = fields.Char(string='Task Title', track_visibility='always', required=True)
    description = fields.Html(string='Description')
    sequence = fields.Integer(string='Sequence', default=10,
                              help='Gives the sequence order when displaying a list of tasks.')
    # FIXME stage looks as unknown after save and empty on tree view
    stage_id = fields.Many2one('project.task.type', string='Stage')
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid)
    tag_ids = fields.Many2many('project.tags', string='Tags')
    date_deadline = fields.Integer(string='Deadline')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


class ProjectDefaults(models.Model):
    _inherit = 'project.project'

    use_default_tasks = fields.Boolean(default=False)

    @api.model
    def get_task_values(self, default_task, project_id):
        deadline = default_task.date_deadline > 0 and date.today() + timedelta(days=default_task.date_deadline) or None
        return {
            'name': default_task.name,
            'description': default_task.description,
            'sequence': default_task.sequence,
            'tag_ids': [(6, 0, [x.id for x in default_task.tag_ids])],
            'stage_id': default_task.stage_id.id,
            'user_id': default_task.user_id.id,
            'date_deadline': fields.Date.to_string(deadline),
            'project_id': project_id.id if project_id else False,
            'partner_id': project_id.partner_id.id if project_id else False,
        }

    @api.model
    def create_default_tasks(self, project_id=None):
        default_tasks = self.env['project.default_tasks'].search([
            ('active', '=', True), '|', ('company_id', '=', False), ('company_id.id', '=', self.env.user.company_id.id)
        ])
        task_obj = self.env['project.task']
        for task in default_tasks:
            task_vals = self.get_task_values(task, project_id)
            task_id = task_obj.create(task_vals)
        return True

    @api.model
    def create(self, vals):
        project_id = super(ProjectDefaults, self).create(vals)
        if vals.get('use_default_tasks'):
            self.create_default_tasks(project_id=project_id)
        return project_id
