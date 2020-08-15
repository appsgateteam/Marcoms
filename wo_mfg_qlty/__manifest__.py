{
    'name': 'MRP Workerorder in quality',
    'author': "IG company",
    'category': 'Manufacturing',
    'depends': ['qlty_cntrl','barcodes','mrp'],
    "data": [
        'views/qlty_views.xml',
        'views/mfg_wo_views.xml',
    ],
    'auto_install': True,
}
