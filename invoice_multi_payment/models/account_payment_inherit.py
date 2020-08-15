from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class account_payment(models.Model):
    _inherit = 'account.payment'
    
    invoice_lines = fields.One2many('payment.invoice.line', 'payment_id', string="Invoice Line")
   
    @api.multi
    def update_invoice_lines(self):
        for inv in self.invoice_lines:
            inv.open_amount = inv.invoice_id.residual 
        self.onchange_partner_id()
        
    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        # Set partner_id domain
        if self.partner_type:
            if not self.env.context.get('default_invoice_ids'):
                self.partner_id = False
            return {'domain': {'partner_id': [(self.partner_type, '=', True)]}}

    @api.onchange('partner_id', 'currency_id')
    def onchange_partner_id(self):
        if self.partner_id and self.payment_type != 'transfer':
            vals = {}
            line = [(6, 0, [])]
            invoice_ids = []
            if self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_ids = self.env['account.invoice'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','open'),
                                                                  ('type','=', 'in_invoice'),
                                                                  ('currency_id', '=', self.currency_id.id)])
            if self.payment_type == 'inbound' and self.partner_type == 'supplier':
                invoice_ids = self.env['account.invoice'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','open'),
                                                                  ('type','=', 'in_refund'),
                                                                  ('currency_id', '=', self.currency_id.id)])
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_ids = self.env['account.invoice'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','open'),
                                                                  ('type','=', 'out_invoice'),
                                                                  ('currency_id', '=', self.currency_id.id)])
            if self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_ids = self.env['account.invoice'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','open'),
                                                                  ('type','=', 'out_refund'),
                                                                  ('currency_id', '=', self.currency_id.id)])

            for inv in invoice_ids[::-1]:
                vals = {
                       'invoice_id': inv.id,
                       }
                line.append((0, 0, vals))
            self.invoice_lines = line
            self.onchnage_amount() 
        
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type == 'transfer':
            self.invoice_lines = [(6, 0, [])]
            
        if not self.invoice_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        res['domain']['journal_id'] = self.payment_type == 'inbound' and [('at_least_one_inbound', '=', True)] or [('at_least_one_outbound', '=', True)]
        res['domain']['journal_id'].append(('type', 'in', ('bank', 'cash')))
        return res
    
    @api.onchange('amount')
    def onchnage_amount(self):
        total = 0.0
        remain = self.amount
        for line in self.invoice_lines:
            if line.open_amount <= remain:
                line.allocation = line.open_amount
                remain -= line.allocation
            else:
                line.allocation = remain
                remain -= line.allocation
            total += line.allocation

    @api.multi
    def post(self):
        """"Override to process multiple invoice using single payment."""
        for rec in self:
            # code start
