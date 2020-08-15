# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ADDQTYpurchase(models.TransientModel):
    _name = 'add.qty.purchase'

    qty = fields.Integer('Qty')

    @api.multi
    def action_add_qty(self):
        pur = self.env['purchase.order.line'].browse(self.env.context.get('active_ids'))
        pur.write({'product_qty': self.qty})

    @api.multi
    def next_stage_6(self):
        pur = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        pur.write({'stage_id': 8})