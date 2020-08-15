# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'marcoms expense updates',
    'summary': 'customization of the wfexpense',
    'depends': ['hr_expense'],
    'data': [
        'wizard/hr_expense_refuse_reason_views.xml',
        'wizard/hr_expense_sheet_register_payment.xml',
        'wizard/petty_cash_report.xml',
        'report/expense.xml',
        'report/marcom_petty_cash_expense.xml',
        'views/food_view.xml',
        'views/transporation_vehicle_type.xml',
        'views/transportaion_type.xml',
        'views/meal_type.xml',
        # 'views/food_product.xml',
        # 'views/account.xml',
        'security/ir.model.access.csv',
        'security/wf_security.xml',
        'data/marcom_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
