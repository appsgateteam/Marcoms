import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from odoo.addons import decimal_precision as dp




class food_expense_detals(models.Model):
    _name = 'food.expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Food Expense"
    _order = "date desc, id desc"

    @api.model
    def _default_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    # @api.model
    # def _default_product_uom_id(self):
    #     return self.env['uom.uom'].search([], limit=1, order='id')

    @api.model
    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    @api.model
    def _get_employee_id_domain(self):

        res= [('id', '=', 0)] # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_manager') or self.user_has_groups('account.group_account_user'):
            res = [] # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_user') and self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = ['|', '|', ('department_id.manager_id.id', '=', employee.id),
                   ('parent_id.id', '=', employee.id), ('expense_manager_id.id', '=', employee.id)]
        elif self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = [('id', '=', employee.id)]
        return res

    # product_id_food_st = fields.Many2one('res.config.settings', string='Product', readonly=True)
    name = fields.Char('Description', readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    date = fields.Date(readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=fields.Date.context_today, string="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", compute='_compute_employy')
    product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)])
    # product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_product_uom_id)
    unit_amount = fields.Float("Unit Price", readonly=True, currency_field='currency_id', required=True,states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    quantity = fields.Float( string='Quantity' ,   readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    tax_ids = fields.Many2many('account.tax','food_expense_id', 'tax_id', string='VAT',  readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    untaxed_amount = fields.Float("Subtotal", store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    total_amount = fields.Monetary("Total Amount", compute='_compute_amount', store=True, currency_field='currency_id', digits=dp.get_precision('Account'))
    company_currency_id = fields.Many2one('res.currency', string="Report Company Currency", related='sheet_id.currency_id', store=True, readonly=False)
    total_amount_company = fields.Monetary("Total (Company Currency)", compute='_compute_total_amount_company', store=True, currency_field='company_currency_id', digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, oldname='analytic_account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, default=_default_account_id, help="An expense account is expected")
    description = fields.Text('Notes...', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True  , string="Paid By")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the Food expense.")
    sheet_id = fields.Many2one('food.expense.sheet', string="Food Expense Report", readonly=True, copy=False)
    reference = fields.Char("Bill Reference" , readonly=True , required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    is_refused = fields.Boolean("Explicitely Refused by manager or acccountant", readonly=True, copy=False)
    # by Fouad
    meal_type = fields.Many2one('meal.type', string='Meal Type', required=True,  change_default=True, track_visibility='always', help="You can find Type Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    
    # meal_type = fields.Selection([
    #     ('breakfast', 'Breakfast'),
    #     ('dinner', 'Dinner'),
    # ],  string='Meal Type', copy=False, index=True, store=True, help="Status of the meal.")
    # account = fields.Many2one('account', string='Account', required=True,  change_default=True, track_visibility='always', help="You can find Type Reference.")

    # account =  fields.Selection([
    #     ('one', '300241 Food Exp., Water & Refreshment'),
    #     ('tow', 'Tow'),
    #     ('three', 'Three'),
    # ],  string='Account', copy=False, index=True, store=True, default="one")
    project_id = fields.Many2one('project.project', string='Project', required=True , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True,  change_default=True, track_visibility='always', help="You can find a vendor by its Name, TIN, Email or Internal Reference." , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    project_manager = fields.Many2one('res.users',string="Project Manager")
    # food_seq = fields.Char('Sequnce', required=True, copy=False, readonly=True, default='New')
    # product_id_food = fields.Char("product" , readonly=True , required=True, related ='product_id_food_sting.product_id')

    # product_id_food = fields.Many2one('product.food', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})


    # @api.model
    # def default_manager(self):
    # manager = self.env.user.company_id.manager_company.name
    # return managere
    can_project = fields.Char('Can project', compute='_compute_can_project')

    @api.onchange('project_id')
    def _compute_man_project(self):
        for rec in self:
            rec.project_manager = rec.project_id.user_id.id
            rec.analytic_account_id = rec.project_id.analytic_account_id.id

    @api.model
    def _compute_can_project(self):
        for rec in self:
            rec.can_project = rec.project_id.name


    
    @api.model
    @api.depends('employee_id')
    def _compute_employy(self):
        com = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

        for rec in self:
            rec.employee_id = com.id
       


    @api.one
    @api.constrains('quantity')
    def _check_values(self):
        if self.quantity == 0.0 :
            raise Warning(_('Quantity should not be zero.'))

    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.project_id.user_id
    #     for rec in self:
    #         if rec.sheet_id.user_id == is_expense_user :
    #             rec.can_project = True



    # @api.model
    # def create(self, vals):
    #     if vals.get('food_seq', 'New') == 'New':
    #         vals['food_seq'] = self.env['ir.sequence'].next_by_code('food.expense.sequence') or 'New'   


    #     result = super(food_expense_detals, self).create(vals)       

    #     return result



    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

    @api.depends('date', 'total_amount', 'company_currency_id')
    def _compute_total_amount_company(self):
        for expense in self:
            amount = 0
            if expense.company_currency_id:
                date_expense = expense.date
                amount = expense.currency_id._convert(
                    expense.total_amount, expense.company_currency_id,
                    expense.company_id, date_expense or fields.Date.today())
            expense.total_amount_company = amount

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'food.expense'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            # self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    # @api.onchange('product_uom_id')
    # def _onchange_product_uom_id(self):
    #     if self.product_id and self.product_uom_id.category_id != self.product_id.uom_id.category_id:
    #         raise UserError(_('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.'))

    # ----------------------------------------
    # ORM Overrides
    # ----------------------------------------

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['done', 'approved']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
        return super(food_expense_detals, self).unlink()

    @api.model
    def get_empty_list_help(self, help_message):
        if help_message and "o_view_nocontent_smiling_face" not in help_message:
            use_mailgateway = self.env['ir.config_parameter'].sudo().get_param('hr_expense.use_mailgateway')
            alias_record = use_mailgateway and self.env.ref('hr_expense.mail_alias_expense') or False
            if alias_record and alias_record.alias_domain and alias_record.alias_name:
                link = "<a id='o_mail_test' href='mailto:%(email)s?subject=Lunch%%20with%%20customer%%3A%%20%%2412.32'>%(email)s</a>" % {
                    'email': '%s@%s' % (alias_record.alias_name, alias_record.alias_domain)
                }
                return '<p class="o_view_nocontent_smiling_face">%s</p><p class="oe_view_nocontent_alias">%s</p>' % (
                    _('Add a new expense,'),
                    _('or send receipts by email to %s.') % (link),)
        return super(food_expense_detals, self).get_empty_list_help(help_message)

    # ----------------------------------------
    # Actions
    # ----------------------------------------

    @api.multi
    def action_view_sheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'food.expense.sheet',
            'target': 'current',
            'res_id': self.sheet_id.id
        }

    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'food.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_name': todo[0].name if len(todo) == 1 else '',
                'default_user_id': self[0].project_manager.id
                
            }
        }

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'food.expense'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'food.expense', 'default_res_id': self.id}
        return res

    # ----------------------------------------
    # Business
    # ----------------------------------------

    @api.multi
    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    @api.multi
    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        for expense in self:
            # create the move that will contain the accounting entries
            if expense.sheet_id.id not in move_grouped_by_sheet:
                move = self.env['account.move'].create(expense._prepare_move_values())
                move_grouped_by_sheet[expense.sheet_id.id] = move
            else:
                move = move_grouped_by_sheet[expense.sheet_id.id]
        return move_grouped_by_sheet

    @api.multi
    def _get_expense_account_source(self):
        self.ensure_one()
        if self.account_id:
            account = self.account_id
        elif self.product_id:
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (self.product_id.name))
        else:
            account = self.env['ir.property'].with_context(force_company=self.company_id.id).get('property_account_expense_categ_id', 'product.category')
            if not account:
                raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
        return account

    @api.multi
    def _get_expense_account_destination(self):
        self.ensure_one()
        account_dest = self.env['account.account']
        if self.payment_mode == 'company_account':
            if not self.sheet_id.bank_journal_id.default_credit_account_id:
                raise UserError(_("No credit account found for the %s journal, please configure one.") % (self.sheet_id.bank_journal_id.name))
            account_dest = self.sheet_id.bank_journal_id.default_credit_account_id.id
        else:
            if not self.employee_id.address_home_id:
                raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
            account_dest = self.employee_id.address_home_id.property_account_payable_id.id
        return account_dest

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.partner_id.id

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                # 'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'food_expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount -= move_line_src['debit']
            total_amount_currency -= move_line_src['amount_currency'] or move_line_src['debit']

            # taxes move lines
            for tax in taxes['taxes']:
                amount = tax['amount']
                amount_currency = False
                if different_currency:
                    amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                    amount_currency = tax['amount']
                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                    'amount_currency': amount_currency if different_currency else 0.0,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_line_id': tax['id'],
                    'food_expense_id': expense.id,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id if different_currency else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'food_expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'name': expense.name,
                })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.with_context(dont_create_taxes=True).write({
                'line_ids': [(0, 0, line) for line in move_line_values]
            })
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

        # post the moves
        for move in move_group_by_sheet.values():
            move.post()

        return move_group_by_sheet

    

    @api.multi
    def refuse_expense(self, reason):
        self.write({'is_refused': True})
        self.sheet_id.write({'state': 'cancel'})
        self.sheet_id.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                             values={'reason': reason, 'is_sheet': False, 'name': self.name})

    # ----------------------------------------
    # Mail Thread
    # ----------------------------------------

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}

        email_address = email_split(msg_dict.get('email_from', False))[0]

        employee = self.env['hr.employee'].search([
            '|',
            ('work_email', 'ilike', email_address),
            ('user_id.email', 'ilike', email_address)
        ], limit=1)

        expense_description = msg_dict.get('subject', '')

        # Match the first occurence of '[]' in the string and extract the content inside it
        # Example: '[foo] bar (baz)' becomes 'foo'. This is potentially the product code
        # of the product to encode on the expense. If not, take the default product instead
        # which is 'Fixed Cost'
        default_product = self.env.ref('hr_expense.product_product_fixed_cost')
        pattern = '\[([^)]*)\]'
        product_code = re.search(pattern, expense_description)
        if product_code is None:
            product = default_product
        else:
            expense_description = expense_description.replace(product_code.group(), '')
            products = self.env['product.product'].search([('default_code', 'ilike', product_code.group(1))]) or default_product
            product = products.filtered(lambda p: p.default_code == product_code.group(1)) or products[0]
        account = product.product_tmpl_id._get_product_accounts()['expense']

        pattern = '[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
        # Match the last occurence of a float in the string
        # Example: '[foo] 50.3 bar 34.5' becomes '34.5'. This is potentially the price
        # to encode on the expense. If not, take 1.0 instead
        expense_price = re.findall(pattern, expense_description)
        # TODO: International formatting
        if not expense_price:
            price = 1.0
        else:
            price = expense_price[-1][0]
            expense_description = expense_description.replace(price, '')
            try:
                price = float(price)
            except ValueError:
                price = 1.0

        custom_values.update({
            'name': expense_description.strip(),
            'employee_id': employee.id,
            'product_id': product.id,
            # 'product_uom_id': product.uom_id.id,
            'tax_ids': [(4, tax.id, False) for tax in product.supplier_taxes_id],
            'quantity': 1,
            'unit_amount': price,
            'company_id': employee.company_id.id,
        })
        if account:
            custom_values['account_id'] = account.id
        return super(food_expense_detals, self).message_new(msg_dict, custom_values)



