# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'N2N Stock Report',
    'version': '1.0',
    'category': 'General',
    'sequence': 15,
    'summary': 'Stock Move Report',
    'description': """ """,
    'website': 'http://www.viscore-i.com',
    'depends': ['base', 'stock', 'project'],
    'data': [ 
            'security/ir.model.access.csv',
            'wizard/n2n_stock_move_analysis_wizard.xml',
            'report/n2n_stock_move_analysis_view.xml',
           ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}
