from odoo import api, fields, models, _


class accountmoveinheirt(models.Model):
    _inherit = 'account.move'

    prepare = fields.Char('Prepared by')
    checked = fields.Char('Checked by')
    received = fields.Char('Received by')
    approved = fields.Char('Approved by')
    verified = fields.Char('Verified by')

    

class accountmoveinheirt2(models.Model):
    _inherit = 'account.payment'

    prepare = fields.Char('Prepared by')
    checked = fields.Char('Checked by')
    received = fields.Char('Received by')
    approved = fields.Char('Approved by')
    verified = fields.Char('Verified by')
