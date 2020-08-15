# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Show Done Activities',
    'summary': 'Show Done Activity details in the crm module',
    'author': 'Ziad Monim(ZMs Company)',
    'license': 'AGPL-3',
    'description': """
Show Done Activity
===================

Show Done Activity details in the crm modules

after install the module go to CRM/Reporting/Done Activites
    """,
    'depends': ['crm','sales_team'],
    'data': [
        'views/done_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
