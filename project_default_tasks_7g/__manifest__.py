# Copyright 2013-Today Seven Gates Interactive Technologies

{
    'name': 'Project Default Tasks',
    'summary': 'Adds default task functionality to projects.',
    'description': '''
This module offers default tasks for projects. If enabled in the settings, 
module creates all the default tasks when on project creation.''',
    'author': 'SevenGates Interactive Technologies',
    'version': '12.0.1.0.0',
    'category': 'Project',
    'website': 'https://www.sevengates.co',
    'depends': [
        'base',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/project_project.xml',
    ],
    'installable': True,
    'application': False,
    'css': ['static/src/css/project_default_tasks_7g.css'],
    'images': ["images/main_screenshot.png",
               "static/description/icon.png"],
    'license': 'OPL-1',
    'support': 'support@sevengates.co',
    'price': 0.0,
    'currency': 'EUR',
}
