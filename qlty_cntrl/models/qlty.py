from math import sqrt
from dateutil.relativedelta import relativedelta
from datetime import datetime
import random

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp


class QualityPoint(models.Model):
    _inherit = "quality.point"

    failure_message = fields.Html('Failure Message')
    measure_frequency_type = fields.Selection([
        ('all', 'All Operations'),
        ('random', 'Randomly'),
        ('periodical', 'Periodically')], string="Type of Frequency",
        default='all', required=True)
    measure_frequency_value = fields.Float('Percentage')  # TDE RENAME ?
    measure_frequency_unit_value = fields.Integer('Frequency Unit Value')  # TDE RENAME ?
    measure_frequency_unit = fields.Selection([
        ('day', 'Day(s)'),
        ('week', 'Week(s)'),
        ('month', 'Month(s)')], default="day")  # TDE RENAME ?
    norm = fields.Float('Norm', digits=dp.get_precision('Quality Tests'))  # TDE RENAME ?
    tolerance_min = fields.Float('Min Tolerance', digits=dp.get_precision('Quality Tests'))
    tolerance_max = fields.Float('Max Tolerance', digits=dp.get_precision('Quality Tests'))
    norm_unit = fields.Char('Norm Unit', default=lambda self: 'mm')  # TDE RENAME ?
    average = fields.Float(compute="_compute_standard_deviation_and_average")
    standard_deviation = fields.Float(compute="_compute_standard_deviation_and_average")

    def _compute_standard_deviation_and_average(self):
        # The variance and mean are computed by the Welford’s method and used the Bessel's
        # correction because are working on a sample.
        points = self.filtered(lambda x: x.test_type == 'measure')
        for point in points:
            mean = 0.0
            s = 0.0
            n = 0
            for check in point.check_ids:
                n += 1
                delta = check.measure - mean
                mean += delta / n
                delta2 = check.measure - mean
                s += delta * delta2

            if n > 1:
                point.average = mean
                point.standard_deviation = sqrt( s / ( n - 1))
            elif n == 1:
                point.average = mean
                point.standard_deviation = 0.0
            else:
                point.average = 0.0
                point.standard_deviation = 0.0

    @api.onchange('norm')
    def onchange_norm(self):
        if self.tolerance_max == 0.0:
            self.tolerance_max = self.norm

    @api.multi
    def check_execute_now(self):
        self.ensure_one()
        if self.measure_frequency_type == 'all':
            return True
        elif self.measure_frequency_type == 'random':
            return (random.random() < self.measure_frequency_value / 100.0)
        elif self.measure_frequency_type == 'periodical':
            delta = False
            if self.measure_frequency_unit == 'day':
                delta = relativedelta(days=self.measure_frequency_unit_value)
            elif self.measure_frequency_unit == 'week':
                delta = relativedelta(weeks=self.measure_frequency_unit_value)
            elif self.measure_frequency_unit == 'month':
                delta = relativedelta(months=self.measure_frequency_unit_value)
            date_previous = datetime.today() - delta
            checks = self.env['quality.check'].search([
                ('point_id', '=', self.id),
                ('create_date', '>=', date_previous.strftime(DEFAULT_SERVER_DATETIME_FORMAT))], limit=1)
            return not(bool(checks))
        return super(QualityPoint, self).check_execute_now()

    def _get_type_default_domain(self):
        domain = super(QualityPoint, self)._get_type_default_domain()
        domain.append(('technical_name', '=', 'passfail'))
        return domain

    def action_see_quality_checks(self):
        self.ensure_one()
        action = self.env.ref('qlty_cntrl.quality_check_action_main').read()[0]
        action['domain'] = [('point_id', '=', self.id)]
        action['context'] = {'default_point_id': self.id}
        return action

    @api.multi
    def action_see_spc_control(self):
        self.ensure_one()
        action = self.env.ref('qlty_cntrl.quality_check_action_spc').read()[0]
        if self.test_type == 'measure':
            action['context'] = {'group_by': ['name', 'point_id'], 'graph_measure': ['measure'], 'graph_mode': 'line'}
        action['domain'] = [('point_id', '=', self.id), ('quality_state', '!=', 'none')]
        return action


class QualityAlertTeam(models.Model):
    _inherit = "quality.alert.team"

    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'quality.alert')

    def get_alias_values(self):
        values = super(QualityAlertTeam, self).get_alias_values()
        values['alias_defaults'] = {'team_id': self.id}
        return values


