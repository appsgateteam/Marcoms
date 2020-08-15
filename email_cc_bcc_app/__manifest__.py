# -*- coding: utf-8 -*-
{
    "name" : "Customer Email CC BCC in Odoo",
    "author": "Edge Technologies",
    "version" : "12.0.1.0",
    "category" : "Email",
    'summary': 'App for send Email to customer with CC and BCC',
    "description": """
    App for send Email to customer with CC and BCC, manage customer email cc bcc. Add CC/BCC in Email settings.
                    cc bcc on email wizard, email wizard cc and bcc, CC and BCC option on email wizard. Email CC and BCC option.
    Email CC BCC ODOO Email CC and BCC Mail Compose with Email CC compose Mail with Email CC Compose Email CC email Cc and Bcc cc email cc bcc email email multiple Cc and Bcc Add CC/BCC in Compose Email CC BCC Compose Email Add CC/BCC in Compose Email add multiple reciept email reply to all email reply to all email Default CC/BCC customer email sending option for send email mail send option cc mail bcc mail

                """,
    "license" : "OPL-1",
    "depends" : ['mail', 'account'],
    "data": [
        'security/ir.model.access.csv',
        'data/res_config_settings_data.xml',
        'views/res_config_settings_views.xml',
        'views/mail_mail_view.xml',
        'wizard/mail_compose_message_view.xml',
        'wizard/account_invoice_send_views.xml',
         ],
    "auto_install": False,
    "price": 15,
    "currency": 'EUR',
    "installable": True,
    "live_test_url":'https://youtu.be/mdTlVXc0FOg',
    "images":["static/description/main_screenshot.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
