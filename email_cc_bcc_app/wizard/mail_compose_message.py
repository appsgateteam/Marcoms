# -*- coding: utf-8 -*-

import base64
from odoo import _, api, fields, models
from odoo.tools import pycompat


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    partner_cc_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_cc_res_partner_rel',
        'wizard_id', 'partner_id', 'CC')
    partner_bcc_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_bcc_res_partner_rel',
        'wizard_id', 'partner_id', 'BCC')
    cc_visible = fields.Boolean('Enable Email CC', readonly=True)
    bcc_visible = fields.Boolean('Enable Email BCC', readonly=True)

    @api.model
    def default_get(self, fields):
        result = super(MailComposer, self).default_get(fields)
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
        return result

    @api.multi
    def get_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create mail_messages
        or mail_mails. """
        self.ensure_one()
        results = dict.fromkeys(res_ids, False)
        rendered_values = {}
        mass_mail_mode = self.composition_mode == 'mass_mail'

        # render all template-based value at once
        if mass_mail_mode and self.model:
            rendered_values = self.render_message(res_ids)
        # compute alias-based reply-to in batch
        reply_to_value = dict.fromkeys(res_ids, None)
        if mass_mail_mode and not self.no_auto_thread:
            records = self.env[self.model].browse(res_ids)
            reply_to_value = self.env['mail.thread']._notify_get_reply_to_on_records(default=self.email_from, records=records)

        blacklisted_rec_ids = []
        if mass_mail_mode and hasattr(self.env[self.model], "_primary_email"):
            BL_sudo = self.env['mail.blacklist'].sudo()
            blacklist = set(BL_sudo.search([]).mapped('email'))
            if blacklist:
                [email_field] = self.env[self.model]._primary_email
                targets = self.env[self.model].browse(res_ids).read([email_field])
                # First extract email from recipient before comparing with blacklist
                for target in targets:
                    sanitized_email = self.env['mail.blacklist']._sanitize_email(target.get(email_field))
                    if sanitized_email and sanitized_email in blacklist:
                        blacklisted_rec_ids.append(target['id'])

        for res_id in res_ids:
            # static wizard (mail.message) values
            mail_values = {
                'subject': self.subject,
                'body': self.body or '',
                'parent_id': self.parent_id and self.parent_id.id,
                'partner_ids': [partner.id for partner in self.partner_ids],
                'attachment_ids': [attach.id for attach in self.attachment_ids],
                'partner_cc_ids': [partner_cc.id for partner_cc in self.partner_cc_ids],
                'partner_bcc_ids': [partner_bcc.id for partner_bcc in self.partner_bcc_ids],
                'cc_visible': self.cc_visible,
                'bcc_visible': self.bcc_visible,
                'author_id': self.author_id.id,
                'email_from': self.email_from,
                'record_name': self.record_name,
                'no_auto_thread': self.no_auto_thread,
                'mail_server_id': self.mail_server_id.id,
                'mail_activity_type_id': self.mail_activity_type_id.id,
            }
            # mass mailing: rendering override wizard static values
            if mass_mail_mode and self.model:
                mail_values.update(self.env['mail.thread']._notify_specific_email_values_on_records(False, records=self.env[self.model].browse(res_id)))
                # keep a copy unless specifically requested, reset record name (avoid browsing records)
                mail_values.update(notification=not self.auto_delete_message, model=self.model, res_id=res_id, record_name=False)
                # auto deletion of mail_mail
                if self.auto_delete or self.template_id.auto_delete:
                    mail_values['auto_delete'] = True
                # rendered values using template
                email_dict = rendered_values[res_id]
                mail_values['partner_ids'] += email_dict.pop('partner_ids', [])
                mail_values.update(email_dict)
                if not self.no_auto_thread:
                    mail_values.pop('reply_to')
                    if reply_to_value.get(res_id):
                        mail_values['reply_to'] = reply_to_value[res_id]
                if self.no_auto_thread and not mail_values.get('reply_to'):
                    mail_values['reply_to'] = mail_values['email_from']
                # mail_mail values: body -> body_html, partner_ids -> recipient_ids
                mail_values['body_html'] = mail_values.get('body', '')
                mail_values['recipient_ids'] = [(4, id) for id in mail_values.pop('partner_ids', [])]

                # process attachments: should not be encoded before being processed by message_post / mail_mail create
                mail_values['attachments'] = [(name, base64.b64decode(enc_cont)) for name, enc_cont in email_dict.pop('attachments', list())]
                attachment_ids = []
                for attach_id in mail_values.pop('attachment_ids'):
                    new_attach_id = self.env['ir.attachment'].browse(attach_id).copy({'res_model': self._name, 'res_id': self.id})
                    attachment_ids.append(new_attach_id.id)
                mail_values['attachment_ids'] = self.env['mail.thread']._message_post_process_attachments(
                    mail_values.pop('attachments', []),
                    attachment_ids,
                    {'model': 'mail.message', 'res_id': 0}
                )
                # Filter out the blacklisted records by setting the mail state to cancel -> Used for Mass Mailing stats
                if res_id in blacklisted_rec_ids:
                    mail_values['state'] = 'cancel'
                    # Do not post the mail into the recipient's chatter
                    mail_values['notification'] = False

            results[res_id] = mail_values
        return results
