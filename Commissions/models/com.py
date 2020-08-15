# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools ,_
from odoo.exceptions import except_orm, ValidationError,UserError
from odoo.exceptions import  AccessError, UserError, RedirectWarning,Warning
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.exceptions
import re 

class TeamCommission(models.Model):
    _name = 'team.commission'
    _inherit = 'mail.thread'

    name = fields.Char('Name')
    department = fields.Many2one('hr.department',string='Department',track_visibility="onchange")
    date_from = fields.Date('From',track_visibility="onchange")
    date_to = fields.Date('To',track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    commission_id = fields.One2many('employee.commission','team_id',string='Employee Commission',track_visibility="onchange")

    @api.constrains('date_from','date_to')
    def check_inv_date(self):
        for rec in self:
            if rec.date_from >= rec.date_to:
                raise ValidationError(_("The Date To should be bigger that the from date"))

    @api.multi
    def action_confirm(self):
        self.write({'state':'submit'})

    @api.onchange('department')
    def _get_employees(self):
        for rec in self:
            array = []
            if rec.commission_id:
                # empp = []
                for l in rec.commission_id:
                    l.unlink()
                com = self.env['hr.employee'].search([('department_id','=',rec.department.id)])
                for line in com:
                    vals = {
                        'employee' : line.id,
                    }
                    array.append((0,0,vals))
                rec.update({'commission_id':array})

                
            else:
                com = self.env['hr.employee'].search([('department_id','=',rec.department.id)])
                for line in com:
                    vals = {
                        'employee' : line.id,
                    }
                    array.append((0,0,vals))
                rec.update({'commission_id':array})

    @api.model
    def create(self,vals):

        com = self.env['team.commission'].search([('department','=',vals.get('department')),('date_from','<=',vals.get('date_from')),('date_from','<=',vals.get('date_to')),('date_to','>=',vals.get('date_from')),('date_to','>=',vals.get('date_to'))])
        if com:
            raise UserError('The date Range for this department is already exist')
        # vals['name'] = """%s ( %s - %s)""" %(vals.get('department.name').name,vals.get('date_from'),vals.get('date_to'))
        result = super(TeamCommission, self).create(vals)
        return result

    @api.onchange('department','date_from','date_to')
    def _get_name(self):
        self.name = """%s ( %s - %s)""" %(self.department.name,self.date_from,self.date_to)


class EmployeeCommission(models.Model):
    _name = 'employee.commission'

    employee = fields.Many2one('hr.employee',string="Employee")
    team_id = fields.Many2one('team.commission',string='Commission')
    first_range_amount_from = fields.Float('First Range From')
    first_range_amount_to = fields.Float('First Range To')
    first_range_commission = fields.Float('Commission')
    second_range_amount_from = fields.Float('Second Range From')
    second_range_amount_to = fields.Float('Second Range To')
    second_range_commission = fields.Float('Commission')
    third_range_amount_from = fields.Float('Third Range From')
    third_range_amount_to = fields.Float('Third Range To')
    third_range_commission = fields.Float('Commission')
    

class CommissionEvaluation(models.Model):
    _name = 'commission.evaluation'
    _inherit = 'mail.thread'

    name = fields.Char('Name', readonly=True,copy =False, default=lambda self: _('New'),track_visibility="onchange")
    date_from = fields.Date('From Date',copy =False,track_visibility="onchange")
    date_to = fields.Date('To Date',copy =False,track_visibility="onchange")
    sales_commission = fields.Float('Sales Commission%',track_visibility="onchange")
    designer_commission = fields.Float('Designer Commission%',track_visibility="onchange")
    operation_commission = fields.Float('Operation Commission%',track_visibility="onchange")
    purchase_commission = fields.Float('Purchase Commission%',track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    commission_id = fields.One2many('commission.lines','comm_id',string='Commission Lines',track_visibility="onchange")

    @api.constrains('date_from','date_to')
    def check_inv_date(self):
        for rec in self:
            if rec.date_from >= rec.date_to:
                raise ValidationError(_("The Date To should be bigger that the from date"))

    @api.multi
    def action_confirm(self):
        self.write({'state':'confirm'})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('commission.evaluation') or 'New'  

        return super(CommissionEvaluation, self).create(vals)

    @api.onchange('commission_id')
    def _get_commission(self):
        for rec in self:
            for line in rec.commission_id:
                line.total_commission = line.sales_commission + line.designer_commission + line.operation_commission + line.purchase_commission
                

    # @api.model_cr
    def get_data(self, cr, context=None):

        for lines in self.commission_id:
            lines.unlink()
        # tools.drop_view_if_exists(self.env.cr, table)
        d_from = str(self.date_from)
        to = str(self.date_to)
        d_from = d_from.replace('-', '')
        to = to.replace('-', '')
        # raise UserError(d_from)
        self.env.cr.execute("""select 
                            so.name as name,
                            so.confirmation_date as date,
                            so.partner_id as client,
                            so.user_id as saleperson,
                            crm.assign_to_designer as designer,
                            crm.show as event,
                            so.contract_type as contract_type,
                            so.analytic_account_id as project,
                            so.amount_untaxed as untax_amount,
                            so.amount_total as total_amount,

                            ( SELECT sum(aml.debit) AS sum
                                    FROM account_move_line aml
                                    WHERE aml.account_id = 579 and aml.analytic_account_id=so.analytic_account_id) AS organizer,

                                    
                            ( SELECT sum(aml.debit) AS sum
                                    FROM account_move_line aml
                                    WHERE aml.account_id = 580 and aml.analytic_account_id=so.analytic_account_id) AS early,

                                    
                            ( SELECT sum(aml.debit) AS sum
                                    FROM account_move_line aml
                                    WHERE aml.account_id = 581 and aml.analytic_account_id=so.analytic_account_id) AS storage,

                                    
                            ( SELECT sum(aml.debit) AS sum
                                    FROM account_move_line aml
                                    WHERE aml.account_id = 582 and aml.analytic_account_id=so.analytic_account_id) AS others
                            
                            from sale_order so
                            left join crm_lead crm on crm.id=so.opportunity_id
                            left join account_move_line aml on aml.analytic_account_id=so.analytic_account_id
                            WHERE CAST(so.confirmation_date as date) >= '%s' AND CAST(so.confirmation_date as date) < '%s' AND (so.state = 'sale' OR so.state = 'done')
                            
                            group by 
                            so.name,
                            so.confirmation_date,
                            so.partner_id,
                            so.user_id,
                            crm.assign_to_designer,
                            crm.show,
                            so.contract_type,
                            so.analytic_account_id,
                            so.amount_untaxed,
                            so.amount_total,
                            aml.account_id"""% (d_from,to))
        # querys = self.env.cr.execute(query,)
        res = self.env.cr.dictfetchall() 
        array = []
        com = self.env['commission.lines']
        
        for rec in res:
            # raise UserError(rec['name'])
            x = 0.0
            y = 0.0
            paid_amount = 0.0
            bal_amount = 0.0
            coms = self.env['account.invoice'].search([('origin','=',rec['name'])])
            for l in coms:
                x = x + l.amount_total
                y = y + l.residual
                # rec.inv_date = l.date_invoice
                paid_amount = x - y
                bal_amount = y 
            vals = {
                'comm_id':self.id,
                'so_number':rec['name'],
                'so_date':rec['date'],
                'client':rec['client'],
                'account_manager':rec['saleperson'],
                'designer_name':rec['designer'],
                'event':rec['event'],
                'contract_type':rec['contract_type'],
                'contract_value':rec['untax_amount'],
                'net_value_vat':rec['total_amount'],
                'received':paid_amount,
                'balance':bal_amount,
                'organizer_charge':rec['organizer'] or 0.0,
                'early_access_charge':rec['early'] or 0.0,
                'storage':rec['storage'] or 0.0,
                'others1':rec['others'] or 0.0,
                # 'contract_net_value': float(rec['untax_amount']) - float(rec['organizer']) - float(rec['early']) - float(rec['storage']) - float(rec['others']),
            }
            array.append(vals)
            # raise UserError(vals['organizer_charge'])
        com.create(array)
        

        for line in self.commission_id:
            line.contract_net_value = line.contract_value - line.organizer_charge - line.early_access_charge - line.storage - line.others1
            line.sales_commission = (line.contract_net_value * (self.sales_commission or 0.0) / 100.0)
            line.designer_commission = (line.contract_net_value * (self.designer_commission or 0.0) / 100.0)
            line.operation_commission = (line.contract_net_value * (self.operation_commission or 0.0) / 100.0)
            line.purchase_commission = (line.contract_net_value * (self.purchase_commission or 0.0) / 100.0)
            line.total_commission = line.sales_commission + line.designer_commission + line.operation_commission + line.purchase_commission
            

class CommissionLines(models.Model):
    _name = 'commission.lines'

    comm_id = fields.Many2one('commission.evaluation',string='Commission')
    so_number = fields.Char('SO Number')
    so_date = fields.Date('Sales order date')
    client = fields.Many2one('res.partner',string='Client')
    account_manager = fields.Many2one('res.users',string='Account Manager')
    designer_name = fields.Many2one('res.users',string='Designer Name')
    event = fields.Char('Event')
    contract_type = fields.Char('Contract type')
    contract_value = fields.Float('Contract Value AED')
    net_value_vat = fields.Float('Net Contract Value + VAT')
    received = fields.Float('Received')
    balance = fields.Float('Balance')
    organizer_charge = fields.Float('Organizer chg.')
    early_access_charge = fields.Float('Early Access Chg.')
    storage = fields.Float('Storage')
    others1 = fields.Float('Others1')
    contract_net_value = fields.Float('Contract Net Value')
    sales_commission = fields.Float('Sales Commission')
    designer_commission = fields.Float('Designer Commission')
    operation_commission = fields.Float('Operation Commission')
    purchase_commission = fields.Float('Purchase Commission')
    total_commission = fields.Float('Total Commission')
    remarks = fields.Text('Remarks')

    