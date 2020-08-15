# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'COMMISSIONS',
    'author': 'Ziad Monim',
    'depends': ['mail','hr'],
    'data': [
        'views/com.xml',
        'security/ir.model.access.csv',
        'security/COM_security.xml',
        'data/comm_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
