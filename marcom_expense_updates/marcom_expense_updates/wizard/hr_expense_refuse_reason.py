# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FoodExpenseRefuseWizard(models.TransientModel):
    """This wizard can be launched from an he.expense (an expense line)
    or from an hr.expense.sheet (En expense report)
    'hr_expense_refuse_model' must be passed in the context to differentiate
    the right model to use.
    """

    _name = "food.expense.refuse.wizard"
    _description = "Expense Refuse Reason Wizard"

    reason = fields.Char(string='Reason', required=True)
    hr_expense_ids = fields.Many2many('food.expense')
    hr_expense_sheet_id = fields.Many2one('food.expense.sheet')

    @api.model
    def default_get(self, fields):
        res = super(FoodExpenseRefuseWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        refuse_model = self.env.context.get('hr_expense_refuse_model')
        if refuse_model == 'food.expense':
            res.update({
                'hr_expense_ids': active_ids,
                'hr_expense_sheet_id': False,
            })
        elif refuse_model == 'food.expense.sheet':
            res.update({
                'hr_expense_sheet_id': active_ids[0] if active_ids else False,
                'hr_expense_ids': [],
            })
        return res

    @api.multi
    def expense_refuse_reason(self):
        self.ensure_one()
        if self.hr_expense_ids:
            self.hr_expense_ids.refuse_expense(self.reason)
        if self.hr_expense_sheet_id:
            self.hr_expense_sheet_id.refuse_sheet(self.reason)

        return {'type': 'ir.actions.act_window_close'}

#-----------------------------------------------------------------------------------------------------------------
# transportaion start
class TransportaionExpenseRefuseWizard(models.TransientModel):
    """This wizard can be launched from an he.expense (an expense line)
    or from an hr.expense.sheet (En expense report)
    'hr_expense_refuse_model' must be passed in the context to differentiate
    the right model to use.
    """

    _name = "transportaion.expense.refuse.wizard"
    _description = "Expense Refuse Reason Wizard"

    reason = fields.Char(string='Reason', required=True)
    hr_expense_ids = fields.Many2many('transportaion.expense')
    hr_expense_sheet_id = fields.Many2one('transportaion.expense.sheet')

    @api.model
    def default_get(self, fields):
        res = super(TransportaionExpenseRefuseWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        refuse_model = self.env.context.get('hr_expense_refuse_model')
        if refuse_model == 'transportaion.expense':
            res.update({
                'hr_expense_ids': active_ids,
                'hr_expense_sheet_id': False,
            })
        elif refuse_model == 'transportaion.expense.sheet':
            res.update({
                'hr_expense_sheet_id': active_ids[0] if active_ids else False,
                'hr_expense_ids': [],
            })
        return res

    @api.multi
    def expense_refuse_reason(self):
        self.ensure_one()
        if self.hr_expense_ids:
            self.hr_expense_ids.refuse_expense(self.reason)
        if self.hr_expense_sheet_id:
            self.hr_expense_sheet_id.refuse_sheet(self.reason)

        return {'type': 'ir.actions.act_window_close'}

# transportaion end
#-----------------------------------------------------------------------------------------------------------------



#-----------------------------------------------------------------------------------------------------------------
# petty cash start
class PettyCashExpenseRefuseWizard(models.TransientModel):
    """This wizard can be launched from an he.expense (an expense line)
    or from an hr.expense.sheet (En expense report)
    'hr_expense_refuse_model' must be passed in the context to differentiate
    the right model to use.
    """

    _name = "petty.cash.expense.refuse.wizard"
    _description = "Expense Refuse Reason Wizard"

    reason = fields.Char(string='Reason', required=True)
    hr_expense_ids = fields.Many2many('petty.cash.expense')
    hr_expense_sheet_id = fields.Many2one('petty.cash.sheet')

    @api.model
    def default_get(self, fields):
        res = super(PettyCashExpenseRefuseWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        refuse_model = self.env.context.get('hr_expense_refuse_model')
        if refuse_model == 'petty.cash.expense':
            res.update({
                'hr_expense_ids': active_ids,
                'hr_expense_sheet_id': False,
            })
        elif refuse_model == 'petty.cash.sheet':
            res.update({
                'hr_expense_sheet_id': active_ids[0] if active_ids else False,
                'hr_expense_ids': [],
            })
        return res

    @api.multi
    def expense_refuse_reason(self):
        self.ensure_one()
        if self.hr_expense_ids:
            self.hr_expense_ids.refuse_expense(self.reason)
        if self.hr_expense_sheet_id:
            self.hr_expense_sheet_id.refuse_sheet(self.reason)

        return {'type': 'ir.actions.act_window_close'}

# petty cash end
#-----------------------------------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------------------------------
# Labour start
class LabourExpenseRefuseWizard(models.TransientModel):
    """This wizard can be launched from an he.expense (an expense line)
    or from an hr.expense.sheet (En expense report)
    'hr_expense_refuse_model' must be passed in the context to differentiate
    the right model to use.
    """

    _name = "labour.expense.refuse.wizard"
    _description = "Expense Refuse Reason Wizard"

    reason = fields.Char(string='Reason', required=True)
    hr_expense_ids = fields.Many2many('labour.expense')
    hr_expense_sheet_id = fields.Many2one('labour.sheet')

    @api.model
    def default_get(self, fields):
        res = super(LabourExpenseRefuseWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        refuse_model = self.env.context.get('hr_expense_refuse_model')
        if refuse_model == 'labour.expense':
            res.update({
                'hr_expense_ids': active_ids,
                'hr_expense_sheet_id': False,
            })
        elif refuse_model == 'labour.sheet':
            res.update({
                'hr_expense_sheet_id': active_ids[0] if active_ids else False,
                'hr_expense_ids': [],
            })
        return res

    @api.multi
    def expense_refuse_reason(self):
        self.ensure_one()
        if self.hr_expense_ids:
            self.hr_expense_ids.refuse_expense(self.reason)
        if self.hr_expense_sheet_id:
            self.hr_expense_sheet_id.refuse_sheet(self.reason)

        return {'type': 'ir.actions.act_window_close'}

# Labour end
#-----------------------------------------------------------------------------------------------------------------