class food_Sheet(models.Model):
    """
        Here are the rights associated with the expense flow

        Action       Group                   Restriction
        =================================================================================
        Submit      Employee                Only his own
                    Officer                 If he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Approve     Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Post        Anybody                 State = approve and journal_id defined
        Done        Anybody                 State = approve and journal_id defined
        Cancel      Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        =================================================================================
    """
    _name = "food.expense.sheet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Expense Report"
    _order = "accounting_date desc, id desc"

    @api.model
    def _default_journal_id(self):
        journal = self.env.ref('hr_expense.hr_expense_account_journal', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        return journal.id

    @api.model
    def _default_bank_journal_id(self):
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    name = fields.Char('Expense Report Summary', required=True , readonly=True , states={'draft': [('readonly', False)], 'submit': [('readonly', False)], 'cancel': [('readonly', False)]})
    expense_line_ids = fields.One2many('food.expense', 'sheet_id', string='Expense Lines', states={'approve': [('readonly', True)], 'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True, help='Expense Report State')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    address_id = fields.Many2one('res.partner', string="Employee Home Address")
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company")], related='expense_line_ids.payment_mode', default='company_account', readonly=True, string="Paid By")
    user_id = fields.Many2one('res.users', 'Manager', copy=False, readonly=True)
    # user_id = fields.Many2one('res.users', 'Manager', related='expense_line_ids.project_id.user_id' , readonly=True, copy=False, states={'draft': [('readonly', False)]}, track_visibility='onchange', oldname='responsible_id')
    total_amount = fields.Monetary('Total Amount', currency_field='currency_id', compute='_compute_amount', store=True, digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_journal_id, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_bank_journal_id, help="The payment method used when the expense is paid by the company.")
    accounting_date = fields.Date("Date")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False)
    department_id = fields.Many2one('hr.department', string='Department', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    is_multiple_currency = fields.Boolean("Handle lines with different currencies", compute='_compute_is_multiple_currency')
    can_reset = fields.Boolean('Can Reset', compute='_compute_can_reset')

    
    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.user_id.id
    #     for rec in self:
    #         if rec.expense_line_ids.project_id.user_id.id == is_expense_user :
    #             rec.can_project = True

     # @api.onchange('user_id','expense_line_ids')
    # def onchange_values(self):
    #     return {'domain': {'expense_line_ids': {[ ('user_id', '=', self.user_id.id)]}}

    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.user_id
    #     for rec in self:
    #         if rec.expense_line_ids.project_id.user_id == is_expense_user :
    #             rec.can_project = True



    @api.depends('expense_line_ids.total_amount_company')
    def _compute_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_company'))

    @api.multi
    def _compute_attachment_number(self):
        for sheet in self:
            sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))

    @api.depends('expense_line_ids.currency_id')
    def _compute_is_multiple_currency(self):
        for sheet in self:
            sheet.is_multiple_currency = len(sheet.expense_line_ids.mapped('currency_id')) > 1

    @api.multi
    def _compute_can_reset(self):
        is_expense_user = self.user_has_groups('hr_expense.group_hr_expense_user')
        for sheet in self:
            sheet.can_reset = is_expense_user if is_expense_user else sheet.employee_id.user_id == self.env.user

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.address_id = rec.employee_id.sudo().address_home_id
            rec.department_id = rec.employee_id.department_id
            if not rec.user_id :
                rec.user_id = rec.expense_line_ids.project_manager.id
        # self.user_id = self.employee_id.expense_manager_id or self.employee_id.parent_id.user_id

    @api.multi
    @api.constrains('expense_line_ids')
    def _check_payment_mode(self):
        for sheet in self:
            expense_lines = sheet.mapped('expense_line_ids')
            if expense_lines and any(expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
                raise ValidationError(_("Expenses must be paid by the same entity (Company or employee)."))

    # @api.constrains('expense_line_ids', 'employee_id')
    # def _check_employee(self):
    #     for sheet in self:
    #         employee_ids = sheet.expense_line_ids.mapped('employee_id')
    #         if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != sheet.employee_id):
    #             raise ValidationError(_('You cannot add expenses of another employee.'))

    @api.model
    def create(self, vals):
        sheet = super(food_Sheet, self.with_context(mail_create_nosubscribe=True)).create(vals)
        sheet.activity_update()
        return sheet

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['post', 'done']:
                raise UserError(_('You cannot delete a posted or paid expense.'))
        super(food_Sheet, self).unlink()

    # --------------------------------------------
    # Mail Thread
    # --------------------------------------------

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'approve':
            return 'hr_expense.mt_expense_approved'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_expense.mt_expense_refused'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_expense.mt_expense_paid'
        return super(food_Sheet, self)._track_subtype(init_values)

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(food_Sheet, self)._message_auto_subscribe_followers(updated_values, subtype_ids)
        if updated_values.get('employee_id'):
            employee = self.env['hr.employee'].browse(updated_values['employee_id'])
            if employee.user_id:
                res.append((employee.user_id.partner_id.id, subtype_ids, False))
        return res

    # --------------------------------------------
    # Actions
    # --------------------------------------------


    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    # @api.multi
    # def action_sheet_move_create(self):
    #     if any(sheet.state != 'approve' for sheet in self):
    #         raise UserError(_("You can only generate accounting entry for approved expense(s)."))

    #     if any(not sheet.journal_id for sheet in self):
    #         raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

    #     expense_line_ids = self.mapped('expense_line_ids')\
    #         .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
    #     res = expense_line_ids.action_move_create()

    #     if not self.accounting_date:
    #         self.accounting_date = self.account_move_id.date

    #     if self.payment_mode == 'own_account' and expense_line_ids:
    #         self.write({'state': 'post'})
    #     else:
    #         self.write({'state': 'done'})
    #     self.activity_update()
    #     return res

    @api.multi
    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'food.expense'), ('res_id', 'in', self.expense_line_ids.ids)]
        res['context'] = {
            'default_res_model': 'food.expense.sheet',
            'default_res_id': self.ids,
            'create': False,
            'edit': False,
        }
        return res

    # --------------------------------------------
    # Business
    # --------------------------------------------

    @api.multi
    def set_to_paid(self):
        self.write({'state': 'done'})

    @api.multi
    def action_submit_sheet(self):
        self.write({'state': 'submit'})
        self.activity_update()

    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'approve', 'user_id': responsible_id})
        self.activity_update()

    @api.multi
    def paid_expense_sheets(self):
        self.write({'state': 'done'})

    @api.multi
    def refuse_sheet(self, reason):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot refuse your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only refuse your department expenses"))

        self.write({'state': 'cancel'})
        for sheet in self:
            sheet.message_post_with_view('hr_expense.hr_expense_template_refuse_reason', values={'reason': reason, 'is_sheet': True, 'name': self.name})
        self.activity_update()

    @api.multi
    def reset_expense_sheets(self):
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        self.mapped('expense_line_ids').write({'is_refused': False})
        self.write({'state': 'draft'})
        self.activity_update()
        return True

    def _get_responsible_for_approval(self):
        if self.user_id:
            return self.user_id
        elif self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.department_id.manager_id.user_id:
            return self.employee_id.department_id.manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'approve').activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(['hr_expense.mail_act_expense_approval'])



# Transportaion Start 
# <------------------------------------------------------------------------------------------------------------>


