from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

from odoo import api, fields, models, tools


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    date_planned_start_wo = fields.Datetime(
        'Scheduled Start Date', compute='_compute_date_planned',
        copy=False, store=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    date_planned_finished_wo = fields.Datetime(
        'Scheduled End Date', compute='_compute_date_planned',
        copy=False, store=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    check_ids = fields.One2many('quality.check', 'production_id', string="Checks")

    @api.multi
    @api.depends('workorder_ids.date_planned_start', 'workorder_ids.date_planned_finished')
    def _compute_date_planned(self):
        for order in self:
            date_planned_start_wo = date_planned_finished_wo = False
            if order.workorder_ids:
                start_dates = order.workorder_ids.filtered(lambda r: r.date_planned_start is not False).sorted(key=lambda r: r.date_planned_start)
                date_planned_start_wo = start_dates[0].date_planned_start if start_dates else False
                finished_dates = order.workorder_ids.filtered(lambda r: r.date_planned_finished is not False).sorted(key=lambda r: r.date_planned_finished)
                date_planned_finished_wo = finished_dates[-1].date_planned_finished if finished_dates else False
            order.date_planned_start_wo = date_planned_start_wo
            order.date_planned_finished_wo = date_planned_finished_wo

    def _get_start_date(self):
        return datetime.now()

    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        WorkOrder = self.env['mrp.workorder']
        ProductUom = self.env['uom.uom']
        for order in self.filtered(lambda x: x.state == 'planned'):
            order.workorder_ids.write({'date_planned_start': False, 'date_planned_finished': False})

        # Schedule all work orders (new ones and those already created)
        for order in self:
            if not order.workorder_ids.mapped('check_ids'):
                order.workorder_ids._create_checks()
            start_date = order._get_start_date()
            from_date_set = False
            for workorder in order.workorder_ids:
                workcenter = workorder.workcenter_id
                wos = WorkOrder.search([('workcenter_id', '=', workcenter.id), ('date_planned_finished', '<>', False),
                                        ('state', 'in', ('ready', 'pending', 'progress')),
                                        ('date_planned_finished', '>=', start_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT))], order='date_planned_start')
                from_date = start_date
                to_date = workcenter.resource_calendar_id.attendance_ids and workcenter.resource_calendar_id.plan_hours(workorder.duration_expected / 60.0, from_date, compute_leaves=True, resource=workcenter.resource_id)
                if to_date:
                    if not from_date_set:
                        # planning 0 hours gives the start of the next attendance
                        from_date = workcenter.resource_calendar_id.plan_hours(0, from_date, compute_leaves=True, resource=workcenter.resource_id)
                        from_date_set = True
                else:
                    to_date = from_date + relativedelta(minutes=workorder.duration_expected)
                # Check interval
                for wo in wos:
                    if from_date < fields.Datetime.from_string(wo.date_planned_finished) and (to_date > fields.Datetime.from_string(wo.date_planned_start)):
                        from_date = fields.Datetime.from_string(wo.date_planned_finished)
                        to_date = workcenter.resource_calendar_id.attendance_ids and workcenter.resource_calendar_id.plan_hours(workorder.duration_expected / 60.0, from_date, compute_leaves=True, resource=workcenter.resource_id)
                        if not to_date:
                            to_date = from_date + relativedelta(minutes=workorder.duration_expected)
                workorder.write({'date_planned_start': from_date, 'date_planned_finished': to_date})

                if (workorder.operation_id.batch == 'no') or (workorder.operation_id.batch_size >= workorder.qty_production):
                    start_date = to_date
                else:
                    qty = min(workorder.operation_id.batch_size, workorder.qty_production)
                    cycle_number = math.ceil(qty / workorder.production_id.product_qty / workcenter.capacity)
                    duration = workcenter.time_start + cycle_number * workorder.operation_id.time_cycle * 100.0 / workcenter.time_efficiency
                    to_date = workcenter.resource_calendar_id.attendance_ids and workcenter.resource_calendar_id.plan_hours(duration / 60.0, from_date, compute_leaves=True, resource=workcenter.resource_id)
                    if not to_date:
                        start_date = from_date + relativedelta(minutes=duration)
        return res

    def button_unplan(self):
        self.mapped('workorder_ids').write({'date_planned_start': False, 'date_planned_finished': False})
