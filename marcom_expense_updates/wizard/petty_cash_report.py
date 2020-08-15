# -*- coding: utf-8 -*-

# from odoo import api, fields, models
from odoo import time
from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen







class petty_cash_report(models.TransientModel):
    _name = 'petty.cash.report'
    _description = 'Get Petty Cash Date'


    date_start  = fields.Date(string="Start Date" , required=True, default=fields.Date.today)
    date_end  = fields.Date(string="End Date" , required=True, default=fields.Date.today)
    


    # sales_person = fields.Many2one('res.users', string="Salesperson",required=True,index=True, default=lambda self: self.env.user)
    # able_to_modify_product = fields.Boolean(compute="set_access_for_product", default=False , string='Is user able to modify product?')
    # @api.depends('sales_person')
    # def set_access_for_product(self):
    #     self.able_to_modify_product = self.env['res.users'].has_group('sales_team.group_sale_manager')

    
            

    # def wizard_close(self):

    #     return {'type': 'ir.actions.act_window_close'}
        

    @api.multi
    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.read()[0]
        }
         # ref `module_name.report_id` as reference.
        # return self.env.ref('marcom_expense_updates.action_report_petty_cash_expense').report_action(self, data=data),self.wizard_close()
        self.ensure_one()
        action = self.env.ref('marcom_expense_updates.action_report_petty_cash_expense').report_action(self, data=data)
        action.update({'close_on_report_download': True})

        return action 


#     @api.multi
# def print_pdf(self):
#     action.update({'close_on_report_download': True})
#     return action
 