class QualityCheck(models.Model):
    _inherit = "quality.check"

    failure_message = fields.Html(related='point_id.failure_message', readonly=True)
    measure = fields.Float('Measure', default=0.0, digits=dp.get_precision('Quality Tests'), track_visibility='onchange')
    measure_success = fields.Selection([
        ('none', 'No measure'),
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="Measure Success", compute="_compute_measure_success",
        readonly=True, store=True)
    tolerance_min = fields.Float('Min Tolerance', related='point_id.tolerance_min', readonly=True)
    tolerance_max = fields.Float('Max Tolerance', related='point_id.tolerance_max', readonly=True)
    warning_message = fields.Text(compute='_compute_warning_message')
    norm_unit = fields.Char(related='point_id.norm_unit', readonly=True)

    @api.one
    @api.depends('measure_success')
    def _compute_warning_message(self):
        if self.measure_success == 'fail':
            self.warning_message = _('You measured %.2f %s and it should be between %.2f and %.2f %s.') % (
                self.measure, self.norm_unit, self.point_id.tolerance_min,
                self.point_id.tolerance_max, self.norm_unit
            )

    @api.one
    @api.depends('measure')
    def _compute_measure_success(self):
        if self.point_id.test_type == 'passfail':
            self.measure_success = 'none'
        else:
            if self.measure < self.point_id.tolerance_min or self.measure > self.point_id.tolerance_max:
                self.measure_success = 'fail'
            else:
                self.measure_success = 'pass'

    # Add picture dependency
    @api.depends('picture')
    def _compute_result(self):
        super(QualityCheck, self)._compute_result()

    def _get_check_result(self, test_type):
        if test_type == 'picture' and self.picture:
            return _('Picture Uploaded')
        else:
            return super(QualityCheck, self)._get_check_result(test_type)

    def do_measure(self):
        self.ensure_one()
        if self.measure < self.point_id.tolerance_min or self.measure > self.point_id.tolerance_max:
            return {
                'name': _('Quality Check Failed'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.check',
                'view_mode': 'form',
                'view_id': self.env.ref('qlty_cntrl.quality_check_view_form_failure').id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }
        else:
            return self.do_pass()

    def correct_measure(self):
        self.ensure_one()
        return {
            'name': _('Quality Checks'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check',
            'view_mode': 'form',
            'view_id': self.env.ref('qlty_cntrl.quality_check_view_form_small').id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    def do_alert(self):
        self.ensure_one()
        alert = self.env['quality.alert'].create({
            'check_id': self.id,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'lot_id': self.lot_id.id,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'company_id': self.company_id.id
        })
        return {
            'name': _('Quality Alert'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.alert',
            'views': [(self.env.ref('qlty_cntrl.quality_alert_view_form').id, 'form')],
            'res_id': alert.id,
            'context': {'default_check_id': self.id},
        }

    def action_see_alerts(self):
        self.ensure_one()
        if len(self.alert_ids) == 1:
            return {
                'name': _('Quality Alert'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.alert',
                'views': [(self.env.ref('qlty_cntrl.quality_alert_view_form').id, 'form')],
                'res_id': self.alert_ids.ids[0],
                'context': {'default_check_id': self.id},
            }
        else:
            action = self.env.ref('qlty_cntrl.quality_alert_action_check').read()[0]
            action['domain'] = [('id', 'in', self.alert_ids.ids)]
            return action

    @api.multi
    def redirect_after_pass_fail(self):
        check = self[0]
        if check.picking_id:
            checks = self.picking_id.check_ids.filtered(lambda x: x.quality_state == 'none')
            if checks:
                action = self.env.ref('qlty_cntrl.quality_check_action_small').read()[0]
                action['res_id'] = checks.ids[0]
                return action
        return super(QualityCheck, self).redirect_after_pass_fail()


class QualityAlert(models.Model):
    _inherit = "quality.alert"

    title = fields.Char('Title')

    def action_see_check(self):
        return {
            'name': _('Quality Check'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'quality.check',
            'target': 'current',
            'res_id': self.check_id.id,
        }

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages of the ECO type
        in the Kanban view, even if there is no ECO in that stage
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    @api.depends('name', 'title')
    def name_get(self):
        result = []
        for record in self:
            name = record.name + ' - ' + record.title if record.title else record.name
            result.append((record.id, name))
        return result

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Override, used with creation by email alias. The purpose of the override is
        to use the subject for title and body for description instead of the name.
        """
        # We need to add the name in custom_values or it will use the subject.
        custom_values['name'] = self.env['ir.sequence'].next_by_code('quality.alert') or _('New')
        if msg_dict.get('subject'):
            custom_values['title'] = msg_dict['subject']
        if msg_dict.get('body'):
            custom_values['description'] = msg_dict['body']
        return super(QualityAlert, self).message_new(msg_dict, custom_values)
