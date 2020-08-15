from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError


class AppointmentReport(models.AbstractModel):
    _name = 'report.marcoms_updates.job_costing_report_view'
    _description = 'Job Costing Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        event = data['form']['event']
        project = data['form']['project']
        # if data['form']['project']:
        #     appointments = self.env['hospital.appointment'].search([('patient_id', '=', data['form']['patient_id'][0])])
        # else:
        appointment_list = []
        array = []
        array2 = []
        array3 = []
        vals = {}
        # for rec in data['form']['project']:
        #     appointments = self.env['account.move.line'].search([('analytic_account_id','=',rec['id'])])
        #     for l in appointments:
        #         vals = {
        #             'debit':l.debit,
        #             'credit':l.credit,
        #         }
        #         array.append(vals)
        for rec in data['form']['project']:
            appointments = self.env['account.move.line'].search([('analytic_account_id','=',rec['id'])])
            # raise ValidationError(_(appointments))
            
            for l in appointments:
                array = []
                for recs in data['form']['project']:
                    appointmen = self.env['account.move.line'].search([('analytic_account_id','=',recs['id']),('account_id','=',l.account_id.id)])
                    debit = 0.0
                    for le in appointmen:
                        debit += abs(le.balance)
                        # credit += le.credit
                    vals = {
                    'pro':recs['id'],
                    'acc':l.account_id.id,
                    'acc_type':l.account_id.user_type_id.id,
                    'balance':debit,
                    }
                    array.append(vals)
                # raise ValidationError(_(array))
                accid = []
                if appointment_list:
                    for ac in appointment_list:
                        accid.append(ac['acc'])
                aid = array[0]['acc']
                if aid in accid:
                    for x in appointment_list:
                        if aid == x['acc']:
                            i = 0
                            for arr in x['vals']:
                                
                                arr['balance'] += array[i]['balance']
                                i = i+1
                else:
                    
                    appointment_list.append({'project':rec['id'],'acc_type':l.account_id.user_type_id.id,'acc':l.account_id.id,'account':l.account_id.name,'vals':array})
                # y = 0
                for recs in array:
                    valss = {
                        'pro':recs['pro'],
                        'acc':recs['acc'],
                        'acc_type':recs['acc_type'],
                        'balance':recs['balance'],
                    }
                    array3.append(valss)
                    
                    

        # raise ValidationError(_(array3))
        x = 0
        for rec in data['form']['project']:
            appointments = self.env['account.move.line'].search([('analytic_account_id','=',rec['id'])])
            # raise ValidationError(_(appointments))
            debit = 0.0
            credit = 0.0
            grand_total = 0.0
            
            # arrayz = []
            for l in array3:
                if l['pro'] == rec['id']:
                    if l['acc_type'] == 14:
                        debit = debit + l['balance']
                    if l['acc_type'] == 16:
                        credit = credit + l['balance']
            x = x + 1
            # for l in appointments:

            #     if l.account_id.user_type_id.id == 14:
            #         debit = debit + abs(l.balance)
            #     if l.account_id.user_type_id.id == 16:
            #         credit = credit + abs(l.balance)
                        # credit += le.credit
            Contribution_per = 0.0
            Contribution = 0.0
            grand_total = credit
            Contribution = debit - credit
            if debit == 0:
                Contribution_per = 0
            else:
                Contribution_per = float(Contribution) / float(debit)*100
            vals = {
            'pro':rec['id'],
            'balance_sal':debit,
            'balance_ex':credit,
            'grand_total':grand_total,
            'Contribution':Contribution,
            'Contribution_per':Contribution_per,
            }
            array2.append(vals)

    
            # for res in appointment_list:
                
        # raise ValidationError(_(array2))
        # array2 = []
        # for rec in data['form']['project']:
        
        # x = 0
        # for res in appointment_list:
        #     to_sal = 0.0
        #     to_ex = 0.0
        #     if res['acc_type'] == 14:
        #         for v in res['vals']:
        #             to_sal +=  v['balance']
        #     elif res['acc_type'] == 16:
        #         for v in res['vals']:
        #             to_ex +=  v['balance']
        #     x = x + 1
        #     vals = {
        #         'project': res['project'],
        #         'sales':to_sal,
        #         'expen':to_ex,
        #         }
        #     array2.append(vals)
        # raise ValidationError(_(array2))
          # raise ValidationError(_(data['form']['project']))
        # appointment_list = []
        # for app in appointments:
        #     vals = {
        #         'name': app.name,
        #         'notes': app.notes,
        #         'appointment_date': app.appointment_date
        #     }
        #     appointment_list.append(vals)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'event': event,
            'project': project,
            # 'date_end': date_end,
            # 'sales_person': sales_person,
            'docs': appointment_list,
            'total': array2,
        }
