# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'
    _description = 'Account Invoice Send'

    partner_cc_ids = fields.Many2many(
        'res.partner', 'account_invoice_send_cc_res_partner_rel',
        'wizard_id', 'partner_id', 'CC')
    partner_bcc_ids = fields.Many2many(
        'res.partner', 'account_invoice_send_bcc_res_partner_rel',
        'wizard_id', 'partner_id', 'BCC')
    cc_visible = fields.Boolean('Enable Email CC', readonly=True)
    bcc_visible = fields.Boolean('Enable Email BCC', readonly=True)

    @api.model
    def default_get(self, fields):
        result = super(AccountInvoiceSend, self).default_get(fields)
        default_cc_bcc = self.env.ref('email_cc_bcc_app.res_config_email_ccbcc_data1')
        if result:
            config_obj = self.env['res.config.settings'].search([], limit=1, order="id desc")
            if not config_obj:
                config_obj = default_cc_bcc
            result.update({
                'partner_cc_ids': [(6, 0, config_obj.partner_cc_ids.ids)],
                'partner_bcc_ids': [(6, 0, config_obj.partner_bcc_ids.ids)],
                'cc_visible' : config_obj.cc_visible,
                'bcc_visible' : config_obj.bcc_visible,
            })
            composer_id = self.env['mail.compose.message'].browse(result.get('composer_id'))
            composer_id.write({
                'partner_cc_ids': [(6, 0, config_obj.partner_cc_ids.ids)],
                'partner_bcc_ids': [(6, 0, config_obj.partner_bcc_ids.ids)],
                'cc_visible' : config_obj.cc_visible,
                'bcc_visible' : config_obj.bcc_visible,
            })
        return result