class Transportaion_expense_detals(models.Model):
    _name = 'transportaion.expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Transportaion Expense"
    _order = "date desc, id desc"

    @api.model
    def _default_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    # @api.model
    # def _default_product_uom_id(self):
    #     return self.env['uom.uom'].search([], limit=1, order='id')

    @api.model
    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    @api.model
    def _get_employee_id_domain(self):

        res= [('id', '=', 0)] # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_manager') or self.user_has_groups('account.group_account_user'):
            res = [] # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_user') and self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = ['|', '|', ('department_id.manager_id.id', '=', employee.id),
                   ('parent_id.id', '=', employee.id), ('expense_manager_id.id', '=', employee.id)]
        elif self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = [('id', '=', employee.id)]
        return res

    name = fields.Char('Description', readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    date = fields.Date(readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=fields.Date.context_today, string="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", compute='_compute_employy')
    product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)])
    # product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_product_uom_id)
    # unit_amount = fields.Float("Unit Price", readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, digits=dp.get_precision('Product Price'))
    # quantity = fields.Float(required=True, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    # tax_ids = fields.Many2many('account.tax','transportaion_expense_id', 'tax_id', string='Taxes',  readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    # untaxed_amount = fields.Float("Subtotal", store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    total_amount = fields.Monetary("Total Amount", compute='_compute_amount', store=True, currency_field='currency_id', digits=dp.get_precision('Account'))
    company_currency_id = fields.Many2one('res.currency', string="Report Company Currency", related='sheet_id.currency_id', store=True, readonly=False)
    total_amount_company = fields.Monetary("Total (Company Currency)", compute='_compute_total_amount_company', store=True, currency_field='company_currency_id', digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, oldname='analytic_account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, default=_default_account_id, help="An expense account is expected")
    description = fields.Text('Notes...', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account',  readonly=True  , string="Paid By")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the Food expense.")
    sheet_id = fields.Many2one('transportaion.expense.sheet', string="Food Expense Report", readonly=True, copy=False)
    reference = fields.Char("Receipt No"  , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    is_refused = fields.Boolean("Explicitely Refused by manager or acccountant", readonly=True, copy=False)
    # by Fouad
    # meal_type = fields.Selection([
    #     ('breakfast', 'Breakfast'),
    #     ('dinner', 'Dinner'),
    # ],  string='Meal Type', copy=False, index=True, store=True, help="Status of the meal.")
    # account =  fields.Selection([
    #     ('one', '300241 Food Exp., Water & Refreshment'),
    #     ('tow', 'Tow'),
    #     ('three', 'Three'),
    # ],  string='Account', copy=False, index=True, store=True, default="one")
    project_id = fields.Many2one('project.project', string='Project' , required=True , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Supplier Name' , required=True,  change_default=True, track_visibility='always', help="You can find a vendor by its Name, TIN, Email or Internal Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    type_id = fields.Many2one('transportaion.type', string='Type' , required=True,  change_default=True, track_visibility='always', help="You can find Type Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    vehicle_type_id = fields.Many2one('transportaion.vehicle.type' , string='Vehicle Type', required=True,  change_default=True, track_visibility='always', help="You can find Vehicle Type Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    vehicle_no = fields.Char('Vehicle No', required=True ,   readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    trip_from = fields.Char('Trip From', required=True ,  readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    trip_to = fields.Char('Trip To', required=True ,  readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    remarks = fields.Char('Remarks',   readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    rates = fields.Monetary("Rates", store=True , currency_field='currency_id', digits=dp.get_precision('Account'), readonly=True  , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    labour_charges = fields.Monetary("Labour Charges", store=True , currency_field='currency_id', digits=dp.get_precision('Account') , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    waiting_charges  = fields.Monetary("Waiting Charges", store=True , currency_field='currency_id', digits=dp.get_precision('Account') , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    # product_id_transpotaion = fields.Many2one('product.transpotaion', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})

    # food_seq = fields.Char('Sequnce', required=True, copy=False, readonly=True, default='New')


    # @api.model
    # def create(self, vals):
    #     if vals.get('food_seq', 'New') == 'New':
    #         vals['food_seq'] = self.env['ir.sequence'].next_by_code('food.expense.sequence') or 'New'   


    #     result = super(food_expense_detals, self).create(vals)       

    #     return result
    project_manager = fields.Many2one('res.users',string="Project Manager")

    @api.onchange('project_id')
    def _compute_man_project(self):
        for rec in self:
            rec.project_manager = rec.project_id.user_id.id
            rec.analytic_account_id = rec.project_id.analytic_account_id.id

    
    
    @api.model
    @api.depends('employee_id')
    def _compute_employy(self):
        com = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        for rec in self:
            rec.employee_id = com.id


    @api.one
    @api.constrains('rates')
    def _check_values(self):
        if self.rates == 0.0 :
            raise Warning(_('Rates should not be zero.'))


    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

    @api.depends('rates', 'labour_charges', 'waiting_charges')
    def _compute_amount(self):
        for expense in self:
            expense.total_amount = (expense.rates + expense.labour_charges + expense.waiting_charges)
            # expense.untaxed_amount = expense.unit_amount * expense.quantity
            # taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            # expense.total_amount = taxes.get('total_included')

    @api.depends('date', 'total_amount', 'company_currency_id')
    def _compute_total_amount_company(self):
        for expense in self:
            amount = 0
            if expense.company_currency_id:
                date_expense = expense.date
                amount = expense.currency_id._convert(
                    expense.total_amount, expense.company_currency_id,
                    expense.company_id, date_expense or fields.Date.today())
            expense.total_amount_company = amount

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'transportaion.expense'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            # self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            # self.product_uom_id = self.product_id.uom_id
            # self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    # @api.onchange('product_uom_id')
    # def _onchange_product_uom_id(self):
    #     if self.product_id and self.product_uom_id.category_id != self.product_id.uom_id.category_id:
    #         raise UserError(_('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.'))

    # ----------------------------------------
    # ORM Overrides
    # ----------------------------------------

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['done', 'approved']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
        return super(Transportaion_expense_detals, self).unlink()

    @api.model
    def get_empty_list_help(self, help_message):
        if help_message and "o_view_nocontent_smiling_face" not in help_message:
            use_mailgateway = self.env['ir.config_parameter'].sudo().get_param('hr_expense.use_mailgateway')
            alias_record = use_mailgateway and self.env.ref('hr_expense.mail_alias_expense') or False
            if alias_record and alias_record.alias_domain and alias_record.alias_name:
                link = "<a id='o_mail_test' href='mailto:%(email)s?subject=Lunch%%20with%%20customer%%3A%%20%%2412.32'>%(email)s</a>" % {
                    'email': '%s@%s' % (alias_record.alias_name, alias_record.alias_domain)
                }
                return '<p class="o_view_nocontent_smiling_face">%s</p><p class="oe_view_nocontent_alias">%s</p>' % (
                    _('Add a new expense,'),
                    _('or send receipts by email to %s.') % (link),)
        return super(Transportaion_expense_detals, self).get_empty_list_help(help_message)

    # ----------------------------------------
    # Actions
    # ----------------------------------------

    @api.multi
    def action_view_sheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'transportaion.expense.sheet',
            'target': 'current',
            'res_id': self.sheet_id.id
        }

    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'transportaion.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_name': todo[0].name if len(todo) == 1 else '',
                'default_user_id': self[0].project_manager.id
            }
        }

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'food.expense'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'food.expense', 'default_res_id': self.id}
        return res

    # ----------------------------------------
    # Business
    # ----------------------------------------

    @api.multi
    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    @api.multi
    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        for expense in self:
            # create the move that will contain the accounting entries
            if expense.sheet_id.id not in move_grouped_by_sheet:
                move = self.env['account.move'].create(expense._prepare_move_values())
                move_grouped_by_sheet[expense.sheet_id.id] = move
            else:
                move = move_grouped_by_sheet[expense.sheet_id.id]
        return move_grouped_by_sheet

    @api.multi
    def _get_expense_account_source(self):
        self.ensure_one()
        if self.account_id:
            account = self.account_id
        elif self.product_id:
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (self.product_id.name))
        else:
            account = self.env['ir.property'].with_context(force_company=self.company_id.id).get('property_account_expense_categ_id', 'product.category')
            if not account:
                raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
        return account

    @api.multi
    def _get_expense_account_destination(self):
        self.ensure_one()
        account_dest = self.env['account.account']
        if self.payment_mode == 'company_account':
            if not self.sheet_id.bank_journal_id.default_credit_account_id:
                raise UserError(_("No credit account found for the %s journal, please configure one.") % (self.sheet_id.bank_journal_id.name))
            account_dest = self.sheet_id.bank_journal_id.default_credit_account_id.id
        else:
            if not self.employee_id.address_home_id:
                raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
            account_dest = self.employee_id.address_home_id.property_account_payable_id.id
        return account_dest

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            # taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.partner_id.id


            # source move line
            amount = expense.total_amount
            amount_currency = False
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = 0
            move_line_src = {
                'name': move_line_name,
                # 'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                # 'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'transportaion_expense_id': expense.id,
                'partner_id': partner_id,
                # 'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount -= move_line_src['debit']
            total_amount_currency -= move_line_src['amount_currency'] or move_line_src['debit']

            # # taxes move lines
            # for tax in taxes['taxes']:
            #     amount = tax['amount']
            #     amount_currency = False
            #     if different_currency:
            #         amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
            #         amount_currency = tax['amount']
            #     move_line_tax_values = {
            #         'name': tax['name'],
            #         # 'quantity': 1,
            #         'debit': amount if amount > 0 else 0,
            #         'credit': -amount if amount < 0 else 0,
            #         'amount_currency': amount_currency if different_currency else 0.0,
            #         'account_id': tax['account_id'] or move_line_src['account_id'],
            #         'tax_line_id': tax['id'],
            #         'transportaion_expense_id': expense.id,
            #         'partner_id': partner_id,
            #         'currency_id': expense.currency_id.id if different_currency else False,
            #     }
            #     total_amount -= amount
            #     total_amount_currency -= move_line_tax_values['amount_currency'] or amount
            #     move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'transportaion_expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'name': expense.name,
                })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.with_context(dont_create_taxes=True).write({
                'line_ids': [(0, 0, line) for line in move_line_values]
            })
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

        # post the moves
        for move in move_group_by_sheet.values():
            move.post()

        return move_group_by_sheet

    
        # post the moves
        for move in move_group_by_sheet.values():
            move.post()

        return move_group_by_sheet

    @api.multi
    def refuse_expense(self, reason):
        self.write({'is_refused': True})
        self.sheet_id.write({'state': 'cancel'})
        self.sheet_id.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                             values={'reason': reason, 'is_sheet': False, 'name': self.name})

    # ----------------------------------------
    # Mail Thread
    # ----------------------------------------

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}

        email_address = email_split(msg_dict.get('email_from', False))[0]

        employee = self.env['hr.employee'].search([
            '|',
            ('work_email', 'ilike', email_address),
            ('user_id.email', 'ilike', email_address)
        ], limit=1)

        expense_description = msg_dict.get('subject', '')

        # Match the first occurence of '[]' in the string and extract the content inside it
        # Example: '[foo] bar (baz)' becomes 'foo'. This is potentially the product code
        # of the product to encode on the expense. If not, take the default product instead
        # which is 'Fixed Cost'
        default_product = self.env.ref('hr_expense.product_product_fixed_cost')
        pattern = '\[([^)]*)\]'
        product_code = re.search(pattern, expense_description)
        if product_code is None:
            product = default_product
        else:
            expense_description = expense_description.replace(product_code.group(), '')
            products = self.env['product.product'].search([('default_code', 'ilike', product_code.group(1))]) or default_product
            product = products.filtered(lambda p: p.default_code == product_code.group(1)) or products[0]
        account = product.product_tmpl_id._get_product_accounts()['expense']

        pattern = '[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
        # Match the last occurence of a float in the string
        # Example: '[foo] 50.3 bar 34.5' becomes '34.5'. This is potentially the price
        # to encode on the expense. If not, take 1.0 instead
        expense_price = re.findall(pattern, expense_description)
        # TODO: International formatting
        if not expense_price:
            price = 1.0
        else:
            price = expense_price[-1][0]
            expense_description = expense_description.replace(price, '')
            try:
                price = float(price)
            except ValueError:
                price = 1.0

        custom_values.update({
            'name': expense_description.strip(),
            'employee_id': employee.id,
            'product_id': product.id,
            # 'product_uom_id': product.uom_id.id,
            # 'tax_ids': [(4, tax.id, False) for tax in product.supplier_taxes_id],
            # 'quantity': 1,
            # 'unit_amount': price,
            'company_id': employee.company_id.id,
        })
        if account:
            custom_values['account_id'] = account.id
        return super(Transportaion_expense_detals, self).message_new(msg_dict, custom_values)



