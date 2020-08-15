{
    'name': 'Maintenance mrp',
    'author': "IG company",
    'category': 'Manufacturing',
    'summary': 'Schedule and manage maintenance on machine and tools.',
    'depends': ['maintenance','mrp'],
    'data': [
        'views/mfg_main_views.xml',
        'views/mfg_mrp_views.xml'
    ],
    'auto_install': True,
}