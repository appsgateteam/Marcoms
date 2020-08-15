from odoo import api, fields, models,_
from odoo.exceptions import except_orm, ValidationError ,UserError
from datetime import datetime, timedelta , date



class done_activity(models.Model):
    _name = "done.activity"

    name = fields.Char('Summary')
    state = fields.Char('State')
    type = fields.Char('Type')
    user = fields.Char('Done By')
    res_name = fields.Char('Description')
    plan_date = fields.Date('Due Date')
    close_date = fields.Date('Closed Date')


class mail_activity2(models.Model):
    _inherit = "mail.activity"

    def action_feedback(self, feedback=False):
        message = self.env['mail.message']
        obj = self.env['done.activity']
        if feedback:
            self.write(dict(feedback=feedback))
            
        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity},
                subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
                mail_activity_type_id=activity.activity_type_id.id,
            )
            obj.create({'res_name':activity.res_name,'close_date':date.today(),'plan_date':activity.date_deadline,'name': activity.summary,'type':activity.activity_type_id.name,'state':'done','user':activity.user_id.name})
            message |= record.message_ids[0] 

        self.unlink()
        return message.ids and message.ids[0] or False