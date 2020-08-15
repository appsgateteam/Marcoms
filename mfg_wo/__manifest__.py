{
    'name': 'Mrp workorder',
    'author': "IG company",
    'category': 'Manufacturing',
    'depends': ['qlty_core', 'mrp', 'barcodes'],
    'data': [
        'views/qlty_views.xml',
        'views/mfg_pro_views.xml',
        'views/mfg_wo_views.xml',
	'views/mfg_rout.xml',
	'views/mfg_wc.xml',
	'views/res_config_settings_view.xml',
    ],
    'qweb': [
        'static/src/xml/widget_template.xml',
        'static/src/xml/_barcode.xml',
    ],
    'application': False,
}