class Transportaion_Sheet(models.Model):
    """
        Here are the rights associated with the expense flow

        Action       Group                   Restriction
        =================================================================================
        Submit      Employee                Only his own
                    Officer                 If he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Approve     Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Post        Anybody                 State = approve and journal_id defined
        Done        Anybody                 State = approve and journal_id defined
        Cancel      Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        =================================================================================
    """
    _name = "transportaion.expense.sheet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Expense Report"
    _order = "accounting_date desc, id desc"

    @api.model
    def _default_journal_id(self):
        journal = self.env.ref('hr_expense.hr_expense_account_journal', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        return journal.id

    @api.model
    def _default_bank_journal_id(self):
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    name = fields.Char('Expense Report Summary', required=True ,  readonly=True , states={'draft': [('readonly', False)], 'submit': [('readonly', False)], 'cancel': [('readonly', False)]})
    expense_line_ids = fields.One2many('transportaion.expense', 'sheet_id', string='Expense Lines', states={'approve': [('readonly', True)], 'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True, help='Expense Report State')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    address_id = fields.Many2one('res.partner', string="Employee Home Address")
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company")], related='expense_line_ids.payment_mode', default='company_account', readonly=True, string="Paid By")
    user_id = fields.Many2one('res.users', 'Manager', copy=False , readonly=True)
    # user_id = fields.Many2one('res.users', 'Manager', readonly=True, copy=False, states={'draft': [('readonly', False)]}, track_visibility='onchange', oldname='responsible_id')
    total_amount = fields.Monetary('Total Amount', currency_field='currency_id', compute='_compute_amount', store=True, digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_journal_id, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_bank_journal_id, help="The payment method used when the expense is paid by the company.")
    accounting_date = fields.Date("Date")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False)
    department_id = fields.Many2one('hr.department', string='Department', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    is_multiple_currency = fields.Boolean("Handle lines with different currencies", compute='_compute_is_multiple_currency')
    can_reset = fields.Boolean('Can Reset', compute='_compute_can_reset')



    @api.depends('expense_line_ids.total_amount_company')
    def _compute_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_company'))

    @api.multi
    def _compute_attachment_number(self):
        for sheet in self:
            sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))

    @api.depends('expense_line_ids.currency_id')
    def _compute_is_multiple_currency(self):
        for sheet in self:
            sheet.is_multiple_currency = len(sheet.expense_line_ids.mapped('currency_id')) > 1

    @api.multi
    def _compute_can_reset(self):
        is_expense_user = self.user_has_groups('hr_expense.group_hr_expense_user')
        for sheet in self:
            sheet.can_reset = is_expense_user if is_expense_user else sheet.employee_id.user_id == self.env.user

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.address_id = rec.employee_id.sudo().address_home_id
            rec.department_id = rec.employee_id.department_id
            if not rec.user_id :
                rec.user_id = rec.expense_line_ids.project_manager.id
        # self.user_id = self.employee_id.expense_manager_id or self.employee_id.parent_id.user_id

    @api.multi
    @api.constrains('expense_line_ids')
    def _check_payment_mode(self):
        for sheet in self:
            expense_lines = sheet.mapped('expense_line_ids')
            if expense_lines and any(expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
                raise ValidationError(_("Expenses must be paid by the same entity (Company or employee)."))

    # @api.constrains('expense_line_ids', 'employee_id')
    # def _check_employee(self):
    #     for sheet in self:
    #         employee_ids = sheet.expense_line_ids.mapped('employee_id')
    #         if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != sheet.employee_id):
    #             raise ValidationError(_('You cannot add expenses of another employee.'))

    @api.model
    def create(self, vals):
        sheet = super(Transportaion_Sheet, self.with_context(mail_create_nosubscribe=True)).create(vals)
        sheet.activity_update()
        return sheet

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['post', 'done']:
                raise UserError(_('You cannot delete a posted or paid expense.'))
        super(Transportaion_Sheet, self).unlink()

    # --------------------------------------------
    # Mail Thread
    # --------------------------------------------

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'approve':
            return 'hr_expense.mt_expense_approved'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_expense.mt_expense_refused'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_expense.mt_expense_paid'
        return super(Transportaion_Sheet, self)._track_subtype(init_values)

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(Transportaion_Sheet, self)._message_auto_subscribe_followers(updated_values, subtype_ids)
        if updated_values.get('employee_id'):
            employee = self.env['hr.employee'].browse(updated_values['employee_id'])
            if employee.user_id:
                res.append((employee.user_id.partner_id.id, subtype_ids, False))
        return res

    # --------------------------------------------
    # Actions
    # --------------------------------------------

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    # @api.multi
    # def action_sheet_move_create(self):
    #     if any(sheet.state != 'approve' for sheet in self):
    #         raise UserError(_("You can only generate accounting entry for approved expense(s)."))

    #     if any(not sheet.journal_id for sheet in self):
    #         raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

    #     expense_line_ids = self.mapped('expense_line_ids')\
    #         .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
    #     res = expense_line_ids.action_move_create()

    #     if not self.accounting_date:
    #         self.accounting_date = self.account_move_id.date

    #     if self.payment_mode == 'own_account' and expense_line_ids:
    #         self.write({'state': 'post'})
    #     else:
    #         self.write({'state': 'done'})
    #     self.activity_update()
    #     return res

    @api.multi
    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'transportaion.expense'), ('res_id', 'in', self.expense_line_ids.ids)]
        res['context'] = {
            'default_res_model': 'transportaion.expense.sheet',
            'default_res_id': self.ids,
            'create': False,
            'edit': False,
        }
        return res

    # --------------------------------------------
    # Business
    # --------------------------------------------

    @api.multi
    def set_to_paid(self):
        self.write({'state': 'done'})

    @api.multi
    def action_submit_sheet(self):
        self.write({'state': 'submit'})
        self.activity_update()

    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'approve', 'user_id': responsible_id})
        self.activity_update()

    @api.multi
    def paid_expense_sheets(self):
        self.write({'state': 'done'})

    @api.multi
    def refuse_sheet(self, reason):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot refuse your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only refuse your department expenses"))

        self.write({'state': 'cancel'})
        for sheet in self:
            sheet.message_post_with_view('hr_expense.hr_expense_template_refuse_reason', values={'reason': reason, 'is_sheet': True, 'name': self.name})
        self.activity_update()

    @api.multi
    def reset_expense_sheets(self):
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        self.mapped('expense_line_ids').write({'is_refused': False})
        self.write({'state': 'draft'})
        self.activity_update()
        return True

    def _get_responsible_for_approval(self):
        if self.user_id:
            return self.user_id
        elif self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.department_id.manager_id.user_id:
            return self.employee_id.department_id.manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'approve').activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(['hr_expense.mail_act_expense_approval'])


 
    



# Start Petty Cash 
    
