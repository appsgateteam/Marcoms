# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta , date
from odoo.tools.translate import _


class GeneratePO(models.TransientModel):
    _name = 'generate.po'


    @api.multi
    def Generate_Purchase_order(self):
        
        inv_obj = self.env['purchase.order']
        pur = self.env['purchase.order.line'].browse(self.env.context.get('active_ids'))
        for xc in pur:
            xc.state_id = 'confirm'
        vendor = []
        for l in pur:
            if l.partner_id.id in vendor:
                continue
            else:
                ven = l.partner_id.id
                vendor.append(ven)
        for x in vendor:
            invoice_line = []
            for l in pur:
                if x == l.partner_id.id:
                    tax = []
                    for z in l.taxes_id:
                        tax.append(z.id)
                    invoice_line_vals = {'name':l.name,
                            'partner_id':l.partner_id.id,
                            'product_id':l.product_id.id,
                            'price_unit':l.price_unit,
                            'date_planned':datetime.today(),
                            'product_uom':l.product_uom.id,
                            'requ':l.requ.id,
                            'taxes_id':[(6, 0, tax)],
                            'product_qty':l.product_qty,}
                    invoice_line.append((0, 0, invoice_line_vals))
                    vals = {
                        'partner_id': l.partner_id.id,
                        'requisition_id':l.requ.id,
                        'origin':l.requ.name,
                        'state':'sel',
                        'order_line': invoice_line,
                    }
            inv_obj.create(vals)


class CancelPO(models.TransientModel):
    _name = 'cancel.po'

    @api.multi
    def cancel_Purchase_order(self):
        pur = self.env['purchase.order'].browse(self.env.context.get('active_ids'))
        for l in pur:
            for inv in l.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

            pur.write({'state': 'cancel'})