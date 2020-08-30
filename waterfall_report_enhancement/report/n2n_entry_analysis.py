# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools

# N2NAccountInvoiceReport
class N2NAccountEntryAnalysis(models.Model):
    _name = "n2n.account.entry.analysis"
    _description = "N2N Account Entry Analysis"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char(string='Number')
    date = fields.Date(string="Date")
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status')
    quantity = fields.Float(digits=(16, 2),string="Quantity")
    product_id = fields.Many2one('product.product', string='Product')
    debit = fields.Monetary(default=0.0, string='Debit')
    credit = fields.Monetary(default=0.0, string='Credit')
    balance = fields.Monetary(string='Balance')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_residual = fields.Monetary( string='Residual Amount')
    amount_residual_currency = fields.Monetary(string='Residual Amount in Currency')
    account_id = fields.Many2one('account.account', string='Account')
    ref = fields.Char( string='Reference')
    payment_id = fields.Many2one('account.payment', string="Originator Payment")
    reconciled = fields.Boolean(string="Reconciled")
    full_reconcile_id = fields.Many2one('account.full.reconcile', string="Matching Number")
    journal_id = fields.Many2one('account.journal',  string='Journal')
    blocked = fields.Boolean(string='No Follow-up')
    date_maturity = fields.Date(string='Due date')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    tax_line_id = fields.Many2one('account.tax', string='Originator tax', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    company_id = fields.Many2one('res.company', related='account_id.company_id', string='Company', store=True)
    invoice_id = fields.Many2one('account.invoice', oldname="invoice")
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    user_type_id = fields.Many2one('account.account.type', string="Account Type")
    tax_exigible = fields.Boolean(string='Appears in VAT report')


    @api.model_cr
    def init(self):
        cr = self.env.cr   
        tools.drop_view_if_exists(cr, 'n2n_account_entry_analysis')
        cr.execute("""
            create or replace view n2n_account_entry_analysis as (
                SELECT
                	mvl.id,
					mvl.balance_cash_basis,
					mvl.debit_cash_basis, 
					mvl.account_id, 
					mvl.tax_exigible, 
					mvl.create_uid, 
					(mvl.credit * -1) AS credit, 
					mvl.blocked, 
					mvl.company_id, 
					mvl.credit_cash_basis, 
					mvl.amount_currency,  
					mvl.date_maturity, 	
					mvl.amount_residual, 
					mvl.write_date, 
					mvl.payment_id, 
					mvl.partner_id, 
					mvl.create_date, 
					mvl.reconciled, 
					mvl.amount_residual_currency, 
					mvl.invoice_id, 
					mvl.statement_id, 
					mvl.quantity, 
					mvl.product_id, 
					mvl.debit, 
					mvl.journal_id,
					mvl.user_type_id,
					mvl.ref, 
					mvl.currency_id,  
					mvl.full_reconcile_id, 
					mvl.write_uid, 
					mvl.analytic_account_id, 
					mvl.balance,
					mve.state,
					mve.name,
					mve.date

				FROM account_move_line mvl
				LEFT JOIN account_move mve ON mvl.move_id = mve.id
				LEFT JOIN res_partner ptnr ON mvl.partner_id = ptnr.id
				LEFT JOIN product_product prd ON mvl.product_id = prd.id
				LEFT JOIN account_account acc ON mvl.account_id = acc.id
            )
        """)
