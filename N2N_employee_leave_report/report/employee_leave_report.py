# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools

class N2NLeaveAnalysisView(models.Model):
    _name = "n2n.leave.analysis.view"
    _description = "N2N Leave Analysis"
    _auto = False

    employee_id = fields.Many2one('hr.employee',string='Name')
    identification_id = fields.Char(string='Employee No.')
    designation = fields.Many2one('hr.job',string='Designation')
    company_id = fields.Many2one('res.company',string='Company')
    join_date = fields.Date(string='Joining Date')
    total_leaves = fields.Char(string='Total Leaves Taken')
    total_allocated = fields.Char(string='Total Allocated Days')
    pending_leaves = fields.Char(string='Pending Leaves')
    wage = fields.Float(string='Salary per month')
    salary_per = fields.Float(string='80% of Salary')
    leave_amt = fields.Float(string='Leave Amount')
      


 
    @api.model_cr
    def init(self):
        # cr = self.env.cr   
        tools.drop_view_if_exists(self._cr, 'n2n_leave_analysis_view')
        self._cr.execute("""
            CREATE OR REPLACE VIEW n2n_leave_analysis_view AS
                SELECT row_number() over() AS id,
                emp.id as employee_id,
                emp.identification_id as identification_id,
                emp.job_id as designation,
                emp.join_date::date as join_date,
                emp.company_id as company_id,
                sum(l.number_of_days) as total_leaves, 
                (select sum(a.number_of_days)
                from hr_leave_allocation a
                where emp.id = a.employee_id
                ) as total_allocated,
                ((select sum(a.number_of_days)
                    from hr_leave_allocation a
                    where emp.id = a.employee_id
                    ) - sum(l.number_of_days)) as pending_leaves,
                con.wage as wage,
                (con.wage*0.8) as salary_per,
                (con.wage - (con.wage*0.8)) as leave_amt
                from hr_employee emp
                left join hr_leave l on l.employee_id = emp.id
                left join hr_contract con on con.employee_id = emp.id
                group by emp.id,emp.identification_id,emp.job_id,emp.join_date,emp.company_id,con.wage

                        """)