class Petty_Cash_detals(models.Model):
    _name = 'petty.cash.expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Petty Cash Expense"
    _order = "date desc, id desc"

    # @api.model
    # def _default_employee_id(self):
    #     return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    # @api.model
    # def _default_product_uom_id(self):
    #     return self.env['uom.uom'].search([], limit=1, order='id')

    @api.model
    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    @api.model
    def _get_employee_id_domain(self):

        res= [('id', '=', 0)] # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_manager') or self.user_has_groups('account.group_account_user'):
            res = [] # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_user') and self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = ['|', '|', ('department_id.manager_id.id', '=', employee.id),
                   ('parent_id.id', '=', employee.id), ('expense_manager_id.id', '=', employee.id)]
        elif self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = [('id', '=', employee.id)]
        return res

    # product_id_food_st = fields.Many2one('res.config.settings', string='Product', readonly=True)
    name = fields.Char('Description', readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    date = fields.Date(readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=fields.Date.context_today, string="Date")
    employee_id = fields.Many2one('res.partner', string="Partner",readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    employees_id = fields.Many2one('hr.employee', string="Employee",compute='_compute_employy')
    product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)])
    # product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_product_uom_id)
    unit_amount = fields.Float("Unit Price", readonly=True, currency_field='currency_id', required=True,states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    quantity = fields.Float( string='Quantity' ,   readonly=True, compute='_quantity_one')
    tax_ids = fields.Many2many('account.tax','pettycash_expense_id', 'tax_id', string='VAT',  readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    untaxed_amount = fields.Float("Net Amount", store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    total_amount = fields.Monetary("Gross Amount", compute='_compute_amount', store=True, currency_field='currency_id', digits=dp.get_precision('Account'))
    company_currency_id = fields.Many2one('res.currency', string="Report Company Currency", related='sheet_id.currency_id', store=True, readonly=False)
    total_amount_company = fields.Monetary("Total (Company Currency)", compute='_compute_total_amount_company', store=True, currency_field='company_currency_id', digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, oldname='analytic_account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, default=_default_account_id, help="An expense account is expected")
    description = fields.Text('Notes...', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='own_account', readonly=True  , string="Paid By")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the Food expense.")
    sheet_id = fields.Many2one('petty.cash.sheet', string="Petty Cash Expense Report", readonly=True, copy=False)
    reference = fields.Char("Bill Reference" , readonly=True , required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    is_refused = fields.Boolean("Explicitely Refused by manager or acccountant", readonly=True, copy=False)
    # by Fouad
    # meal_type = fields.Many2one('meal.type', string='Meal Type', required=True,  change_default=True, track_visibility='always', help="You can find Type Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    
    # meal_type = fields.Selection([
    #     ('breakfast', 'Breakfast'),
    #     ('dinner', 'Dinner'),
    # ],  string='Meal Type', copy=False, index=True, store=True, help="Status of the meal.")
    # account = fields.Many2one('account', string='Account', required=True,  change_default=True, track_visibility='always', help="You can find Type Reference.")

    # account =  fields.Selection([
    #     ('one', '300241 Food Exp., Water & Refreshment'),
    #     ('tow', 'Tow'),
    #     ('three', 'Three'),
    # ],  string='Account', copy=False, index=True, store=True, default="one")
    project_id = fields.Many2one('project.project', string='Project', required=True , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    # partner_id = fields.Many2one('res.partner', string='Vendor', required=True,  change_default=True, track_visibility='always', help="You can find a vendor by its Name, TIN, Email or Internal Reference." , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    project_manager = fields.Many2one('res.users',string="Project Manager")
    # food_seq = fields.Char('Sequnce', required=True, copy=False, readonly=True, default='New')
    # product_id_food = fields.Char("product" , readonly=True , required=True, related ='product_id_food_sting.product_id')

    # product_id_food = fields.Many2one('product.food', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})


    # @api.model
    # def default_manager(self):
    # manager = self.env.user.company_id.manager_company.name
    # return managere
    # can_project = fields.Char('Can project', compute='_compute_can_project')

    @api.onchange('project_id')
    def _compute_man_project(self):
        for rec in self:
            rec.project_manager = rec.project_id.user_id.id
            rec.analytic_account_id = rec.project_id.analytic_account_id.id


    @api.model
    @api.depends('employees_id')
    def _compute_employy(self):
        com = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        for rec in self:
            rec.employees_id = com.id


    @api.multi
    def _quantity_one(self):
        for rec in self:
            rec.quantity = 1.00

    # @api.model
    # def _compute_can_project(self):
    #     for rec in self:
    #         rec.can_project = rec.project_id.name


    # @api.one
    # @api.constrains('quantity')
    # def _check_values(self):
    #     if self.quantity == 0.0 :
    #         raise Warning(_('Quantity should not be zero.'))

    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.project_id.user_id
    #     for rec in self:
    #         if rec.sheet_id.user_id == is_expense_user :
    #             rec.can_project = True



    # @api.model
    # def create(self, vals):
    #     if vals.get('food_seq', 'New') == 'New':
    #         vals['food_seq'] = self.env['ir.sequence'].next_by_code('food.expense.sequence') or 'New'   


    #     result = super(food_expense_detals, self).create(vals)       

    #     return result



    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

    @api.depends('date', 'total_amount', 'company_currency_id')
    def _compute_total_amount_company(self):
        for expense in self:
            amount = 0
            if expense.company_currency_id:
                date_expense = expense.date
                amount = expense.currency_id._convert(
                    expense.total_amount, expense.company_currency_id,
                    expense.company_id, date_expense or fields.Date.today())
            expense.total_amount_company = amount

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'petty.cash.expense'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            # self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    # @api.onchange('product_uom_id')
    # def _onchange_product_uom_id(self):
    #     if self.product_id and self.product_uom_id.category_id != self.product_id.uom_id.category_id:
    #         raise UserError(_('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.'))

    # ----------------------------------------
    # ORM Overrides
    # ----------------------------------------

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['done', 'approved']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
        return super(Petty_Cash_detals, self).unlink()

    @api.model
    def get_empty_list_help(self, help_message):
        if help_message and "o_view_nocontent_smiling_face" not in help_message:
            use_mailgateway = self.env['ir.config_parameter'].sudo().get_param('hr_expense.use_mailgateway')
            alias_record = use_mailgateway and self.env.ref('hr_expense.mail_alias_expense') or False
            if alias_record and alias_record.alias_domain and alias_record.alias_name:
                link = "<a id='o_mail_test' href='mailto:%(email)s?subject=Lunch%%20with%%20customer%%3A%%20%%2412.32'>%(email)s</a>" % {
                    'email': '%s@%s' % (alias_record.alias_name, alias_record.alias_domain)
                }
                return '<p class="o_view_nocontent_smiling_face">%s</p><p class="oe_view_nocontent_alias">%s</p>' % (
                    _('Add a new expense,'),
                    _('or send receipts by email to %s.') % (link),)
        return super(Petty_Cash_detals, self).get_empty_list_help(help_message)

    # ----------------------------------------
    # Actions
    # ----------------------------------------

    @api.multi
    def action_view_sheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'petty.cash.sheet',
            'target': 'current',
            'res_id': self.sheet_id.id
        }

    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different partners in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'petty.cash.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_name': todo[0].name if len(todo) == 1 else '',
                'default_user_id': self[0].project_manager.id,
                'default_employees_id': self[0].employees_id.id
                
            }
        }

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'petty.cash.expense'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'petty.cash.expense', 'default_res_id': self.id}
        return res

    # ----------------------------------------
    # Business
    # ----------------------------------------

    @api.multi
    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    @api.multi
    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        for expense in self:
            # create the move that will contain the accounting entries
            if expense.sheet_id.id not in move_grouped_by_sheet:
                move = self.env['account.move'].create(expense._prepare_move_values())
                move_grouped_by_sheet[expense.sheet_id.id] = move
            else:
                move = move_grouped_by_sheet[expense.sheet_id.id]
        return move_grouped_by_sheet

    @api.multi
    def _get_expense_account_source(self):
        self.ensure_one()
        if self.account_id:
            account = self.account_id
        elif self.product_id:
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (self.product_id.name))
        else:
            account = self.env['ir.property'].with_context(force_company=self.company_id.id).get('property_account_expense_categ_id', 'product.category')
            if not account:
                raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
        return account

    @api.multi
    def _get_expense_account_destination(self):
        self.ensure_one()
        account_dest = self.env['account.account']
        if self.payment_mode == 'company_account':
            if not self.sheet_id.bank_journal_id.default_credit_account_id:
                raise UserError(_("No credit account found for the %s journal, please configure one.") % (self.sheet_id.bank_journal_id.name))
            account_dest = self.sheet_id.bank_journal_id.default_credit_account_id.id
        else:
            if not self.employee_id.property_account_payable_id:
                raise UserError(_("No Payable account found for the partner %s, please configure one.") % (self.employee_id.name))
            account_dest = self.employee_id.property_account_payable_id.id
        return account_dest

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, 1, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.commercial_partner_id.id

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                # 'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'pettycash_expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount -= move_line_src['debit']
            total_amount_currency -= move_line_src['amount_currency'] or move_line_src['debit']

            # taxes move lines
            for tax in taxes['taxes']:
                amount = tax['amount']
                amount_currency = False
                if different_currency:
                    amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                    amount_currency = tax['amount']
                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                    'amount_currency': amount_currency if different_currency else 0.0,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_line_id': tax['id'],
                    'pettycash_expense_id': expense.id,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id if different_currency else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'pettycash_expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'name': expense.name,
                })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.with_context(dont_create_taxes=True).write({
                'line_ids': [(0, 0, line) for line in move_line_values]
            })
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

        # post the moves
        for move in move_group_by_sheet.values():
            move.post()

        return move_group_by_sheet

    

    @api.multi
    def refuse_expense(self, reason):
        self.write({'is_refused': True})
        self.sheet_id.write({'state': 'cancel'})
        self.sheet_id.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                             values={'reason': reason, 'is_sheet': False, 'name': self.name})

    # ----------------------------------------
    # Mail Thread
    # ----------------------------------------

    # @api.model
    # def message_new(self, msg_dict, custom_values=None):
    #     if custom_values is None:
    #         custom_values = {}

    #     email_address = email_split(msg_dict.get('email_from', False))[0]

    #     employee = self.env['hr.employee'].search([
    #         '|',
    #         ('work_email', 'ilike', email_address),
    #         ('user_id.email', 'ilike', email_address)
    #     ], limit=1)

    #     expense_description = msg_dict.get('subject', '')

    #     # Match the first occurence of '[]' in the string and extract the content inside it
    #     # Example: '[foo] bar (baz)' becomes 'foo'. This is potentially the product code
    #     # of the product to encode on the expense. If not, take the default product instead
    #     # which is 'Fixed Cost'
    #     default_product = self.env.ref('hr_expense.product_product_fixed_cost')
    #     pattern = '\[([^)]*)\]'
    #     product_code = re.search(pattern, expense_description)
    #     if product_code is None:
    #         product = default_product
    #     else:
    #         expense_description = expense_description.replace(product_code.group(), '')
    #         products = self.env['product.product'].search([('default_code', 'ilike', product_code.group(1))]) or default_product
    #         product = products.filtered(lambda p: p.default_code == product_code.group(1)) or products[0]
    #     account = product.product_tmpl_id._get_product_accounts()['expense']

    #     pattern = '[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
    #     # Match the last occurence of a float in the string
    #     # Example: '[foo] 50.3 bar 34.5' becomes '34.5'. This is potentially the price
    #     # to encode on the expense. If not, take 1.0 instead
    #     expense_price = re.findall(pattern, expense_description)
    #     # TODO: International formatting
    #     if not expense_price:
    #         price = 1.0
    #     else:
    #         price = expense_price[-1][0]
    #         expense_description = expense_description.replace(price, '')
    #         try:
    #             price = float(price)
    #         except ValueError:
    #             price = 1.0

    #     custom_values.update({
    #         'name': expense_description.strip(),
    #         'employee_id': employee.id,
    #         'product_id': product.id,
    #         # 'product_uom_id': product.uom_id.id,
    #         'tax_ids': [(4, tax.id, False) for tax in product.supplier_taxes_id],
    #         'quantity': 1,
    #         'unit_amount': price,
    #         'company_id': employee.company_id.id,
    #     })
    #     if account:
    #         custom_values['account_id'] = account.id
    #     return super(Petty_Cash_detals, self).message_new(msg_dict, custom_values)



