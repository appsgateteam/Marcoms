# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Accounting Reports',
    'summary': 'View and create reports',
    'category': 'Accounting',
    'description': """
Accounting Reports
==================
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_financial_report_data.xml',
        'views/mfb_account_report_view.xml',
        'views/mfb_report_financial.xml',
        'views/mfb_search_template_view.xml',
        'views/mfb_report_followup.xml',
        'views/mfb_partner_view.xml',
        'views/mfb_followup_view.xml',
        'views/mfb_account_journal_dashboard_view.xml',
        'views/mfb_res_config_settings_views.xml',
    ],
    'qweb': [
        'static/src/xml/account_report_template.xml',
    ],
    'auto_install': True,
    'installable': True,

}
