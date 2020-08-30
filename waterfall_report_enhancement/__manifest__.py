# -*- coding: utf-8 -*-

{
    'name': 'Report Enhancement',
    'version': '2.2.4',
    'category': 'Purchase',
    'summary': """This app allow you to check the inv qty and qty to be invoiced in purchase analysis and send the due invoice notifications to salesperson""",
    'depends': [
        'purchase',
        'base',
        'account',
    ],
    'description': """
                   """,
    'author': 'Ernst',
    'website': 'http://www.n2n.com',
    'support': 'N2N',
    'images': [],
    'data': [
        'security/ir.model.access.csv',
        # 'views/customer_overdue.xml',
        'views/customer_overdue_cron.xml',
        'views/email_template_customer_overdue.xml',
        'report/n2n_entry_analysis.xml',
        'report/purchase_report_inherit.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
