from odoo import models
from datetime import datetime

class BankReconcileXLS(models.AbstractModel):
    _name = 'report.bank_reconciliation.report_bank_reconcillation_st_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        lang = self.env.user.lang
        lang_date = self.env['res.lang'].search([('code', '=', lang)])


        format1 = workbook.add_format({'font_size':14 ,'align':'vcenter','bold': True})
        format2 = workbook.add_format({'font_size': 10, 'align': 'vcenter'})
        format3 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': True})
        sheet = workbook.add_worksheet('Bank Statement')

        sheet.write(2, 2, 'Bank', format1)
        sheet.write(3, 2, lines.journal_id.name, format2)
        sheet.write(2, 4, 'Bank Account', format1)
        sheet.write(3, 4, lines.account_id.name, format2)

        oldformat = lines.date_from
        newformat = oldformat.strftime(lang_date.date_format)
        old1 = lines.date_to
        new1 = old1.strftime(lang_date.date_format)

        sheet.write(2, 6, 'Date From', format1)
        sheet.write(3, 6, newformat, format2)
        sheet.write(2, 8, 'Date To', format1)
        sheet.write(3, 8, new1, format2)

        sheet.write(5, 2, 'Book Balance', format1)
        sheet.write(6, 2, lines.gl_balance, format2)
        sheet.write(5, 4, 'Bank Balance', format1)
        sheet.write(6, 4, lines.bank_balance, format2)
        sheet.write(5, 6, 'Unreconciled Amount', format1)
        sheet.write(6, 6, lines.balance_difference, format2)



        sheet.write(8, 1, 'Date', format3)
        sheet.write(8, 2, 'Label', format3)
        sheet.write(8, 3, 'Reference', format3)
        sheet.write(8, 4, 'Partner', format3)
        sheet.write(8, 5, 'Due Date', format3)
        sheet.write(8, 6, 'Bank St.Date', format3)
        sheet.write(8, 7, 'Debit', format3)
        sheet.write(8, 8, 'Credit', format3)

        # result = []
        # record = []
        # line_st = self.env['bank.statement'].browse('statement_lines')
        #
        # print('----rec---',line_st)
        #
        row_number = 10

        for line in lines.statement_lines:
            d1 = line.date
            d2 = d1.strftime(lang_date.date_format)
            d3 = line.date_maturity
            d4 = d3.strftime(lang_date.date_format)
            d5 = line.statement_date
            d6 = 0
            if d5:
                d6 = d5.strftime(lang_date.date_format)

            sheet.write(row_number, 1, d2, format2)
            sheet.write(row_number, 2, line['name'], format2)
            sheet.write(row_number, 3, line['ref'], format2)
            sheet.write(row_number, 4, line.partner_id.name, format2)
            sheet.write(row_number, 5, d4, format2)
            sheet.write(row_number, 6, d6, format2)
            sheet.write(row_number, 7, line['debit'], format2)
            sheet.write(row_number, 8,line['credit'], format2)
            row_number+= 1

