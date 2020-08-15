# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Job Costing and Job Cost Sheet With Material Request Odoo',
    'version': '12.0.0.8',
    'category': 'Projects',
    'summary': 'This modules helps to manage contracting,Job Costing and Job Cost Sheet inculding dynamic material request',
    'description': """
        Project Job Costing and Job Cost Sheet.
        This modules helps to manage contracting,Job Costing and Job Cost Sheet inculding dynamic material request
        Project Contracting
        Project costing , project calculation , project cost calculation  constuction project costing 
        project cost sheet , construction material request odoo , construction project management , construction billing system , construction cost calculation , calculate  cost of construction project
        job contract, job contracting, Construction job , contracting job , contract estimation cost estimation project estimation , 
        This modules helps to manage contracting,Job Costing and Job Cost Sheet inculding dynamic material request
        Odoo job costing bundle , job costing in construction , project cost Estimation , construction cost Estimation in Odoo 
            Send Estimation to your Customers for materials, labour, overheads details in job estimation.
        Estimation for Jobs - Material / Labour / Overheads
        Material Esitmation
        Job estimation
        labour estimation
        Overheads estimation
        BrowseInfo developed a new odoo/OpenERP module apps.
        This module use for Real Estate Management, Construction management, Building Construction,
        Material Line on JoB Estimation
        Labour Lines on Job Estimation.
        Overhead Lines on Job Estimation.
        create Quotation from the Job Estimation.
        overhead on job estimation
        Construction Projects
        Budgets
        Notes
        Materials
        Material Request For Job Orders
        Add Materials
        Job Orders
        Create Job Orders
        Job Order Related Notes
        Issues Related Project
        Vendors
        Vendors / Contractors

        Construction Management
        Construction Activity
        Construction Jobs
        Job Order Construction
        Job Orders Issues
        Job Order Notes
        Construction Notes
        Job Order Reports
        Construction Reports
        Job Order Note
        Construction app
        Project Report
        Task Report
        Construction Project - Project Manager
        real estate property
        propery management
        bill of material
        Material Planning On Job Order

        Bill of Quantity On Job Order
        Bill of Quantity construction
        Project job costing on manufacturing
    BrowseInfo developed a new odoo/OpenERP module apps.
    Material request is an instruction to procure a certain quantity of materials by purchase , internal transfer or manufacturing.So that goods are available when it require.
    Material request for purchase, internal transfer or manufacturing
    Material request for internal transfer
    Material request for purchase order
    Material request for purchase tender
    Material request for tender
    Material request for manufacturing order.
    product request, subassembly request, raw material request, order request
    manufacturing request, purchase request, purchase tender request, internal transfer request
""",
    'author': 'BrowseInfo',
    "price": 48,
    "currency": "EUR",
    'website': 'http://www.browseinfo.in',
    'depends': ['base','sale_management','project','purchase','account','hr_timesheet','note','stock','document','hr_timesheet_attendance','bi_subtask','bi_material_purchase_requisitions'],  #
    'data': [
        
            # bi_project_issue
            'security/ir.model.access.csv',
            'security/requisition_menu_hide.xml',
            'views/project_issue.xml',
            'views/project_project_views.xml',
            'views/res_partner_views.xml',
            
            
            'views/custom_job_costing_view.xml',
            'views/project_view.xml',
            'views/job_cost_view.xml',
            'views/material_view.xml',
            'views/configuration_view.xml',
            'report/job_cost_report.xml',
            'report/project_job_report_view.xml',
            'report/job_order_report_view.xml',
            'report/job_cost_sheet_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
    "live_test_url":'https://youtu.be/xnjlNTuX6U4',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
