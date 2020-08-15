# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError


class BankStatement(models.Model):
    _name = 'bank.statement'


    # @api.multi
    # def write(self, vals):
    #     for line in self.statement_lines:
    #         vals['date'] = line.statement_date
    #         # raise Warning(str(vals))
    #         # vals['reconcile'] = vals['reconcile']
    #     return super(BankStatement, self).write(vals)

    @api.multi
    def reconcile_lines(self):
        if self.recnl_type == 'reconcile':
            for record in self.statement_lines:
                if record.payment_id:
                    record.payment_id.state = 'reconciled'
        # res = self.write({'state': 'reconciled'})
        # return res

    @api.multi
    def unreconcile_lines(self):
        if self.recnl_type == 'unreconcile':
            for record in self.statement_lines:
                if record.payment_id and record.payment_id.state == 'reconciled':
                    record.payment_id.state = 'posted'
        # res = self.write({'state': 'unreconciled'})
        # return res

    # @api.multi
    # def cancel_lines(self):
    #     res = self.write({'state': 'draft'})
    #     return res


    @api.multi
    def show_lines(self):
        if self.recnl_type == 'unreconcile':
            domain = [('account_id', '=', self.account_id.id), ('statement_date', '=', False)]
        elif self.recnl_type == 'reconcile':
            domain = [('account_id', '=', self.account_id.id), ('statement_date', '!=', False)]
        else:
            domain = [('account_id', '=', self.account_id.id)]
        
        if self.date_from:
            domain += [('date', '>=', self.date_from)]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]
        s_lines = []
        lines = self.env['account.move.line'].search(domain)
        for line in self.statement_lines:
            line.bank_statement_id = self.id
        self.statement_lines = lines

    @api.onchange('journal_id')
    def get_lines(self):
        self.account_id = self.journal_id.default_debit_account_id.id or self.journal_id.default_credit_account_id.id
        self.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id or \
                           self.env.user.company_id.currency_id


    # @api.multi
    # def unlink(self):
    #     for bank in self:
    #         if bank.state not in ('draft'):
    #             raise UserError(_('You cannot delete the posted entries.'))
    #     return super(AccountInvoice, self).unlink()
       


    @api.one
    @api.depends('statement_lines.statement_date','date_to')
    def _compute_amount(self):
        gl_balance = 0
        bank_balance = 0
        current_update = 0
        domain = [('account_id', '=', self.account_id.id)]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]
        
        lines = self.env['account.move.line'].search(domain)
        gl_balance += sum([line.debit - line.credit for line in lines])
        # domain += [('statement_date', '!=', False)]
        # ('id', 'not in', self.statement_lines.ids), 
        # domain += [('statement_date','<=', self.date_to)]
        domain2 = [('account_id', '=', self.account_id.id)]
        lines1 = self.env['account.move.line'].search(domain2)

        for l in lines1:
            if self.date_to:
                if l.statement_date and l.statement_date <= self.date_to:
                    # bank_balance += l.balance
                    current_update += l.debit - l.credit
            else:
                if l.statement_date:
                    # bank_balance += l.balance
                    current_update += l.debit - l.credit
            # else:
            #     bank_balance += l.balance
        # for x in self.statement_lines:
        #     if x.statement_date:
        #         if self.date_to:
        #             if x.statement_date and x.statement_date <= self.date_to:
        #                 current_update += x.debit - x.credit 
        #         else:
        #             current_update += x.debit - x.credit 
        #     else:
        #         current_update = 0

        self.gl_balance = gl_balance
        # self.bank_balance = bank_balance + current_update
        self.bank_balance = current_update
        self.balance_difference = self.gl_balance - self.bank_balance
# 
    journal_id = fields.Many2one('account.journal', 'Bank', domain=[('type', '=', 'bank')])
    account_id = fields.Many2one('account.account', 'Bank Account')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    recnl_type = fields.Selection([('reconcile','Reconcile'),('unreconcile','Unreconcile'),('all','All'),],default='unreconcile',string='Reconcile status')
    statement_lines = fields.One2many('account.move.line', 'bank_statement_id')
    gl_balance = fields.Monetary('Book Balance', readonly=True, compute='_compute_amount')
    bank_balance = fields.Monetary('Bank Balance', readonly=True, compute='_compute_amount')
    balance_difference = fields.Monetary('Unreconciled Amount', readonly=True, compute='_compute_amount')
    current_update = fields.Monetary('Balance of entries updated now')
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('bank.statement'))
    # state = fields.Selection([('draft','Draft'),('reconciled','Reconciled'),('unreconciled','Unreconciled')],'Status',default="draft")


