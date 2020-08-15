from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    equipment_ids = fields.One2many('maintenance.equipment', 'workcenter_id', "Maintenance Equipment")


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    expected_mtbf = fields.Integer(string='Expected MTBF', help='Expected Mean Time Between Failure')
    mtbf = fields.Integer(compute='_compute_maintenance_request', string='MTBF', help='Mean Time Between Failure, computed based on done corrective maintenances.')
    mttr = fields.Integer(compute='_compute_maintenance_request', string='MTTR', help='Mean Time To Repair')
    estimated_next_failure = fields.Date(compute='_compute_maintenance_request', string='Estimated time before next failure (in days)', help='Computed as Latest Failure Date + MTBF')
    latest_failure_date = fields.Date(compute='_compute_maintenance_request', string='Latest Failure Date')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center')

    @api.multi
    def _compute_maintenance_request(self):
        for equipment in self:
            maintenance_requests = equipment.maintenance_ids.filtered(lambda x: x.maintenance_type == 'corrective' and x.stage_id.done)
            mttr_days = 0
            for maintenance in maintenance_requests:
                if maintenance.stage_id.done and maintenance.close_date:
                    mttr_days += (maintenance.close_date - maintenance.request_date).days
            equipment.mttr = len(maintenance_requests) and (mttr_days / len(maintenance_requests)) or 0
            maintenance = maintenance_requests.sorted(lambda x: x.request_date)
            if len(maintenance) >= 1:
                equipment.mtbf = (maintenance[-1].request_date - equipment.effective_date).days / len(maintenance)
            equipment.latest_failure_date = maintenance and maintenance[-1].request_date or False
            if equipment.mtbf:
                equipment.estimated_next_failure = equipment.latest_failure_date + relativedelta(days=equipment.mtbf)
            else:
                equipment.estimated_next_failure = False

    @api.multi
    def button_mrp_workcenter(self):
        self.ensure_one()
        return {
            'name': _('work centers'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.workcenter',
            'view_id': self.env.ref('mrp.mrp_workcenter_view').id,
            'type': 'ir.actions.act_window',
            'res_id': self.workcenter_id.id
        }


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    workorder_id = fields.Many2one('mrp.workorder', string='Work Order')


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Number of maintenance requests")
    request_ids = fields.One2many('maintenance.request', 'production_id')

    @api.multi
    @api.depends('request_ids')
    def _compute_maintenance_count(self):
        for production in self:
            production.maintenance_count = len(production.request_ids)

    @api.multi
    def button_maintenance_req(self):
        self.ensure_one()
        return {
            'name': _('New Maintenance Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'context': {'default_production_id': self.id,},
            'domain': [('production_id', '=', self.id)],
        }

    @api.multi
    def open_maintenance_request_mo(self):
        self.ensure_one()
        action = {
            'name': _('Maintenance Requests'),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form,pivot,graph,calendar',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'context': {'default_production_id': self.id,},
            'domain': [('production_id', '=', self.id)],
        }
        if self.maintenance_count == 1:
            production = self.env['maintenance.request'].search([('production_id', '=', self.id)])
            action['view_mode'] = 'form'
            action['res_id'] = production.id
        return action


class MrpProductionWorkcenterLine(models.Model):
    _inherit = "mrp.workorder"

    @api.multi
    def button_maintenance_req(self):
        self.ensure_one()
        return {
            'name': _('New Maintenance Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'context': {
                'default_workorder_id': self.id,
                'default_production_id': self.production_id.id,
                'discard_on_footer_button': True,
            },
            'target': 'new',
            'domain': [('workorder_id', '=', self.id)]
        }