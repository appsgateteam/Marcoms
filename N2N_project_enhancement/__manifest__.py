# -*- coding: utf-8 -*-

{
    'name': 'Project Enhancement Odoo',
    'version': '12.0.0.4',
    'category': 'Project',
    'summary': 'Project Tasks Management',
    'description': """
                    """,
    'author': 'Ernst',
    'website': 'http://www.ernst.in',
    'images': [],
    'depends': ['base','project', 'purchase_requisition', 'stock', 'purchase', 'sale_timesheet', 'hr_timesheet', 'analytic', 'mail', 'account'],
    'data': [
                'security/ir.model.access.csv',
		'security/security_view.xml',
                'data/material_requisition_template_view.xml',
                'data/ir_sequence_data.xml',
                'views/employee_timesheet_view.xml',
                'views/project_enhancement_view.xml',
                'views/material_requisition_view.xml',
                'views/timesheet_template_inherit.xml',
                'views/overhead_timesheet_view.xml',
                'report/material_comparison_view.xml',
                'report/n2n_stock_move_analysis_view.xml',
                'report/labour_comparison_view.xml',
                'report/overhead_comparison_view.xml',
                'wizard/n2n_stock_move_analysis_wizard.xml',
    
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
