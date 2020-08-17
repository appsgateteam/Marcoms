# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError, ValidationError
import math


class FinalSettlement(models.Model):
	_name = "final.settlement"
	_rec_name = 'employee_id'


	@api.multi
	def action_generate(self):
		payable = 0
		recievable = 0
		unpaid_tot = 0
		working_days = 0
		amount = 0
		for obj in self:
			final_settlement = obj.settlement_type_id.final_settlement
			leave_pending = obj.employee_id.leaves_count
			joining_date = obj.employee_id.join_date

			holiday_ids = self.env['hr.leave'].search([('employee_id','=',obj.employee_id.id),('holiday_status_id','=',4),('state','not in',('cancel','refuse'))])
			for holiday in holiday_ids:
				holiday_obj = self.env['hr.leave'].browse(holiday).id
				unpaid_tot = unpaid_tot + holiday_obj.number_of_days

			date_to = obj.resign_date
			if date_to:
				date_to = datetime.strptime(str(date_to),"%Y-%m-%d")
			if joining_date:
				joining_date = datetime.strptime(str(joining_date),"%Y-%m-%d")
			if not (date_to and joining_date):
				raise UserError(_('make sure joining_date and document date given'))

			working_days = ((date_to - joining_date).days + 1) - unpaid_tot
			allow_rules = []
			employee_id = obj.employee_id and obj.employee_id.id
			contract_ids = self.env['hr.contract'].search([('employee_id','=',employee_id),('state','=','open')])
			if not contract_ids:
				raise UserError(_('no active contract for this employee'))
			contract_id = contract_ids[0]
			contract_obj = self.env['hr.contract'].browse(contract_id).id
			basic = contract_obj.wage
			total_sal = contract_obj.hr_total_wage
			# for al_line in contract_obj.xo_allowance_rule_line_ids:
			#     al_line.copy({'od_sett_id':ids[0],'contract_id':False})
			vals = {'basic':basic,
					'join_date':obj.employee_id.join_date,
					'total_salary':total_sal,
					'leave_pending':leave_pending,
					'unpaid_leave':unpaid_tot,
					'total_working_days':working_days,
					'job_id':obj.employee_id.job_id.id,
					'department_id':obj.employee_id.department_id.id,
					'address_home_id':obj.employee_id.address_home_id.id,
					}
			self.write(vals)
			partner_id = obj.employee_id.address_home_id.id
			settlement_type_id = obj.settlement_type_id and obj.settlement_type_id.id
			settlement_ids = self.env['final.settlement.type.master'].search([('id','=',settlement_type_id)])
			settlement_type_obj = self.env['final.settlement.type.master'].browse(settlement_ids).id
			account_ids = []
			for accounts in settlement_type_obj.settlement_type_master_line:
				account_ids.append(accounts.account_id.id)
			if not account_ids:
				raise UserError(_('first set the accounts in settlement type master'))
			# if not partner_id:
			#     raise osv.except_osv(_('Error!'), _('define Home Address First'))
			if obj.account_line:
				for lines in obj.account_line:
					self.env['final.settlement.account.line'].unlink()


			account_move_line_obj = self.env['account.move.line']


			
			move_ids = account_move_line_obj.search([('partner_id','=',partner_id),('account_id','in',account_ids)])
			if not move_ids:
				raise UserError(_('there is no accounting entries for the particular employee'))

			move_data = account_move_line_obj.browse(move_ids).id
			move_line_credit={}
			move_line_debit={}
			for line in move_data:
				if not line.account_id:
					continue
				if line.credit:
					move_line_credit[line.account_id.id] = (line.account_id.id not in move_line_credit) \
															 and line.credit or (float(move_line_credit.get(line.account_id.id))+line.credit)
				if line.debit:
					move_line_debit[line.account_id.id] = (line.account_id.id not in move_line_debit) \
														   and line.debit or (float(move_line_debit.get(line.account_id.id))+line.debit)

			result =  { k: move_line_debit.get(k, 0) - move_line_credit.get(k, 0) for k in set(move_line_debit) | set(move_line_credit) }
			for account_id in result:
				if result[account_id] < 0:
					payable = math.fabs(result[account_id])
					amount = math.fabs(result[account_id])
				elif result[account_id] >0:
					amount = (-1 * result[account_id])
					payable = 0


				vals = {
					'account_id':account_id,
					'balance':result[account_id],
					'account_line_id':self.id,
					'amount':amount,
					'final_settlement_flag':final_settlement

				}
				self.env['final.settlement.account.line'].create(vals)
		# self.write(cr,uid,ids,{'checking_acc_entry_button_ctrl':True})
		return True

	@api.multi
	def action_validate(self):
		for obj in self:
			if not obj.account_new_line:
				raise UserError(_('there is no lines in adjustment'))
			final_settlement = obj.final_settlement
			account_move_obj = self.env['account.move']
			journal_id = obj.settlement_type_id.journal_id and obj.settlement_type_id.journal_id.id
			home_address = obj.employee_id.address_home_id and obj.employee_id.address_home_id.id
			date = obj.resign_date
			total_credit = 0
			total_debit = 0
			narration = 'Final Settlement' + '/'+ str(obj.employee_id.name)
			# period_pool = self.pool.get('account.period')
			# search_periods = period_pool.find(cr, uid, date, context=context)
			# period_id = search_periods[0]
			data_lines = []

			if not home_address:
				raise UserError(_('pls define partner for the employee'))

			recievable_acc_id = obj.employee_id.address_home_id.property_account_receivable_id and obj.employee_id.address_home_id.property_account_receivable_id.id
			payable_acc_id = obj.employee_id.address_home_id.property_account_payable_id and obj.employee_id.address_home_id.property_account_payable_id.id
			if not payable_acc_id:
				raise UserError(_('set payable acc in employee home address'))
			if not recievable_acc_id:
				raise UserError(_('set recievable acc in employee home address'))

			for lines in obj.account_new_line:
				total_debit = total_debit + round(lines.debit,2)
				total_credit = total_credit + round(lines.credit,2)

			if total_debit != total_credit:

				raise UserError(_('total debit and credit are not matching'))


			for line in obj.account_new_line:

				vals2 = {
						'journal_id':journal_id,
						'date':date,
						'naration':narration,
						'name':narration,
						'account_id':line.account_id.id,
						'debit':line.debit,
						'credit':0.0,
						'partner_id':home_address,
				}
				if vals2['debit'] >0.0 or vals2['credit'] >0.0:
					data_lines.append((0,0,vals2),)


				vals1 = {
						'journal_id':journal_id,
						'date':date,
						'naration':narration,
						'name':narration,
						'account_id':line.account_id.id,
						'debit':0.0,
						'credit':line.credit,
						'partner_id':home_address,
				}
				if vals1['debit'] >0.0 or vals1['credit'] >0.0:
					data_lines.append((0,0,vals1),)


			if data_lines:
				data = {
					'journal_id':journal_id,
					'date':date,
					'state':'draft',
					'ref':narration,
					'line_ids':data_lines
				}
				account_move = account_move_obj.create(data)

				self.write({'state':'done','account_move_id':account_move.id})
			else:
				raise UserError(_('no lines for generating journal entry'))

		return True


	@api.multi
	def check_accounts_entry(self):
		for obj in self:
			final_settlement = obj.final_settlement
			extra_row = {}
			transaction_ids = []
			recievable_acc_id = obj.employee_id.address_id.property_account_receivable_id and obj.employee_id.address_id.property_account_receivable_id.id
			payable_acc_id = obj.employee_id.address_id.property_account_payable_id and obj.employee_id.address_id.property_account_payable_id.id
			debit = 0
			credit = 0
			total_due = 0
			total_amt = 0
			total_debit =0
			total_credit =0
			sum_of_negative_values = 0
			sum_of_postive_values = 0
			existing_ids = self.env['final.settlement.new.account.line'].search([('account_line_id','=',obj.id)])
			if existing_ids:
				self.env['final.settlement.new.account.line'].unlink()

			for linee in obj.account_line:
				transaction_ids.append(linee.id)
			if not transaction_ids:
				raise UserError(_('generate the transactions first'))




			for line in obj.account_line:
	#            if not obj.account_line:
	#                raise osv.except_osv(_('Warning!'), _('generate the transactions first'))

				total_due = total_due + line.balance
				total_amt = total_amt + line.amount
				if line.balance < 0:

					if line.amount <0:
						sum_of_negative_values = sum_of_negative_values + line.balance
						raise UserError(_('check the signs of balance and amount'))

				if line.balance > 0:
					if line.amount >0:
						sum_of_postive_values = sum_of_postive_values + line.balance
						raise UserError(_('check the signs of balance and amount'))

					credit = line.amount

					debit = 0
				else:
					credit = 0
					debit = line.amount
				print("::::::::::::sum_of_postive_values",sum_of_postive_values)
				print("::::::::::::sum_of_negative_values",sum_of_negative_values)
				vals = {'account_id':line.account_id.id or False,'account_line_id':line.account_line_id.id or False,'final_settlement':final_settlement,'debit':math.fabs(debit),'credit':math.fabs(credit),'due':math.fabs(line.balance)}
				self.env['final.settlement.new.account.line'].create(vals)
			if total_due < 0:
				total_debit = 0
				total_credit =total_amt

				extra_row = {'account_id':payable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
			else:
				total_debit = total_amt
				total_credit =0
				extra_row = {'account_id':recievable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
			self.env['final.settlement.new.account.line'].create(extra_row)
			self.write({'state':'progress'})
		return True

	@api.multi
	def generate_gratuity_value(self):
		experience = 0
		gratuity = 0
		for obj in self:
			obj.gratuity_line_id.unlink()
			terminated = obj.settlement_type_id.termination
			resign = obj.settlement_type_id.final_settlement
			join_date = obj.join_date
			resign_date = obj.resign_date
			if not join_date:
				raise Warning(_("pls provide join date"))
			joining_date = datetime.strptime(str(join_date), "%Y-%m-%d").date()
			gratuity_date = datetime.strptime(str(resign_date), "%Y-%m-%d").date()
			experience = float((gratuity_date -  joining_date).days)/365.00
			experiance_days = float((gratuity_date -  joining_date).days)
			working_days = ((gratuity_date - joining_date).days + 1)
			contract_ids = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','=','open')])
			if not contract_ids:
				raise UserError(_('no active contract for this employee'))
			contract_ids = contract_ids[0]
			contract_obj = self.env['hr.contract'].browse(contract_ids).id
			contract_type = contract_obj.contract_type
			one_day_wage = float(contract_obj.wage * 12) / 365.00 
			max_gratuity = float(contract_obj.wage * 24)  
#                 one_day_wage = float((contract_obj.wage) / 30)
				

##################################################case1
			data_lines = []
			if contract_type =='limited' and resign==True:
				if experience < 1:
					vals1 = {
							  'slab':'0 to 1 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0.0,
							  'resign_amount':0.0,
					}
					data_lines.append((0,0,vals1),)
				elif experience >= 1 and experience < 3:
					gratuity = (((7 * one_day_wage)/365.0) * experiance_days)
					vals2 = {
							  'slab':'1 to 3 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals2),)
				elif experience >= 3 and experience < 5:
					gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
					vals3 = {
							  'slab':'3 to 5 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals3),)
				elif experience >= 5:
					extra_year = experiance - 5
					extra_year_in_days = extra_year * 365
					gratuity = ((21 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
					vals4 = {
							  'slab':'Over 5 Years',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals4),)
				self.gratuity_line_id = data_lines

			if contract_type =='limited' and terminated==True:
				if experience < 1:
					vals1 = {
							  'slab':'0 to 1 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0.0,
							  'resign_amount':0.0,
					}
					data_lines.append((0,0,vals1),)
				elif experience >= 1 and experience < 3:
					gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
					vals2 = {
							  'slab':'1 to 3 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals2),)
				elif experience >= 3 and experience < 5:
					gratuity = (((21 * one_day_wage)/365.0) * experiance_days)
					vals3 = {
							  'slab':'3 to 5 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals3),)
				elif experience >= 5:
					extra_year = experiance - 5
					extra_year_in_days = extra_year * 365
					gratuity = ((30 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
					vals4 = {
							  'slab':'Over 5 Years',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals4),)
				self.gratuity_line_id = data_lines
			if contract_type =='unlimited' and resign==True:
				if experience < 1:
					vals1 = {
							  'slab':'0 to 1 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0.0,
							  'resign_amount':0.0,
					}
					data_lines.append((0,0,vals1),)
				elif experience >= 1 and experience < 3:
					gratuity = (((7 * one_day_wage)/365.0) * experiance_days)
					vals2 = {
							  'slab':'1 to 3 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals2),)
				elif experience >= 3 and experience < 5:
					gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
					vals3 = {
							  'slab':'3 to 5 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals3),)
				elif experience >= 5:
					extra_year = experiance - 5
					extra_year_in_days = extra_year * 365
					gratuity = ((21 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
					vals4 = {
							  'slab':'Over 5 Years',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals4),)
				self.gratuity_line_id = data_lines

			if contract_type =='unlimited' and terminated==True:
				if experience < 1:
					vals1 = {
							  'slab':'0 to 1 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0.0,
							  'resign_amount':0.0,
					}
					data_lines.append((0,0,vals1),)
				elif experience >= 1 and experience < 3:
					gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
					vals2 = {
							  'slab':'1 to 3 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals2),)
				elif experience >= 3 and experience < 5:
					gratuity = (((21 * one_day_wage)/365.0) * experiance_days)
					vals3 = {
							  'slab':'3 to 5 Year',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals3),)
				elif experience >= 5:
					extra_year = experiance - 5
					extra_year_in_days = extra_year * 365
					gratuity = ((30 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
					vals4 = {
							  'slab':'Over 5 Years',
							  'date_from':joining_date,
							  'date_to':gratuity_date,
							  'no_of_days':working_days,
							  'termination_amount':0,
							  'resign_amount':gratuity,
					}
					data_lines.append((0,0,vals4),)
				self.gratuity_line_id = data_lines
			   
		return True

	company_id = fields.Many2one('res.company',string="Company", default=lambda self: self.env.user.company_id.id)
	employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
	join_date = fields.Date(string="Join Date")
	resign_date = fields.Date(string="Resign Date", default=fields.Date.context_today)
	settlement_type_id = fields.Many2one('final.settlement.type.master',string="Settlement Type",required=True)
	basic = fields.Float(string="Basic")
	# hr_allowance_line_ids = fields.One2many('hr.allowance.line','nn_sett_id',string="HR Allowance")
	total_salary = fields.Float('Total Salary')
	department_id = fields.Many2one('hr.department',string="Department",readonly=True)
	job_id =fields.Many2one('hr.job',string='Job', readonly=True)
	reason = fields.Text(string="Reason")
	state = fields.Selection([
			('draft', 'New'),
			('progress', 'Progress'),
			('done', 'Done'),
			],
			'Status', readonly=True, track_visibility='onchange')
	final_settlement = fields.Boolean("Final Settlement")
	address_home_id = fields.Many2one('res.partner', string='Home Address',readonly=True)
	account_line = fields.One2many('final.settlement.account.line','account_line_id',string="Account Line")
	account_new_line = fields.One2many('final.settlement.new.account.line','account_line_id',string="Account New Line")
	account_move_id = fields.Many2one('account.move','Entry',readonly=True)
	gratuity_line_id = fields.One2many('gratuity.employee','settlement_grat_id',string="Gratuity Line")
	leave_pending = fields.Integer(string="Remaining Leaves")
	unpaid_leaves = fields.Integer(string="Unpaid Leaves")
	total_working_days = fields.Float(string="Total Working Days")
	# @api.multi
	# def _total_wage(self):
	# 	for rec in self:
	# 		x = rec.wage
	# 		for l in rec.hr_allowance_line_ids:
	# 			x = x + l.amt
	# 		rec.hr_total_wage = x

# class HRallowanceLine(models.Model):
#     _inherit = 'hr.allowance.line'

#     nn_sett_id = fields.Many2one('final.settlement',string="Settlement")

class FinalSettlementAccountLine(models.Model):
	_name = "final.settlement.account.line"
	_description = "final.settlement.account.line"


	
	account_line_id = fields.Many2one('final.settlement',"settlement")
	account_id = fields.Many2one('account.account',"Account",required=True)
	balance = fields.Float("Balance",readonly=True)
	amount = fields.Float("Payable")
	final_settlement_flag = fields.Boolean("Final Settlement")




class od_final_settlement_new_account_line(models.Model):
	_name = "final.settlement.new.account.line"
	_description = "final.settlement.new.account.line"

	# def create(self, cr, uid, vals, context=None):
	#     if vals.get('account_line_id') or  vals.get('account_id'):
	#         obj = self.pool.get('od.final.settlement').browse(cr,uid,[vals.get('account_line_id')],context)
	#         final_settlement = obj.final_settlement


	#         if final_settlement:
	#             vals['final_settlement'] = final_settlement
	#     return super(od_final_settlement_new_account_line, self).create(cr, uid, vals, context=context)




	account_line_id = fields.Many2one('final.settlement',string="Settlement")
	account_id = fields.Many2one('account.account',string="Account",required=True)
	debit = fields.Float("Debit")
	credit = fields.Float("Credit")
	due = fields.Float("Due")
	final_settlement = fields.Boolean("Final Settlement")


	
class FinalSettlementTypeMaster(models.Model):
	_name = "final.settlement.type.master"

	name = fields.Char("Name",required=True)
	final_settlement = fields.Boolean("Resign")
	remarks = fields.Text("Remarks")
	termination = fields.Boolean("Termination")
	journal_id = fields.Many2one('account.journal',string="Journal",required=True)
	settlement_type_master_line = fields.One2many('final.settlement.type.master.line','settlement_type_master_line_id',string="Settlement Line")

class FinalSettlementTypeMasterLine(models.Model):
	_name = "final.settlement.type.master.line"

	
	account_id = fields.Many2one('account.account',"Account")
	settlement_type_master_line_id = fields.Many2one('final.settlement.type.master')


class GratuityCalculation(models.Model):
	_name = "gratuity.employee"

	
	slab = fields.Char(string="Slab")
	date_from = fields.Date(string="Date From")
	date_to = fields.Date(string="Date To")
	no_of_days = fields.Float(string="Num of Days Working")
	termination_amount = fields.Float(string="Termination")
	resign_amount = fields.Float(string="Resignation")
	settlement_grat_id = fields.Many2one('final.settlement', string="Settlement")


class Contract(models.Model):
	_inherit = 'hr.contract'
	
	contract_type = fields.Selection([('limited', 'Limited'),('unlimited', 'Unlimited')], string="Contract Type", required=True)