class Petty_Cash_Sheet(models.Model):
    """
        Here are the rights associated with the expense flow

        Action       Group                   Restriction
        =================================================================================
        Submit      Employee                Only his own
                    Officer                 If he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Approve     Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Post        Anybody                 State = approve and journal_id defined
        Done        Anybody                 State = approve and journal_id defined
        Cancel      Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        =================================================================================
    """
    _name = "petty.cash.sheet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Expense Report"
    _order = "accounting_date desc, id desc"

    @api.model
    def _default_journal_id(self):
        journal = self.env.ref('hr_expense.hr_expense_account_journal', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        return journal.id

    @api.model
    def _default_bank_journal_id(self):
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    name = fields.Char('Expense Report Summary', required=True , readonly=True , states={'draft': [('readonly', False)], 'submit': [('readonly', False)], 'cancel': [('readonly', False)]})
    expense_line_ids = fields.One2many('petty.cash.expense', 'sheet_id', string='Expense Lines', states={'approve': [('readonly', True)], 'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True, help='Expense Report State')
    employee_id = fields.Many2one('res.partner', string="Partner", required=True, readonly=True, states={'draft': [('readonly', False)]})
    employees_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    address_id = fields.Char(string="Employee Home Address")
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company")], related='expense_line_ids.payment_mode', default='company_account', readonly=True, string="Paid By")
    user_id = fields.Many2one('res.users', 'Manager', copy=False , readonly=True)
    # user_id = fields.Many2one('res.users', 'Manager', related='expense_line_ids.project_id.user_id' , readonly=True, copy=False, states={'draft': [('readonly', False)]}, track_visibility='onchange', oldname='responsible_id')
    total_amount = fields.Monetary('Total Amount', currency_field='currency_id', compute='_compute_amount', store=True, digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_journal_id, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_bank_journal_id, help="The payment method used when the expense is paid by the company.")
    accounting_date = fields.Date("Date")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False)
    department_id = fields.Many2one('hr.department', string='Department', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    is_multiple_currency = fields.Boolean("Handle lines with different currencies", compute='_compute_is_multiple_currency')
    # can_reset = fields.Boolean('Can Reset', compute='_compute_can_reset')

    
    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.user_id.id
    #     for rec in self:
    #         if rec.expense_line_ids.project_id.user_id.id == is_expense_user :
    #             rec.can_project = True

     # @api.onchange('user_id','expense_line_ids')
    # def onchange_values(self):
    #     return {'domain': {'expense_line_ids': {[ ('user_id', '=', self.user_id.id)]}}

    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.user_id
    #     for rec in self:
    #         if rec.expense_line_ids.project_id.user_id == is_expense_user :
    #             rec.can_project = True



    @api.depends('expense_line_ids.total_amount_company')
    def _compute_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_company'))

    @api.multi
    def _compute_attachment_number(self):
        for sheet in self:
            sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))

    @api.depends('expense_line_ids.currency_id')
    def _compute_is_multiple_currency(self):
        for sheet in self:
            sheet.is_multiple_currency = len(sheet.expense_line_ids.mapped('currency_id')) > 1

    # @api.multi
    # def _compute_can_reset(self):
    #     is_expense_user = self.user_has_groups('hr_expense.group_hr_expense_user')
    #     for sheet in self:
    #         sheet.can_reset = is_expense_user if is_expense_user else sheet.employee_id.user_id == self.env.user

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.address_id = rec.employee_id.street
            # rec.department_id = rec.employee_id.department_id
            if not rec.user_id :
                rec.user_id = rec.expense_line_ids.project_manager.id
        # self.user_id = self.employee_id.expense_manager_id or self.employee_id.parent_id.user_id

    @api.multi
    @api.constrains('expense_line_ids')
    def _check_payment_mode(self):
        for sheet in self:
            expense_lines = sheet.mapped('expense_line_ids')
            if expense_lines and any(expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
                raise ValidationError(_("Expenses must be paid by the same entity (Company or partner)."))

    # @api.constrains('expense_line_ids', 'employee_id')
    # def _check_employee(self):
    #     for sheet in self:
    #         employee_ids = sheet.expense_line_ids.mapped('employee_id')
    #         if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != sheet.employee_id):
    #             raise ValidationError(_('You cannot add expenses of another employee.'))

    @api.model
    def create(self, vals):
        sheet = super(Petty_Cash_Sheet, self.with_context(mail_create_nosubscribe=True)).create(vals)
        sheet.activity_update()
        return sheet


    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['post', 'done']:
                raise UserError(_('You cannot delete a posted or paid expense.'))
        super(Petty_Cash_Sheet, self).unlink()

    # --------------------------------------------
    # Mail Thread
    # --------------------------------------------

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'approve':
            return 'hr_expense.mt_expense_approved'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_expense.mt_expense_refused'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_expense.mt_expense_paid'
        return super(Petty_Cash_Sheet, self)._track_subtype(init_values)

    # def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
    #     res = super(Petty_Cash_Sheet, self)._message_auto_subscribe_followers(updated_values, subtype_ids)
    #     if updated_values.get('employee_id'):
    #         employee = self.env['hr.employee'].browse(updated_values['employee_id'])
    #         if employee.user_id:
    #             res.append((employee.user_id.partner_id.id, subtype_ids, False))
    #     return res

    # --------------------------------------------
    # Actions
    # --------------------------------------------


    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    # @api.multi
    # def action_sheet_move_create(self):
    #     if any(sheet.state != 'approve' for sheet in self):
    #         raise UserError(_("You can only generate accounting entry for approved expense(s)."))

    #     if any(not sheet.journal_id for sheet in self):
    #         raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

    #     expense_line_ids = self.mapped('expense_line_ids')\
    #         .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
    #     res = expense_line_ids.action_move_create()

    #     if not self.accounting_date:
    #         self.accounting_date = self.account_move_id.date

    #     if self.payment_mode == 'own_account' and expense_line_ids:
    #         self.write({'state': 'post'})
    #     else:
    #         self.write({'state': 'done'})
    #     self.activity_update()
    #     return res

    @api.multi
    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'petty.cash.expense'), ('res_id', 'in', self.expense_line_ids.ids)]
        res['context'] = {
            'default_res_model': 'petty.cash.sheet',
            'default_res_id': self.ids,
            'create': False,
            'edit': False,
        }
        return res

    # --------------------------------------------
    # Business
    # --------------------------------------------

    @api.multi
    def set_to_paid(self):
        self.write({'state': 'done'})

    @api.multi
    def action_submit_sheet(self):
        self.write({'state': 'submit'})
        self.activity_update()

    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employees_id.parent_id.user_id | self.employees_id.department_id.manager_id.user_id

            if self.employees_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'approve', 'user_id': responsible_id})
        self.activity_update()

    @api.multi
    def paid_expense_sheets(self):
        self.write({'state': 'done'})

    @api.multi
    def refuse_sheet(self, reason):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employees_id.parent_id.user_id | self.employees_id.department_id.manager_id.user_id

            if self.employees_id.user_id == self.env.user:
                raise UserError(_("You cannot refuse your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only refuse your department expenses"))

        self.write({'state': 'cancel'})
        for sheet in self:
            sheet.message_post_with_view('hr_expense.hr_expense_template_refuse_reason', values={'reason': reason, 'is_sheet': True, 'name': self.name})
        self.activity_update()

    @api.multi
    def reset_expense_sheets(self):
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        self.mapped('expense_line_ids').write({'is_refused': False})
        self.write({'state': 'draft'})
        self.activity_update()
        return True

    def _get_responsible_for_approval(self):
        if self.user_id:
            return self.user_id
        elif self.employees_id.parent_id.user_id:
            return self.employees_id.parent_id.user_id
        elif self.employees_id.department_id.manager_id.user_id:
            return self.employees_id.department_id.manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'approve').activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(['hr_expense.mail_act_expense_approval'])




# Start Labour  
    
