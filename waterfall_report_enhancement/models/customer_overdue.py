# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def cron_overdue_customer(self):
        overdue_list = []
        email = []
        data = {}
        duecount = 0
        current_date = datetime.today().strftime('%Y-%m-%d')
        # match = self.search([('state', '=', 'open'), ('type', 'in', ['out_invoice', 'out_refund'])])
        query = """SELECT DISTINCT ai.user_id, ru.login FROM ACCOUNT_INVOICE ai 
                    LEFT JOIN res_users ru ON ru.id = ai.user_id
                    WHERE state='open' AND type in ('out_invoice', 'out_refund')"""
        self.env.cr.execute(query)
        match = self.env.cr.dictfetchall()
        for i in match:
            duecount = 0
            
            # overdue = self.env['account.invoice'].search(
            #     [('date_due', '<=', current_date), ('state', '=', 'open'), ('user_id', '=', i['user_id']),
            #      ('type', 'in', ['out_invoice', 'out_refund'])])
            querys = """SELECT ru.name as name ,
                        ai.number as number,
                        ai.origin as origin,
                        ai.date_invoice as date_invoice,
                        ai.date_due as date_due,
                        ai.amount_total as amount_total,
                        ai.residual as residual
                        FROM ACCOUNT_INVOICE ai
                        LEFT JOIN res_partner ru ON ru.id = ai.partner_id
                        WHERE ai.date_due <= '%s' and ai.user_id = %s
                        AND ai.state='open' AND ai.type in ('out_invoice', 'out_refund')"""% (current_date,i['user_id'])
            self.env.cr.execute(querys)
            overdue = self.env.cr.dictfetchall()
            
            
            for res in overdue:
                overdue_content = {}
                duecount = duecount + 1
                overdue_content['inv_count'] = duecount
                overdue_content['inv_no'] = res['number']
                overdue_content['origin'] = res['origin'] if res['origin'] else ''
                overdue_content['customer'] = res['name']
                overdue_content['inv_date'] = res['date_invoice']
                overdue_content['due_date'] = res['date_due']
                overdue_content['inv_amt'] = res['amount_total']
                overdue_content['due_amt'] = res['residual']
                overdue_list.append(overdue_content)
            data['invoice_overdue'] = overdue_list
            try:
                template_id = self.env.ref('waterfall_report_enhancement.customer_overdue_mail_report')
            except ValueError:
                template_id = False
            mail_template = self.env['mail.template'].browse(template_id.id)
            user_id = self.env['res.users'].browse(i['user_id'])
            
            ctx = self.env.context.copy()
            for user in user_id:
                ctx['name'] = user.name
            ctx['email_to'] = i['login']
            email.append(ctx['email_to'])
            
            for key, value in data.items():
                ctx['data'] = value
            
            mail_template.with_context(ctx).send_mail(i['user_id'], force_send=True, raise_exception=True)
            overdue_list = []
        return True
