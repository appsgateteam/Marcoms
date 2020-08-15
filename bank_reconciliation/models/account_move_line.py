# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bank_statement_id = fields.Many2one('bank.statement', 'Bank Statement', copy=False)
    statement_date = fields.Date('Bank.St Date', copy=False)

    # @api.multi
    # def write(self, vals):
    #     if self.bank_statement_id.recnl_type == 'unreconcile':
    #         vals.update({"reconciled": False})
    #         for record in self:
    #             if record.payment_id and record.payment_id.state == 'reconciled':
    #                 record.payment_id.state = 'posted'
    #     elif self.bank_statement_id.recnl_type == 'reconcile':
    #         vals.update({"reconciled": True})
    #         for record in self:
    #             if record.payment_id:
    #                 record.payment_id.state = 'reconciled'
    #     res = super(AccountMoveLine, self).write(vals)
    #     return res
