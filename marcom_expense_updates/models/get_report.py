# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT




class PettyCashtReport(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.marcom_expense_updates.report_petty_cash_expense'

    


    

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        # sales_person = data['form']['sales_person'][1]


        SO = self.env['petty.cash.expense']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)


        # date_ob_star = datetime.strptime(date_start, DATE_FORMAT)

        # date_ob_end = datetime.strptime(date_end,DATE_FORMAT)

        

        docs = []
        while start_date <= end_date:
            date = start_date
            start_date += delta

            print(date, start_date)
            orders = SO.search([
                ('date', '>=', date.strftime(DATETIME_FORMAT)),
                ('date', '<', start_date.strftime(DATETIME_FORMAT)) ])

            # for rec in orders: 

            #     if rec.inv_date and rec.inv_date < date_ob_star.date():
            #         continue

            #     if rec.inv_date and rec.inv_date > date_ob_end.date():
            #         continue
                    

            for rec in orders: 
                vaul = {
                    'date'        : rec.date,
                    'reference'   : rec.reference,
                    'name'        : rec.name,
                    'product_id'  : rec.product_id.name,
                    'unit_amount' : rec.unit_amount,
                    'tax_ids'     : rec.tax_ids.name,
                    'untaxed_amount' : rec.untaxed_amount,
                    'total_amount'  : rec.total_amount,
                    'employee_id'   : rec.employee_id.name,
                    'project_id'    : rec.project_id.name,
                    'state'         : rec.state,
                    'user_id'       : rec.sheet_id.user_id.name,
                    'journal_id'    : rec.sheet_id.journal_id.name,
                    'company': self.env.user.company_id,
                }
                docs.append(vaul)



        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'docs': docs,
        }