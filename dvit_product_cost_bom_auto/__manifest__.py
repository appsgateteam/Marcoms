# -*- coding: utf-8 -*-
{
    'name': "Product cost from BoM auto",

    'summary': """
        Auto set final product cost from BoM on update, and from raw material purchase price.
        """,

    'description': """

1- Auto update BoM cost from its components on write

2- Auto update BoM's Product cost price from the BoM cost on write

3- Auto update cost of all BoMs that include a product on updating that product's cost manually or through purchase orders in case of avg price.
    """,

    "license": "AGPL-3",
    'author': "DVIT.ME",
    'website': "http://www.dvit.me",

    'category': 'Uncategorized',
    'version': '10.0.0.4',

    'depends': ['mrp'],

    'data': [],

    'demo': [],
    "images": [
        'static/description/banner.png'
    ],
}
