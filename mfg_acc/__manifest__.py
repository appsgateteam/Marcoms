{
    'name': ' mrp Accounting',
    'author': "IG company",
    'category': 'Manufacturing',
    'summary': 'accounting in Manufacturing',
    'depends': ['mrp', 'stock_account'],
    'data': [
        'views/mfg_acc_view.xml',
        'views/mfg_cost_report.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
}