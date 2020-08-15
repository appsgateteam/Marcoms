# -*- coding: utf-8 -*-

{
    'name': "Barcode_update",
    'summary': "Use barcode scanners to process logistics operations",
    'category': 'Extra Tools',
    'author': "IG Company",
    'description': """
        This module adds support for barcodes scanning to the warehouse management system.
    """,
    'category': 'Warehouse',
    'depends': ['barcodes', 'stock', 'web_tour'],
    'data': [
        'views/stock_inventory_viewss.xml',
        'views/stock_picking_viewss.xml',
        'views/stock_move_line_viewss.xml',
        'views/stock_barcode_templatess.xml',
        'views/stock_barcode_viewss.xml',
        'views/res_config_settings_views.xml',
        'views/stock_scrap_viewss.xml',
        'wizard/stock_barcode_lot_views.xml',
        'data/data.xml',
    ],
    'qweb': [
        "static/src/xml/stock_barcode.xml",
        "static/src/xml/qweb_templates.xml",
    ],
    'demo': [
        'data/demo.xml',
    ],
    'installable': True,
    'application': True,

}
