# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Leave Report Analysis',
    'version': '12.0.0.4',
    'category': 'HR',
    'summary': 'Employee Leave Report Analysis',
    'depends': ['hr','hr_holidays','marcoms_updates'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/employee_inherit_view.xml',
        'wizard/employee_leave_wizard_view.xml',
        'report/employee_leave_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