#             total = 0.0
#             for line in rec.invoice_lines:
#                 if line.allocation < 0:
#                     raise ValidationError(_("Negative allocation amount not allowed!"))
#                 if line.allocation > line.open_amount:
#                     raise UserError("Allocation amount %s is greater then open amount %s of Invoice." % (line.allocation, line.open_amount))
#                 total += line.allocation
#                 if line.open_amount != line.invoice_id.residual:
#                     raise UserError("Due amount changed.\n Please click 'Update Invoice' button to update amount")
#                  
#             if total > rec.amount:
#                 raise UserError("Total allocation %s is more then payment amount %s" % (total, rec.amount))
            amt = 0
            if rec.invoice_lines:
                 
                for line in rec.invoice_lines:
                    amt += line.allocation
                # if rec.amount < amt:
                #     raise ValidationError(("Payment amount must be greater then or equal to '%s'") %(amt))
                # if rec.amount > amt:
                #     for line in rec.invoice_lines:
                #         line.allocation = line.allocation + (rec.amount - amt)
                #         break
        return  super(account_payment,self).post()
            

    @api.multi
    def _create_payment_entry(self, amount):
        """ Create a journal entry related to a payment"""
        # If group data
        if self.invoice_ids and self.invoice_lines:
            aml_obj = self.env['account.move.line'].\
                with_context(check_move_validity=False)
            invoice_currency = False
            if self.invoice_ids and\
                    all([x.currency_id == self.invoice_ids[0].currency_id
                         for x in self.invoice_ids]):
                # If all the invoices selected share the same currency,
                # record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id
            move = self.env['account.move'].create(self._get_move_vals())
            p_id = str(self.partner_id.id)
            for inv in self.invoice_ids:
                amt = 0
                if self.partner_type == 'customer':
                    for line in self.invoice_lines:
                        if line.invoice_id.id == inv.id:
                            if inv.type == 'out_invoice':
                                amt = -(line.allocation)
                            else:
                                amt = line.allocation
                else:
                    for line in self.invoice_lines:
                        if line.invoice_id.id == inv.id:
                            if inv.type == 'in_invoice':
                                amt = line.allocation
                            else:
                                amt = -(line.allocation)

                debit, credit, amount_currency, currency_id =\
                    aml_obj.with_context(date=self.payment_date).\
                    _compute_amount_fields(amt, self.currency_id,
                                          self.company_id.currency_id,
                                          )
                # Write line corresponding to invoice payment
                counterpart_aml_dict =\
                    self._get_shared_move_line_vals(debit,
                                                    credit, amount_currency,
                                                    move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(inv))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                # Reconcile with the invoices and write off
                if self.partner_type == 'customer':
                    handling = 'open'
                    for line in self.invoice_lines:
                        if line.invoice_id.id == inv.id:
                            payment_difference = line.open_amount - line.allocation
                    writeoff_account_id = self.journal_id and self.journal_id.id or False
                    if handling == 'reconcile' and\
                            payment_difference:
                        writeoff_line =\
                            self._get_shared_move_line_vals(0, 0, 0, move.id,
                                                            False)
                        debit_wo, credit_wo, amount_currency_wo, currency_id =\
                            aml_obj.with_context(date=self.payment_date).\
                            _compute_amount_fields(
                                payment_difference,
                                self.currency_id,
                                self.company_id.currency_id,
                                )
                        writeoff_line['name'] = _('Counterpart')
                        writeoff_line['account_id'] = writeoff_account_id
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = credit_wo
                        writeoff_line['amount_currency'] = amount_currency_wo
                        writeoff_line['currency_id'] = currency_id
                        writeoff_line = aml_obj.create(writeoff_line)
                        if counterpart_aml['debit']:
                            counterpart_aml['debit'] += credit_wo - debit_wo
                        if counterpart_aml['credit']:
                            counterpart_aml['credit'] += debit_wo - credit_wo
                        counterpart_aml['amount_currency'] -=\
                            amount_currency_wo
                inv.register_payment(counterpart_aml)
                # Write counterpart lines
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                liquidity_aml_dict =\
                    self._get_shared_move_line_vals(credit, debit,
                                                    -amount_currency, move.id,
                                                    False)
                liquidity_aml_dict.update(
                    self._get_liquidity_move_line_vals(-amount))
                aml_obj.create(liquidity_aml_dict)
            move.post()
            return move

        return super(account_payment, self)._create_payment_entry(amount)
    
    @api.model
    def create(self,vals):
        res = super(account_payment,self).create(vals)
        if vals.get('invoice_lines'):
            res.invoice_ids = res.invoice_lines.mapped('invoice_id')
        return res
    
    @api.multi
    def write(self,vals):
        res = super(account_payment,self).write(vals)
        if vals.get('invoice_lines'):
            self.invoice_ids = self.invoice_lines.mapped('invoice_id')
        
        return res

class PaymentInvoiceLine(models.Model):
    _name = 'payment.invoice.line'
    
    payment_id = fields.Many2one('account.payment', string="Payment")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    invoice = fields.Char(related='invoice_id.number', string="Invoice Number")
    account_id = fields.Many2one(related="invoice_id.account_id", string="Account")
    date = fields.Date(string='Invoice Date', compute='_get_invoice_data', store=True)
    due_date = fields.Date(string='Due Date', compute='_get_invoice_data', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_get_invoice_data', store=True)
    open_amount = fields.Float(string='Due Amount', compute='_get_invoice_data', store=True)
    allocation = fields.Float(string='Allocation Amount')
    
    @api.multi
    @api.depends('invoice_id')
    def _get_invoice_data(self):
        for data in self:
            invoice_id = data.invoice_id
            data.date = invoice_id.date_invoice
            data.due_date = invoice_id.date_due
            data.total_amount = invoice_id.amount_total 
            data.open_amount = invoice_id.residual
