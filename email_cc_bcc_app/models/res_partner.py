# -*- coding: utf-8 -*-

import logging
import threading

from odoo.tools.misc import split_every
from odoo import _, api, fields, models, registry, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _notify(self, message, rdata, record, force_send=False, send_after_commit=True, model_description=False, mail_auto_delete=True):
        """ Method to send email linked to notified messages. The recipients are
        the recordset on which this method is called.

        :param message: mail.message record to notify;
        :param rdata: recipient data (see mail.message _notify);
        :param record: optional record on which the message was posted;
        :param force_send: tells whether to send notification emails within the
          current transaction or to use the email queue;
        :param send_after_commit: if force_send, tells whether to send emails after
          the transaction has been committed using a post-commit hook;
        :param model_description: optional data used in notification process (see
          notification templates);
        :param mail_auto_delete: delete notification emails once sent;
        """
        if not rdata:
            return True

        base_template_ctx = self._notify_prepare_template_context(message, record, model_description=model_description)
        template_xmlid = message.layout if message.layout else 'mail.message_notification_email'
        try:
            base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(lang=base_template_ctx['lang'])
        except ValueError:
            _logger.warning('QWeb template %s not found when sending notification emails. Sending without layouting.' % (template_xmlid))
            base_template = False

        # prepare notification mail values
        base_mail_values = {
            'mail_message_id': message.id,
            'mail_server_id': message.mail_server_id.id,
            'auto_delete': mail_auto_delete,
            'references': message.parent_id.message_id if message.parent_id else False
        }
        if record:
            base_mail_values.update(self.env['mail.thread']._notify_specific_email_values_on_records(message, records=record))

        # classify recipients: actions / no action
        recipients = self.env['mail.thread']._notify_classify_recipients_on_records(message, rdata, records=record)

        Mail = self.env['mail.mail'].sudo()
        emails = self.env['mail.mail'].sudo()
        email_pids = set()
        recipients_nbr, recipients_max = 0, 50
        for group_tpl_values in [group for group in recipients.values() if group['recipients']]:
            # generate notification email content
            template_ctx = {**base_template_ctx, **group_tpl_values}
            mail_body = base_template.render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
            mail_body = self.env['mail.thread']._replace_local_links(mail_body)
            mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name)

            # send email
            for email_chunk in split_every(50, group_tpl_values['recipients']):
                recipient_values = self.env['mail.thread']._notify_email_recipients_on_records(message, email_chunk, records=record)
                create_values = {
                    'body_html': mail_body,
                    'subject': mail_subject,
                    'cc_visible': message.cc_visible,
                    'bcc_visible': message.bcc_visible,
                }
                if message.cc_visible:
                    create_values.update({'recipient_cc_ids': [(4, pccid.id) for pccid in message.partner_cc_ids]})
                else:
                    create_values.update({'recipient_cc_ids': []})

                if message.bcc_visible:
                    create_values.update({'recipient_bcc_ids': [(4, pbccid.id) for pbccid in message.partner_bcc_ids]})
                else:
                    create_values.update({'recipient_bcc_ids': []})

                create_values.update(base_mail_values)
                create_values.update(recipient_values)
                recipient_ids = [r[1] for r in create_values.get('recipient_ids', [])]
                email = Mail.create(create_values)
                if email and recipient_ids:
                    notifications = self.env['mail.notification'].sudo().search([
                        ('mail_message_id', '=', email.mail_message_id.id),
                        ('res_partner_id', 'in', list(recipient_ids))
                    ])
                    notifications.write({
                        'is_email': True,
                        'mail_id': email.id,
                        'is_read': True,  # handle by email discards Inbox notification
                        'email_status': 'ready',
                    })

                emails |= email
                email_pids.update(recipient_ids)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.currentThread(), 'testing', False)
        if force_send and len(emails) < recipients_max and \
                (not self.pool._init or test_mode):
            email_ids = emails.ids
            dbname = self.env.cr.dbname
            _context = self._context

            def send_notifications():
                db_registry = registry(dbname)
                with api.Environment.manage(), db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, _context)
                    env['mail.mail'].browse(email_ids).send()

            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                self._cr.after('commit', send_notifications)
            else:
                emails.send()

        return True

