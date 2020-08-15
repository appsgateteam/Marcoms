# -*- coding: utf-8 -*-

{
    'name': 'Multiple Invoice Payment',
    'version': '12.0.1.3',
    'category': 'account',
    'sequence': 50,
    'author': 'ERP Labz',
    'website': "http://erplabz.com",
    
    'summary': 'Pay multiple invoice using payment screen with any user defined amount same like v7,8',
    'description': """ 
            Pay multiple invoice
            Pay multiple Vendor bill
	    Pay multiple credit/debit note
		Multiple invoice payment, 
		Invocie Multiple payment,
	 	Payment,
		Partial Invocie Payment,
		Full invoice Payment,
		Payment write off,
		Payment Invoice,
		batch payment
		Multiple Vendor Bill Payment,
		Multiple Credit note payment,
		Multiple Debit Note Payment,
		Multiple Invoice Payment,
		multi payment,
		multiple payment,
     """,

    'depends': ['account'],
    
    'data': [
           'views/account_payment_inehrit.xml',
           'security/ir.model.access.csv',
             ],
    "images":['static/description/banner.jpg'],
 'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    
    'currency': 'EUR',
    'price': 30.00,
    
}

