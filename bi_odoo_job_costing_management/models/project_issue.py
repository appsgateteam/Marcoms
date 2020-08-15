# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
import datetime
import pytz

from datetime import timedelta
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.safe_eval import safe_eval
from dateutil import rrule
from operator import itemgetter
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare


import logging
_logger = logging.getLogger(__name__)

class ProjectIssue(models.Model):

    _name = "project.issue"
    _description = "Project Issue"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    def update_date_end(self, stage_id):
        project_task_type = self.env['project.task.type'].browse(stage_id)
        if project_task_type.fold:
            return {'date_closed': fields.Datetime.now()}
        return {'date_closed': False}
    
    @api.model
    def create(self, vals):
        context = dict(self.env.context, mail_create_nolog=True)

        if vals.get('project_id') and not context.get('default_project_id'):
            context['default_project_id'] = vals.get('project_id')
        if vals.get('user_id') and not vals.get('date_open'):
            vals['date_open'] = fields.Datetime.now()
        if vals.get('stage_id'):
            vals.update(self.update_date_end(vals['stage_id']))
        task = super(ProjectIssue, self.with_context(context)).create(vals)
        return task
        
    @api.multi
    def write(self, vals):
        now = fields.Datetime.now()
        if 'stage_id' in vals:
            vals.update(self.update_date_end(vals['stage_id']))
            vals['date_last_stage_update'] = now
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
        if vals.get('user_id') and 'date_open' not in vals:
            vals['date_open'] = now

        result = super(ProjectIssue, self).write(vals)

        return result
        
    @api.multi
    def _active_support_project(self):
        for s_id in self:
            support_ids = self.env['project.task'].search([('support_id','=',s_id.id)])
            count = len(support_ids)
            s_id.task_count = count
        return
        
    @api.multi
    def task(self):
        project = {}
        task_obj = self.env['project.task']
        support_ids = task_obj.search([('support_id','=',self.id)])
        project1 = []
        for support_id in support_ids:
            project1.append(support_id.id)
        if support_ids:
            project = self.env['ir.actions.act_window'].for_xml_id('project', 'action_view_task')
            project['domain'] = [('id', 'in', project1)]
        return project
        
    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False)])
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        if 'default_project_id' in self.env.context:
            search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    
    def stage_find(self, section_id, domain=[], order='sequence'):
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        section_ids.extend(self.mapped('project_id').ids)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('project_ids', '=', section_id))
        search_domain += list(domain)
        return self.env['project.task.type'].search(search_domain, order=order, limit=1).id
    
    @api.multi
    @api.depends('create_date', 'date_action_last', 'date_last_stage_update')
    def _compute_inactivity_days(self):
        current_datetime = fields.Datetime.from_string(fields.Datetime.now())
        for issue in self:
            dt_create_date = fields.Datetime.from_string(issue.create_date) or current_datetime
            issue.days_since_creation = (current_datetime - dt_create_date).days

            if issue.date_action_last:
                issue.inactivity_days = (current_datetime - fields.Datetime.from_string(issue.date_action_last)).days
            elif issue.date_last_stage_update:
                issue.inactivity_days = (current_datetime - fields.Datetime.from_string(issue.date_last_stage_update)).days
            else:
                issue.inactivity_days = (current_datetime - dt_create_date).days
                
    @api.multi
    @api.depends('create_date', 'date_closed', 'date_open')
    def _compute_day(self):
        for issue in self:
            # if the working hours on the project are not defined, use default ones (8 -> 12 and 13 -> 17 * 5)
            calendar = issue.project_id.resource_calendar_id

            dt_create_date = fields.Datetime.from_string(issue.create_date)
            if issue.date_open:
                dt_date_open = fields.Datetime.from_string(issue.date_open)
                issue.day_open = (dt_date_open - dt_create_date).total_seconds() / (24.0 * 3600)
                issue.working_hours_open = calendar.get_working_hours(dt_create_date, dt_date_open,
                    compute_leaves=True, resource_id=False, default_interval=(8, 16))

            if issue.date_closed:
                dt_date_closed = fields.Datetime.from_string(issue.date_closed)
                issue.day_close = (dt_date_closed - dt_create_date).total_seconds() / (24.0 * 3600)
                issue.working_hours_close = calendar.get_working_hours(dt_create_date, dt_date_closed,
                    compute_leaves=True, resource_id=False, default_interval=(8, 16))
                
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        self.email_from = self.partner_id.email
        
    @api.onchange('project_id')
    def _onchange_project(self):
        default_partner_id = self.env.context.get('default_partner_id')
        default_partner = self.env['res.partner'].browse(default_partner_id) if default_partner_id else self.env['res.partner']
        if self.project_id:
            self.partner_id = self.project_id.partner_id or default_partner
            if self.project_id not in self.stage_id.project_ids:
                self.stage_id = self.stage_find(self.project_id.id, [('fold', '=', False)])
        else:
            self.partner_id = default_partner
            self.stage_id = False

    @api.onchange('task_id')
    def _onchange_task_id(self):
        self.user_id = self.task_id.user_id  
                          
    '''@api.multi
    def create_task(self):
        project_task_obj  = self.env['project.task']
        vals = {
                'name' : self.name,
                'project_id' : self.project_id.id,
                'user_id' : self.user_id.id,
                'tag_ids' : self.tag_ids,
                'support_id' : self.id,
                'description' : self.description,
                }
        project_task = project_task_obj.create(vals)
        return project_task'''
    
                                
    partner_id = fields.Many2one('res.partner', string="Customer")
    id = fields.Integer('ID', readonly=True)
    email_from = fields.Char('Email', size=128, help="Destination email for email gateway.")
    name = fields.Char('Issue', required=True)
    description = fields.Text('Description')
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority', default='0')
    stage_id = fields.Many2one('project.task.type', string='Stage', track_visibility='onchange', index=True,
        default=_get_default_stage_id, group_expand='_read_group_stage_ids',
        domain="[('project_ids', '=', project_id)]", copy=False)
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid)
    tag_ids = fields.Many2many('project.tags', string='Tags')
    date_create = fields.Datetime(string="Create Date",default=fields.datetime.now())
    task_id = fields.Many2one('project.task', string='Task', domain="[('project_id','=',project_id)]")
    task_count =  fields.Integer(compute='_active_support_project',string="Tasks") 
    timesheet_ids = fields.One2many('account.analytic.line', 'support_id', 'Timesheets')
    project_id = fields.Many2one('project.project',
        string='Project',
        default=lambda self: self.env.context.get('default_project_id'),
        index=True,
        track_visibility='onchange',
        change_default=True)
    analytic_id = fields.Many2one('account.analytic.account',string="Analytic Account")
    # customer_rating = fields.Selection([('1','Poor'), ('2','Average'), ('3','Good'),('4','Excellent')], 'Customer Rating')
    # comment = fields.Text(string="Comment")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    active = fields.Boolean(default=True)
    days_since_creation = fields.Integer(compute='_compute_inactivity_days', string='Days since creation date',
                                         help="Difference in days between creation date and current date")
    kanban_state = fields.Selection([('normal', 'Normal'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')], string='Kanban State',
                                    track_visibility='onchange', required=True, default='normal',
                                    help="""An Issue's kanban state indicates special situations affecting it:\n
                                           * Normal is the default situation\n
                                           * Blocked indicates something is preventing the progress of this issue\n
                                           * Ready for next stage indicates the issue is ready to be pulled to the next stage""")
    email_cc = fields.Char(string='Watchers Emails', help="""These email addresses will be added to the CC field of all inbound
        and outbound emails for this record before being sent. Separate multiple email addresses with a comma""")
    date_last_stage_update = fields.Datetime(string='Last Stage Update', index=True, default=fields.Datetime.now)
    duration = fields.Float('Duration')
    day_open = fields.Float(compute='_compute_day', string='Days to Assign', store=True)
    day_close = fields.Float(compute='_compute_day', string='Days to Close', store=True)
    working_hours_open = fields.Float(compute='_compute_day', string='Working Hours to assign the Issue', store=True)
    working_hours_close = fields.Float(compute='_compute_day', string='Working Hours to close the Issue', store=True)
    inactivity_days = fields.Integer(compute='_compute_inactivity_days', string='Days since last action',
                                     help="Difference in days between last action and current date")
    color = fields.Integer('Color Index')
    date_action_last = fields.Datetime(string='Last Action', readonly=True)
    date_action_next = fields.Datetime(string='Next Action', readonly=True)
    date_open = fields.Datetime(string='Assigned', readonly=True, index=True)
    date_closed = fields.Datetime(string='Closed', readonly=True, index=True)
    date = fields.Datetime('Date')
    user_email = fields.Char(related='user_id.email', string='User Email', readonly=True)
    

    @api.multi
    def _track_template(self, tracking):
        self.ensure_one()
        res = super(ProjectIssue, self)._track_template(tracking)
        changes, dummy = tracking[self.id]
        if 'stage_id' in changes and self.stage_id.mail_template_id:
            res['stage_id'] = (self.stage_id.mail_template_id, {'composition_mode': 'mass_mail'})
        return res

    @api.multi
    def _notification_recipients(self, message, groups):
        groups = super(ProjectIssue, self)._notification_recipients(message, groups)

        self.ensure_one()
        if not self.user_id:
            take_action = self._notification_link_helper('assign')
            project_actions = [{'url': take_action, 'title': _('I take it')}]
        else:
            new_action_id = self.env.ref('bi_odoo_job_costing_management.project_issue_categ_act0').id
            new_action = self._notification_link_helper('new', action_id=new_action_id)
            project_actions = [{'url': new_action, 'title': _('New Issue')}]

        new_group = (
            'group_project_user', lambda partner: bool(partner.user_ids) and any(user.has_group('project.group_project_user') for user in partner.user_ids), {
                'actions': project_actions,
            })

        return [new_group] + groups

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project. """
        issues = self.browse(res_ids)
        project_ids = set(issues.mapped('project_id').ids)
        aliases = self.env['project.project'].message_get_reply_to(list(project_ids), default=default)
        return dict((issue.id, aliases.get(issue.project_id and issue.project_id.id or 0, False)) for issue in issues)

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(ProjectIssue, self).message_get_suggested_recipients()
        try:
            for issue in self:
                if issue.partner_id:
                    issue._message_add_suggested_recipient(recipients, partner=issue.partner_id, reason=_('Customer'))
                elif issue.email_from:
                    issue._message_add_suggested_recipient(recipients, email=issue.email_from, reason=_('Customer Email'))
        except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
            pass
        return recipients

    @api.multi
    def email_split(self, msg):
        email_list = tools.email_split((msg.get('to') or '') + ',' + (msg.get('cc') or ''))
        # check left-part is not already an alias
        return filter(lambda x: x.split('@')[0] not in self.mapped('project_id.alias_name'), email_list)

    @api.model
    def message_new(self, msg, custom_values=None):
        create_context = dict(self.env.context or {})
        create_context['default_user_id'] = False
        defaults = {
            'name':  msg.get('subject') or _("No Subject"),
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'partner_id': msg.get('author_id', False),
        }
        if custom_values:
            defaults.update(custom_values)

        res_id = super(ProjectIssue, self.with_context(create_context)).message_new(msg, custom_values=defaults)
        issue = self.browse(res_id)
        email_list = issue.email_split(msg)
        partner_ids = filter(None, issue._find_partner_from_emails(email_list))
        issue.message_subscribe(partner_ids)
        return res_id

    @api.multi
    def message_update(self, msg, update_vals=None):
        email_list = self.email_split(msg)
        partner_ids = filter(None, self._find_partner_from_emails(email_list))
        self.message_subscribe(partner_ids)
        return super(ProjectIssue, self).message_update(msg, update_vals=update_vals)

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, subtype=None, **kwargs):
        self.ensure_one()
        mail_message = super(ProjectIssue, self).message_post(subtype=subtype, **kwargs)
        if subtype:
            self.sudo().write({'date_action_last': fields.Datetime.now()})
        return mail_message

    @api.multi
    def message_get_email_values(self, notif_mail=None):
        self.ensure_one()
        res = super(ProjectIssue, self).message_get_email_values(notif_mail=notif_mail)
        headers = {}
        if res.get('headers'):
            try:
                headers.update(safe_eval(res['headers']))
            except Exception:
                pass
        if self.project_id:
            current_objects = filter(None, headers.get('X-Odoo-Objects', '').split(','))
            current_objects.insert(0, 'project.project-%s, ' % self.project_id.id)
            headers['X-Odoo-Objects'] = ','.join(current_objects)
        if self.tag_ids:
            headers['X-Odoo-Tags'] = ','.join(self.tag_ids.mapped('name'))
        res['headers'] = repr(headers)
        return res

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    support_id = fields.Many2one('project.issue','Project Issue')
    
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    support_id = fields.Many2one('project.issue',
        string='Project Issue',track_visibility='onchange',change_default=True)
        
class projec_issue_type(models.Model):
    _name='project.issue.type'

    name  =  fields.Char('Project Issue Name')

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"
    
    @api.multi
    def get_attendances_for_weekday(self, day_dt):
        self.ensure_one()
        weekday = day_dt.weekday()
        attendances = self.env['resource.calendar.attendance']

        for attendance in self.attendance_ids.filtered(
            lambda att:
                int(att.dayofweek) == weekday and
                not (att.date_from and fields.Date.from_string(att.date_from) > day_dt.date()) and
                not (att.date_to and fields.Date.from_string(att.date_to) < day_dt.date())):
            attendances |= attendance
        return attendances
    
    def interval_clean(self, intervals):
        intervals = sorted(intervals, key=itemgetter(0))  # sort on first datetime
        cleaned = []
        working_interval = None
        while intervals:
            current_interval = intervals.pop(0)
            if not working_interval:  # init
                working_interval = [current_interval[0], current_interval[1]]
            elif working_interval[1] < current_interval[0]:  # interval is disjoint
                cleaned.append(tuple(working_interval))
                working_interval = [current_interval[0], current_interval[1]]
            elif working_interval[1] < current_interval[1]:  # union of greater intervals
                working_interval[1] = current_interval[1]
        if working_interval:  # handle void lists
            cleaned.append(tuple(working_interval))
        return cleaned
    
    @api.model
    def interval_remove_leaves(self, interval, leave_intervals):
        if not interval:
            return interval
        if leave_intervals is None:
            leave_intervals = []
        intervals = []
        leave_intervals = self.interval_clean(leave_intervals)
        current_interval = [interval[0], interval[1]]
        for leave in leave_intervals:
            if leave[1] <= current_interval[0]:
                continue
            if leave[0] >= current_interval[1]:
                break
            if current_interval[0] < leave[0] < current_interval[1]:
                current_interval[1] = leave[0]
                intervals.append((current_interval[0], current_interval[1]))
                current_interval = [leave[1], interval[1]]
            if current_interval[0] <= leave[1]:
                current_interval[0] = leave[1]
        if current_interval and current_interval[0] < interval[1]:  # remove intervals moved outside base interval due to leaves
            intervals.append((current_interval[0], current_interval[1]))
        return intervals
    
    @api.multi
    def get_leave_intervals(self, resource_id=None,
                            start_datetime=None, end_datetime=None):
        self.ensure_one()
        leaves = []
        for leave in self.leave_ids:
            if leave.resource_id and not resource_id == leave.resource_id.id:
                continue
            date_from = fields.Datetime.from_string(leave.date_from)
            if end_datetime and date_from > end_datetime:
                continue
            date_to = fields.Datetime.from_string(leave.date_to)
            if start_datetime and date_to < start_datetime:
                continue
            leaves.append((date_from, date_to))
        return leaves
    
    @api.multi
    def get_working_intervals_of_day(self, start_dt=None, end_dt=None,
                                     leaves=None, compute_leaves=False, resource_id=None,
                                     default_interval=None):
        # Computes start_dt, end_dt (with default values if not set) + off-interval work limits
        work_limits = []
        if start_dt is None and end_dt is not None:
            start_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif start_dt is None:
            start_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            work_limits.append((start_dt.replace(hour=0, minute=0, second=0, microsecond=0), start_dt))
        if end_dt is None:
            end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            work_limits.append((end_dt, end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)))
        assert start_dt.date() == end_dt.date(), 'get_working_intervals_of_day is restricted to one day'

        intervals = []
        work_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # no calendar: try to use the default_interval, then return directly
        if not self:
            working_interval = []
            if default_interval:
                working_interval = (start_dt.replace(hour=default_interval[0], minute=0, second=0, microsecond=0),
                                    start_dt.replace(hour=default_interval[1], minute=0, second=0, microsecond=0))
            intervals = self.interval_remove_leaves(working_interval, work_limits)
            return intervals

        working_intervals = []
        tz_info = fields.Datetime.context_timestamp(self, work_dt).tzinfo
        for calendar_working_day in self.get_attendances_for_weekday(start_dt):
            dt_f = work_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=(calendar_working_day.hour_from * 3600))
            dt_t = work_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=(calendar_working_day.hour_to * 3600))

            # adapt tz
            working_interval = (
                dt_f.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(tzinfo=None),
                dt_t.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(tzinfo=None),
                calendar_working_day.id
            )
            working_intervals += self.interval_remove_leaves(working_interval, work_limits)

        # find leave intervals
        if leaves is None and compute_leaves:
            leaves = self.get_leave_intervals(resource_id=resource_id)

        # filter according to leaves
        for interval in working_intervals:
            work_intervals = self.interval_remove_leaves(interval, leaves)
            intervals += work_intervals

        return intervals
    
    @api.multi
    def get_working_hours_of_date(self, start_dt=None, end_dt=None,
                                  leaves=None, compute_leaves=False, resource_id=None,
                                  default_interval=None):
        res = timedelta()
        intervals = self.get_working_intervals_of_day(
            start_dt, end_dt, leaves,
            compute_leaves, resource_id,
            default_interval)
        for interval in intervals:
            res += interval[1] - interval[0]
        return res.total_seconds() / 3600.0
    
    
    @api.multi
    def get_weekdays(self, default_weekdays=None):
        if not self:
            return default_weekdays if default_weekdays is not None else [0, 1, 2, 3, 4]
        self.ensure_one()
        weekdays = set(map(int, (self.attendance_ids.mapped('dayofweek'))))
        return list(weekdays)
    
    @api.multi
    def get_working_hours(self, start_dt, end_dt, compute_leaves=False,
                          resource_id=None, default_interval=None):
        hours = 0.0
        for day in rrule.rrule(rrule.DAILY, dtstart=start_dt,
                               until=(end_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                               byweekday=self.get_weekdays()):
            day_start_dt = day.replace(hour=0, minute=0, second=0, microsecond=0)
            if start_dt and day.date() == start_dt.date():
                day_start_dt = start_dt
            day_end_dt = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            if end_dt and day.date() == end_dt.date():
                day_end_dt = end_dt
            hours += self.get_working_hours_of_date(
                start_dt=day_start_dt, end_dt=day_end_dt,
                compute_leaves=compute_leaves, resource_id=resource_id,
                default_interval=default_interval)
        return hours
    
class task_wizard(models.TransientModel):
    _name= 'task.wizard'

    #task_lines = fields.One2many('project.task','task_wiz_id',string="Task Line")
    name = fields.Char('Task Name')
    project_id = fields.Many2one('project.project','Project')
    user_id = fields.Many2one('res.users','Assigned To')
    planned_hours = fields.Float('Planned Hours')
    description = fields.Text('Description')

    @api.model 
    def default_get(self, flds): 
        result = super(task_wizard, self).default_get(flds)
        issue_id = self.env['project.issue'].browse(self._context.get('active_id'))
        result['name'] = issue_id.name
        result['description'] = issue_id.description
        result['project_id'] = issue_id.project_id.id
        result['user_id'] = issue_id.user_id.id
        return result
    
    @api.multi
    def create_task(self):
        project_issue_id = self.env['project.issue'].browse(self._context.get('active_id'))
        list_of_tag = []
        project_task_obj  = self.env['project.task']
        for tag in project_issue_id.tag_ids:
            list_of_tag.append(tag.id)
        vals = {
                'name' : self.name,
                'project_id' : self.project_id.id,
                'user_id' : self.user_id.id,
                'tag_ids' : [(6,0,list_of_tag)],
                'support_id' : project_issue_id.id,
                'description' : self.description,
                'planned_hours' : self.planned_hours
                }
        project_task = project_task_obj.create(vals)
        return project_task
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
