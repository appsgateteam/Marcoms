from odoo import fields, models, _
from odoo.exceptions import UserError


class MrpProductionWorkcenterLine(models.Model):
    _inherit = "mrp.workorder"

    measure = fields.Float(related='current_quality_check_id.measure', store=True, readonly=False)
    measure_success = fields.Selection(related='current_quality_check_id.measure_success', store=True, readonly=False)
    norm_unit = fields.Char(related='current_quality_check_id.norm_unit', store=True, readonly=False)

    def do_pass(self):
        self.ensure_one()
        return self._next('pass')

    def do_fail(self):
        self.ensure_one()
        return self._next('fail')

    def do_measure(self):
        self.ensure_one()
        point_id = self.current_quality_check_id.point_id
        if self.measure < point_id.tolerance_min or self.measure > point_id.tolerance_max:
            return self.do_fail()
        else:
            return self.do_pass()

    def _next(self, state='pass'):
        self.ensure_one()
        old_check_id = self.current_quality_check_id
        result = super(MrpProductionWorkcenterLine, self)._next(state)
        if state == 'fail' and old_check_id.failure_message:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'quality.check',
                'views': [[self.env.ref('qlty_cntrl.quality_check_failure_message').id, 'form']],
                'name': _('Failure Message'),
                'target': 'new',
                'res_id': old_check_id.id,
            }
        return result

    def button_quality_alert(self):
        self.ensure_one()
        action = self.env.ref('qlty_cntrl.quality_alert_action_check').read()[0]
        action['target'] = 'new'
        action['views'] = [(False, 'form')]
        action['context'] = {
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_workorder_id': self.id,
            'default_production_id': self.production_id.id,
            'default_workcenter_id': self.workcenter_id.id,
            'discard_on_footer_button': True,
        }
        return action