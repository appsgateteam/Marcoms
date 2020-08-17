# -*- coding: utf-8 -*-

{
    'name': 'Final Settlement Odoo',
    'version': '12.0.0.4',
    'category': 'HR',
    'summary': 'HR Management',
    'description': """
                    """,
    'author': 'Ernst',
    'website': 'http://www.ernst.in',
    'images': [],
    'depends': ['base', 'hr_payroll', 'hr_contract'],
    'data': [
                'security/ir.model.access.csv',
                'views/final_settlement_view.xml',
                'views/final_settlement_type_master.xml',
    
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
