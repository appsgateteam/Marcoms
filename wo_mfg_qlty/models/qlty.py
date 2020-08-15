from odoo import models, _


class QualityCheck(models.Model):
    _inherit = "quality.check"

    def _get_check_result(self, test_type):
        if test_type == 'passfail':
            return _('Success') if self.quality_state == 'pass' else _('Failure')
        elif test_type == 'measure':
            return '{} {}'.format(self.measure, self.norm_unit)
        return super(QualityCheck, self)._get_check_result(test_type)

    def redirect_after_pass_fail(self):
        self.ensure_one()
        checks = False
        if self.production_id and not self.workorder_id:
            checks = self.production_id.check_ids.filtered(lambda x: x.quality_state == 'none')
        if self.workorder_id:
            checks = self.workorder_id.check_ids.filtered(lambda x: x.quality_state == 'none')
        if checks:
            action = self.env.ref('qlty_cntrl.quality_check_action_small').read()[0]
            action['res_id'] = checks.ids[0]
            return action
        else:
            return super(QualityCheck, self).redirect_after_pass_fail()
