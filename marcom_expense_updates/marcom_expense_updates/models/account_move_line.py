# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_compare


class FoodAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    food_expense_id  = fields.Many2one('food.expense', string='Expense', copy=False, help="Expense where the move line come from")

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(FoodAccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['food.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res



class TransportaionAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    transportaion_expense_id = fields.Many2one('transportaion.expense', string='Expense', copy=False, help="Expense where the move line come from")

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(TransportaionAccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['transportaion.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res



class PettyCashAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pettycash_expense_id = fields.Many2one('petty.cash.expense', string='Expense', copy=False, help="Expense where the move line come from")

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(PettyCashAccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['petty.cash.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res



class LabourAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    labour_expense_id = fields.Many2one('labour.expense', string='Expense', copy=False, help="Expense where the move line come from")

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(LabourAccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['labour.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res

