# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    invoiced_qty = fields.Float('Invoiced Quantity', readonly=True)
    qty_to_invoice = fields.Float('Qty to be Invoiced', readonly=True)

    def _select(self):
        result = super(PurchaseReport, self)._select()
        select_str = result + """,l.qty_invoiced as invoiced_qty,SUM(l.product_qty - l.qty_invoiced) as qty_to_invoice    
    						"""
        return select_str

    def _group_by(self):
        result = super(PurchaseReport, self)._group_by()
        group_by_str = result + """,l.qty_invoiced
    							"""
        return group_by_str