class Labour_detals(models.Model):
    _name = 'labour.expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Labour Expense"
    _order = "date desc, id desc"

    @api.model
    def _default_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    # @api.model
    # def _default_product_uom_id(self):
    #     return self.env['uom.uom'].search([], limit=1, order='id')

    @api.model
    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    @api.model
    def _get_employee_id_domain(self):

        res= [('id', '=', 0)] # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_manager') or self.user_has_groups('account.group_account_user'):
            res = [] # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_user') and self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = ['|', '|', ('department_id.manager_id.id', '=', employee.id),
                   ('parent_id.id', '=', employee.id), ('expense_manager_id.id', '=', employee.id)]
        elif self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            res = [('id', '=', employee.id)]
        return res

    # product_id_food_st = fields.Many2one('res.config.settings', string='Product', readonly=True)
    name = fields.Char('Description', readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    date = fields.Date(readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=fields.Date.context_today, string="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", compute='_compute_employy')
    # product_id = fields.Many2one('product.product', string='Product', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)])
    # product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_product_uom_id)
    # unit_amount = fields.Float("Unit Price", readonly=True, currency_field='currency_id', required=True,states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    quantity = fields.Float( string='Quantity' ,   readonly=True, compute='_quantity_one')
    tax_ids = fields.Many2many('account.tax','pettycash_expense_id', 'tax_id', string='VAT',  readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    untaxed_amount = fields.Float("Net Amount", store=True,  digits=dp.get_precision('Account'))
    # total_amount = fields.Monetary("Gross Amount",  store=True, currency_field='currency_id', digits=dp.get_precision('Account'))
    company_currency_id = fields.Many2one('res.currency', string="Report Company Currency", related='sheet_id.currency_id', store=True, readonly=False)
    total_amount_company = fields.Monetary("Total (Company Currency)", compute='_compute_total_amount_company', store=True, currency_field='company_currency_id', digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, oldname='analytic_account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, default=_default_account_id, help="An expense account is expected")
    description = fields.Text('Notes...', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', readonly=True  , string="Paid By")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the Food expense.")
    sheet_id = fields.Many2one('labour.sheet', string="Labour Expense Report", readonly=True, copy=False)
    reference = fields.Char("Bill Reference" , readonly=True , required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    is_refused = fields.Boolean("Explicitely Refused by manager or acccountant", readonly=True, copy=False)
    
    # by Fouad----------------------------------------------------------------

    labour_type = fields.Many2one('labour.type', string='Type', required=True,  change_default=True, track_visibility='always', help="You can find Type Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    project_id = fields.Many2one('project.project', string='Project', required=True , readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    project_manager = fields.Many2one('res.users',string="Project Manager")
    partner_id = fields.Many2one('res.partner', string='Supplier Name' , required=True,  change_default=True, track_visibility='always', help="You can find a vendor by its Name, TIN, Email or Internal Reference.", readonly=True , states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    no_of_helpers = fields.Integer( string='Number of Helpers', readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    time_in = fields.Float(string='Time in', readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    time_out = fields.Float(string='Time out',  readonly=True, required=True,  states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    break_hour = fields.Float(string='Break hour',  readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    travelling_hours = fields.Float(string='Travelling hours',  readonly=True, required=True,compute='_check_time',  states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    net_hours = fields.Float(string='Net hours',  readonly=True,compute='_compute_net_hours')
    rate_per_hour = fields.Float(string='Rate per hour',  readonly=True, required=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})
    total_hours = fields.Float(string='Total hours',  readonly=True , compute='_compute_total_hours')
    total_amount = fields.Monetary("Amount(AED)",  compute='_compute_total_amount', store=True, currency_field='currency_id', digits=dp.get_precision('Account'))
    # amount = fields.Float(string='Amount (AED)',  readonly=True)


    @api.multi
    @api.depends('time_in','time_out')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = rec.time_out - rec.time_in 


    @api.multi
    @api.depends('total_hours','break_hour','travelling_hours')
    def _compute_net_hours(self):
        for rec in self:
            rec.net_hours = (rec.total_hours - rec.break_hour) + rec.travelling_hours 


    @api.multi
    @api.depends('rate_per_hour','net_hours','no_of_helpers')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.rate_per_hour * rec.net_hours * rec.no_of_helpers   


    @api.one
    @api.constrains('time_in','time_out','break_hour','travelling_hours')
    def _check_time(self):
        if self.time_in == 0.0 :
            raise Warning(_('Time in should not be zero.'))
        if self.time_in > 24.0 or self.time_in < 0.0:
            raise Warning(_('Time in Must be in rang (1.00 - 24.00)'))
        if self.time_out == 0.0 :
            raise Warning(_('Time out should not be zero.'))
        if self.time_out > 24.0 or self.time_out < 0.0:
            raise Warning(_('Time out Must be in rang (1.00 - 24.00)'))
        
        if self.break_hour > 24.0 or self.time_out < 0.0:
            raise Warning(_('Break hour Must be in rang (1.00 - 24.00)'))
        
        if self.travelling_hours > 24.0 or self.time_out < 0.0:
            raise Warning(_('Travelling hours Must be in rang (1.00 - 24.00)'))
    


    @api.model
    @api.depends('employee_id')
    def _compute_employy(self):
        com = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        for rec in self:
            rec.employee_id = com.id


    @api.multi
    def _quantity_one(self):
        for rec in self:
            rec.quantity = 1.00

    
    
    @api.one
    @api.constrains('no_of_helpers')
    def _check_values(self):
        if self.no_of_helpers == 0.0 :
            raise Warning(_('Number of Helpers should not be zero.'))

    @api.one
    @api.constrains('rate_per_hour')
    def _check_values(self):
        if self.rate_per_hour == 0.0 :
            raise Warning(_('Rate per hour should not be zero.'))



    # @api.model
    # def default_manager(self):
    # manager = self.env.user.company_id.manager_company.name
    # return managere
    # can_project = fields.Char('Can project', compute='_compute_can_project')

    # must back-----------------------------------------------------------------

    # @api.onchange('project_id')
    # def _compute_man_project(self):
    #     for rec in self:
    #         rec.project_manager = rec.project_id.user_id.id
    #         rec.analytic_account_id = rec.project_id.analytic_account_id.id

    #-----------------------------------------------------------------------------



    # @api.model
    # def _compute_can_project(self):
    #     for rec in self:
    #         rec.can_project = rec.project_id.name


    # @api.one
    # @api.constrains('quantity')
    # def _check_values(self):
    #     if self.quantity == 0.0 :
    #         raise Warning(_('Quantity should not be zero.'))

    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.project_id.user_id
    #     for rec in self:
    #         if rec.sheet_id.user_id == is_expense_user :
    #             rec.can_project = True



    # @api.model
    # def create(self, vals):
    #     if vals.get('food_seq', 'New') == 'New':
    #         vals['food_seq'] = self.env['ir.sequence'].next_by_code('food.expense.sequence') or 'New'   


    #     result = super(food_expense_detals, self).create(vals)       

    #     return result





    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

    @api.depends('quantity', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

    @api.depends('date', 'total_amount', 'company_currency_id')
    def _compute_total_amount_company(self):
        for expense in self:
            amount = 0
            if expense.company_currency_id:
                date_expense = expense.date
                amount = expense.currency_id._convert(
                    expense.total_amount, expense.company_currency_id,
                    expense.company_id, date_expense or fields.Date.today())
            expense.total_amount_company = amount

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'labour.expense'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            # self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    # @api.onchange('product_uom_id')
    # def _onchange_product_uom_id(self):
    #     if self.product_id and self.product_uom_id.category_id != self.product_id.uom_id.category_id:
    #         raise UserError(_('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.'))

    # ----------------------------------------
    # ORM Overrides
    # ----------------------------------------

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['done', 'approved']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
        return super(Labour_detals, self).unlink()

    @api.model
    def get_empty_list_help(self, help_message):
        if help_message and "o_view_nocontent_smiling_face" not in help_message:
            use_mailgateway = self.env['ir.config_parameter'].sudo().get_param('hr_expense.use_mailgateway')
            alias_record = use_mailgateway and self.env.ref('hr_expense.mail_alias_expense') or False
            if alias_record and alias_record.alias_domain and alias_record.alias_name:
                link = "<a id='o_mail_test' href='mailto:%(email)s?subject=Lunch%%20with%%20customer%%3A%%20%%2412.32'>%(email)s</a>" % {
                    'email': '%s@%s' % (alias_record.alias_name, alias_record.alias_domain)
                }
                return '<p class="o_view_nocontent_smiling_face">%s</p><p class="oe_view_nocontent_alias">%s</p>' % (
                    _('Add a new expense,'),
                    _('or send receipts by email to %s.') % (link),)
        return super(Labour_detals, self).get_empty_list_help(help_message)

    # ----------------------------------------
    # Actions
    # ----------------------------------------

    @api.multi
    def action_view_sheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'labour.sheet',
            'target': 'current',
            'res_id': self.sheet_id.id
        }

    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'labour.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_name': todo[0].name if len(todo) == 1 else '',
                'default_user_id': self[0].project_manager.id
                
            }
        }

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'labour.expense'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'labour.expense', 'default_res_id': self.id}
        return res

    # ----------------------------------------
    # Business
    # ----------------------------------------

    @api.multi
    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    @api.multi
    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        for expense in self:
            # create the move that will contain the accounting entries
            if expense.sheet_id.id not in move_grouped_by_sheet:
                move = self.env['account.move'].create(expense._prepare_move_values())
                move_grouped_by_sheet[expense.sheet_id.id] = move
            else:
                move = move_grouped_by_sheet[expense.sheet_id.id]
        return move_grouped_by_sheet

    @api.multi
    def _get_expense_account_source(self):
        self.ensure_one()
        if self.account_id:
            account = self.account_id
        elif self.product_id:
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (self.product_id.name))
        else:
            account = self.env['ir.property'].with_context(force_company=self.company_id.id).get('property_account_expense_categ_id', 'product.category')
            if not account:
                raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
        return account

    @api.multi
    def _get_expense_account_destination(self):
        self.ensure_one()
        account_dest = self.env['account.account']
        if self.payment_mode == 'company_account':
            if not self.sheet_id.bank_journal_id.default_credit_account_id:
                raise UserError(_("No credit account found for the %s journal, please configure one.") % (self.sheet_id.bank_journal_id.name))
            account_dest = self.sheet_id.bank_journal_id.default_credit_account_id.id
        else:
            if not self.employee_id.address_home_id:
                raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
            account_dest = self.employee_id.address_home_id.property_account_payable_id.id
        return account_dest

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            # taxes = expense.tax_ids.with_context(round=True).compute_all(expense.currency_id, expense.quantity)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.partner_id.id

            # source move line
            amount = expense.total_amount
            amount_currency = amount
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = amount
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                # 'product_id': expense.product_id.id,
                # 'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'labour_expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount -= move_line_src['debit']
            total_amount_currency -= move_line_src['amount_currency'] or move_line_src['debit']

            # # taxes move lines
            # for tax in taxes['taxes']:
            #     amount = tax['amount']
            #     amount_currency = False
            #     if different_currency:
            #         amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
            #         amount_currency = tax['amount']
            #     move_line_tax_values = {
            #         'name': tax['name'],
            #         'quantity': 1,
            #         'debit': amount if amount > 0 else 0,
            #         'credit': -amount if amount < 0 else 0,
            #         'amount_currency': amount_currency if different_currency else 0.0,
            #         'account_id': tax['account_id'] or move_line_src['account_id'],
            #         'tax_line_id': tax['id'],
            #         'labour_expense_id': expense.id,
            #         'partner_id': partner_id,
            #         'currency_id': expense.currency_id.id if different_currency else False,
            #     }
            #     total_amount -= amount
            #     total_amount_currency -= move_line_tax_values['amount_currency'] or amount
            #     move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'labour_expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'name': expense.name,
                })
                move_line_dst['payment_id'] = payment.id

            # link move lines to move, and move to expense sheet
            move.with_context(dont_create_taxes=True).write({
                'line_ids': [(0, 0, line) for line in move_line_values]
            })
            expense.sheet_id.write({'account_move_id': move.id})

            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

        # post the moves
        for move in move_group_by_sheet.values():
            move.post()

        return move_group_by_sheet

    

    @api.multi
    def refuse_expense(self, reason):
        self.write({'is_refused': True})
        self.sheet_id.write({'state': 'cancel'})
        self.sheet_id.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                             values={'reason': reason, 'is_sheet': False, 'name': self.name})

    # ----------------------------------------
    # Mail Thread
    # ----------------------------------------

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}

        email_address = email_split(msg_dict.get('email_from', False))[0]

        employee = self.env['hr.employee'].search([
            '|',
            ('work_email', 'ilike', email_address),
            ('user_id.email', 'ilike', email_address)
        ], limit=1)

        expense_description = msg_dict.get('subject', '')

        # Match the first occurence of '[]' in the string and extract the content inside it
        # Example: '[foo] bar (baz)' becomes 'foo'. This is potentially the product code
        # of the product to encode on the expense. If not, take the default product instead
        # which is 'Fixed Cost'
        default_product = self.env.ref('hr_expense.product_product_fixed_cost')
        pattern = '\[([^)]*)\]'
        product_code = re.search(pattern, expense_description)
        if product_code is None:
            product = default_product
        else:
            expense_description = expense_description.replace(product_code.group(), '')
            products = self.env['product.product'].search([('default_code', 'ilike', product_code.group(1))]) or default_product
            product = products.filtered(lambda p: p.default_code == product_code.group(1)) or products[0]
        account = product.product_tmpl_id._get_product_accounts()['expense']

        pattern = '[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
        # Match the last occurence of a float in the string
        # Example: '[foo] 50.3 bar 34.5' becomes '34.5'. This is potentially the price
        # to encode on the expense. If not, take 1.0 instead
        expense_price = re.findall(pattern, expense_description)
        # TODO: International formatting
        if not expense_price:
            price = 1.0
        else:
            price = expense_price[-1][0]
            expense_description = expense_description.replace(price, '')
            try:
                price = float(price)
            except ValueError:
                price = 1.0

        custom_values.update({
            'name': expense_description.strip(),
            'employee_id': employee.id,
            'product_id': product.id,
            # 'product_uom_id': product.uom_id.id,
            'tax_ids': [(4, tax.id, False) for tax in product.supplier_taxes_id],
            'quantity': 1,
            'unit_amount': price,
            'company_id': employee.company_id.id,
        })
        if account:
            custom_values['account_id'] = account.id
        return super(Labour_detals, self).message_new(msg_dict, custom_values)


class Labour_Sheet(models.Model):
    """
        Here are the rights associated with the expense flow

        Action       Group                   Restriction
        =================================================================================
        Submit      Employee                Only his own
                    Officer                 If he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Approve     Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        Post        Anybody                 State = approve and journal_id defined
        Done        Anybody                 State = approve and journal_id defined
        Cancel      Officer                 Not his own and he is expense manager of the employee, manager of the employee
                                             or the employee is in the department managed by the officer
                    Manager                 Always
        =================================================================================
    """
    _name = "labour.sheet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Expense Report"
    _order = "accounting_date desc, id desc"

    @api.model
    def _default_journal_id(self):
        journal = self.env.ref('hr_expense.hr_expense_account_journal', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        return journal.id

    @api.model
    def _default_bank_journal_id(self):
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    name = fields.Char('Expense Report Summary', required=True , readonly=True , states={'draft': [('readonly', False)], 'submit': [('readonly', False)], 'cancel': [('readonly', False)]})
    expense_line_ids = fields.One2many('labour.expense', 'sheet_id', string='Expense Lines', states={'approve': [('readonly', True)], 'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True, help='Expense Report State')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    address_id = fields.Many2one('res.partner', string="Employee Home Address")
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company")], related='expense_line_ids.payment_mode', default='company_account', readonly=True, string="Paid By")
    user_id = fields.Many2one('res.users', 'Manager', copy=False , readonly=True)
    # user_id = fields.Many2one('res.users', 'Manager', related='expense_line_ids.project_id.user_id' , readonly=True, copy=False, states={'draft': [('readonly', False)]}, track_visibility='onchange', oldname='responsible_id')
    total_amount = fields.Monetary('Total Amount', currency_field='currency_id', compute='_compute_amount', store=True, digits=dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_journal_id, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=_default_bank_journal_id, help="The payment method used when the expense is paid by the company.")
    accounting_date = fields.Date("Date")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False)
    department_id = fields.Many2one('hr.department', string='Department', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    is_multiple_currency = fields.Boolean("Handle lines with different currencies", compute='_compute_is_multiple_currency')
    can_reset = fields.Boolean('Can Reset', compute='_compute_can_reset')

    
    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.user_id.id
    #     for rec in self:
    #         if rec.expense_line_ids.project_id.user_id.id == is_expense_user :
    #             rec.can_project = True

     # @api.onchange('user_id','expense_line_ids')
    # def onchange_values(self):
    #     return {'domain': {'expense_line_ids': {[ ('user_id', '=', self.user_id.id)]}}

    # can_project = fields.Boolean('Can project', compute='_compute_can_project')


    # @api.multi
    # def _compute_can_project(self):
    #     is_expense_user = self.user_id
    #     for rec in self:
    #         if rec.expense_line_ids.project_id.user_id == is_expense_user :
    #             rec.can_project = True





    @api.depends('expense_line_ids.total_amount_company')
    def _compute_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_company'))

    @api.multi
    def _compute_attachment_number(self):
        for sheet in self:
            sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))

    @api.depends('expense_line_ids.currency_id')
    def _compute_is_multiple_currency(self):
        for sheet in self:
            sheet.is_multiple_currency = len(sheet.expense_line_ids.mapped('currency_id')) > 1

    @api.multi
    def _compute_can_reset(self):
        is_expense_user = self.user_has_groups('hr_expense.group_hr_expense_user')
        for sheet in self:
            sheet.can_reset = is_expense_user if is_expense_user else sheet.employee_id.user_id == self.env.user

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.address_id = rec.employee_id.sudo().address_home_id
            rec.department_id = rec.employee_id.department_id
            if not rec.user_id :
                rec.user_id = rec.expense_line_ids.project_manager.id
        # self.user_id = self.employee_id.expense_manager_id or self.employee_id.parent_id.user_id

    @api.multi
    @api.constrains('expense_line_ids')
    def _check_payment_mode(self):
        for sheet in self:
            expense_lines = sheet.mapped('expense_line_ids')
            if expense_lines and any(expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
                raise ValidationError(_("Expenses must be paid by the same entity (Company or employee)."))

    # @api.constrains('expense_line_ids', 'employee_id')
    # def _check_employee(self):
    #     for sheet in self:
    #         employee_ids = sheet.expense_line_ids.mapped('employee_id')
    #         if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != sheet.employee_id):
    #             raise ValidationError(_('You cannot add expenses of another employee.'))

    @api.model
    def create(self, vals):
        sheet = super(Labour_Sheet, self.with_context(mail_create_nosubscribe=True)).create(vals)
        sheet.activity_update()
        return sheet

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['post', 'done']:
                raise UserError(_('You cannot delete a posted or paid expense.'))
        super(Labour_Sheet, self).unlink()

    # --------------------------------------------
    # Mail Thread
    # --------------------------------------------

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'approve':
            return 'hr_expense.mt_expense_approved'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_expense.mt_expense_refused'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_expense.mt_expense_paid'
        return super(Labour_Sheet, self)._track_subtype(init_values)

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(Labour_Sheet, self)._message_auto_subscribe_followers(updated_values, subtype_ids)
        if updated_values.get('employee_id'):
            employee = self.env['hr.employee'].browse(updated_values['employee_id'])
            if employee.user_id:
                res.append((employee.user_id.partner_id.id, subtype_ids, False))
        return res

    # --------------------------------------------
    # Actions
    # --------------------------------------------


    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    # @api.multi
    # def action_sheet_move_create(self):
    #     if any(sheet.state != 'approve' for sheet in self):
    #         raise UserError(_("You can only generate accounting entry for approved expense(s)."))

    #     if any(not sheet.journal_id for sheet in self):
    #         raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

    #     expense_line_ids = self.mapped('expense_line_ids')\
    #         .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
    #     res = expense_line_ids.action_move_create()

    #     if not self.accounting_date:
    #         self.accounting_date = self.account_move_id.date

    #     if self.payment_mode == 'own_account' and expense_line_ids:
    #         self.write({'state': 'post'})
    #     else:
    #         self.write({'state': 'done'})
    #     self.activity_update()
    #     return res

    @api.multi
    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'labour.expense'), ('res_id', 'in', self.expense_line_ids.ids)]
        res['context'] = {
            'default_res_model': 'labour.sheet',
            'default_res_id': self.ids,
            'create': False,
            'edit': False,
        }
        return res

    # --------------------------------------------
    # Business
    # --------------------------------------------

    @api.multi
    def set_to_paid(self):
        self.write({'state': 'done'})

    @api.multi
    def action_submit_sheet(self):
        self.write({'state': 'submit'})
        self.activity_update()

    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'approve', 'user_id': responsible_id})
        self.activity_update()

    @api.multi
    def paid_expense_sheets(self):
        self.write({'state': 'done'})

    @api.multi
    def refuse_sheet(self, reason):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot refuse your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(_("You can only refuse your department expenses"))

        self.write({'state': 'cancel'})
        for sheet in self:
            sheet.message_post_with_view('hr_expense.hr_expense_template_refuse_reason', values={'reason': reason, 'is_sheet': True, 'name': self.name})
        self.activity_update()

    @api.multi
    def reset_expense_sheets(self):
        if not self.can_reset:
            raise UserError(_("Only HR Officers or the concerned employee can reset to draft."))
        self.mapped('expense_line_ids').write({'is_refused': False})
        self.write({'state': 'draft'})
        self.activity_update()
        return True

    def _get_responsible_for_approval(self):
        if self.user_id:
            return self.user_id
        elif self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.department_id.manager_id.user_id:
            return self.employee_id.department_id.manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'approve').activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(['hr_expense.mail_act_expense_approval'])


   




