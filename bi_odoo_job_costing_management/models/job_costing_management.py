# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import html2plaintext

class JobCostSheet(models.Model):
    _name = 'job.cost.sheet'
    
    name = fields.Char(string="Name",required="True") 
    sequence = fields.Char(string='Sequence', readonly=True,copy=False,index=True,default=lambda self: self.env['ir.sequence'].get('job.cost.sheet'))
    project_id = fields.Many2one('project.project',string='Project')
    analytic_ids = fields.Many2one('account.analytic.account',string="Analytic Account")
    job_order_id = fields.Many2one('job.order','Job Order')
    job_issue_customer_id = fields.Many2one('res.partner','Job Issue Customer')
    create_date = fields.Datetime(string="Create Date",default=datetime.now())
    close_date = fields.Datetime(string="Close Date",default=datetime.now())
    create_by_id = fields.Many2one('res.users','Created By')
    material_job_cost_line_ids = fields.One2many('job.cost.line','material_job_cost_sheet_id','Material Job Cost Line')
    labour_job_cost_line_ids = fields.One2many('job.cost.line','labour_job_cost_sheet_id','Labout Job Cost Line')
    overhead_job_cost_line_ids = fields.One2many('job.cost.line','overhead_job_cost_sheet_id','Overhead Job Cost Line')
    
    
    total_material_cost = fields.Float(compute='_compute_total_material_cost',string="Total Material Cost",default=0.0)
    total_labour_cost = fields.Float(compute='_compute_total_labour_cost',string='Total Labour Cost',default=0.0)
    total_overhead_cost = fields.Float(compute='_compute_total_overhead_cost',string='Total Overhead Cost',default=0.0)
    total_cost = fields.Float(compute='_compute_total_cost',string='Total Cost',default=0.0)
    
    job_cost_description = fields.Text('Job Cost Description')
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    stage = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('approve','Approved'),('done','Done')],'Stage',copy=False,default='draft')
    purchase_order_line_count = fields.Integer('Purchase Order Line', compute='_get_purchase_order_line_count')
    invoice_line_count = fields.Integer('Invoice Order Line', compute='_get_invoice_line_count')
    purchase_id = fields.One2many('purchase.order.line','job_cost_sheet_id',string='Purchase Order')
    invoice_id = fields.One2many('account.invoice.line','job_cost_sheet_id')
    #is_done_stage = fields.Boolean(string='Is Done Stage')
    #is_confirm_stage = fields.Boolean(string='Is Confirm Stage',default=False)
    #is_approve_stage = fields.Boolean(string='Is Approve Stage',default=False)
    company_id = fields.Many2one('res.company',string="Company")
    sale_reference = fields.Text(string="Description Sale Reference")
    
    @api.multi
    def _get_purchase_order_line_count(self):
        count = 0.0
        for job_cost_sheet in self:
            purchase_order_line_ids = self.env['purchase.order.line'].search([('job_cost_sheet_id','=',job_cost_sheet.id)])
            for purchase in purchase_order_line_ids:
                purchase_ids = self.env['purchase.order'].search([('id','in',purchase.order_id.ids)])
                count = count + len(purchase_ids)
            job_cost_sheet.purchase_order_line_count = count
        return True

    @api.multi
    def purchase_order_line_button(self):
        # self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.mapped('purchase_id').mapped('order_id').ids)],
        }

    @api.multi
    def _get_invoice_line_count(self):
        count = 0.0
        for job_cost_sheet in self:
            invoice_line_id = self.env['account.invoice.line'].search([('job_cost_sheet_id','=',job_cost_sheet.id)])
            for invoice in invoice_line_id:
                invoice_ids = self.env['account.invoice'].search([('id','in',invoice.invoice_id.ids)])
                count = count + len(invoice_ids)
            job_cost_sheet.invoice_line_count = count
        
    @api.multi
    def invoice_line_button(self):
        self.ensure_one()
        return {
            'name': 'Invoice/Bill',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'domain': [('id', '=', self.mapped('invoice_id').mapped('invoice_id').ids)],
        }       
        
    @api.multi
    def action_confirm(self):
        confirm_stage = self.write({'stage':'confirm'})
        return confirm_stage
    
    @api.multi
    def action_done(self):
        done_stage = self.write({'stage':'done'})
        return done_stage
    
    @api.multi
    def action_approve(self):
        approve_stage = self.write({'stage':'approve'})
        return approve_stage
    
    @api.multi
    def _compute_total_material_cost(self):
        total = 0.0
        for line in self.material_job_cost_line_ids:
            total += line.subtotal
        self.total_material_cost = total
        
    @api.multi
    def _compute_total_labour_cost(self):
        total = 0.0
        for line in self.labour_job_cost_line_ids:
            total += line.subtotal
        self.total_labour_cost = total
        
    @api.multi
    def _compute_total_overhead_cost(self):
        total = 0.0
        for line in self.overhead_job_cost_line_ids:
            total += line.subtotal
        self.total_overhead_cost = total   
        
    @api.multi
    def _compute_total_cost(self):
        total = 0.0
        total = self.total_material_cost + self.total_labour_cost + self.total_overhead_cost
        self.total_cost = total 
        
    @api.multi
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id.id
    
class JobCostLine(models.Model):
    _name = "job.cost.line"
    
    material_job_cost_sheet_id = fields.Many2one('job.cost.sheet','Material Job Cost Sheet')
    labour_job_cost_sheet_id = fields.Many2one('job.cost.sheet','Labour Job Cost Sheet')
    overhead_job_cost_sheet_id = fields.Many2one('job.cost.sheet','Overhead Job Cost Sheet')
    date = fields.Datetime('Date',default=datetime.now())
    job_type_id = fields.Many2one('job.type',string='Job Type')
    product_id = fields.Many2one('product.product','Product')
    description = fields.Text('Description')
    reference = fields.Char('Reference')
    quantity = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom','Unit Of Measure')
    unit_price = fields.Float('Cost/Unit Price',defaut=0.0)
    actual_purchase_qty = fields.Float(compute='_compute_purchase_quantity',string='Actual Purchased Quantity',default=0.0)
    actual_invoice_qty = fields.Float(compute='_compute_invoice_quantity',string='Actual Invoice Quantity',default=0.0)
    subtotal = fields.Float(compute='onchange_quantity',string='Sub Total',defalut=0.0)
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    job_type = fields.Selection([('material','Material'),('labour','Labour'),('overhead','Overhead')],string="Job Cost Order Type")
    #Labour
    hours = fields.Float('Hours',default=0.0)
    actual_timesheet_hours = fields.Float('Actual Timesheet Hours',default=0.0)
    #Overhead
    basis = fields.Char('Basis')
    
    @api.multi
    def _compute_purchase_quantity(self):
        for line in self:
            purchase_order_line_ids = self.env['purchase.order.line'].search([('product_id','=',line.product_id.id),('account_analytic_id','=',line.material_job_cost_sheet_id.analytic_ids.id)])
            for qty in purchase_order_line_ids:
                line.actual_purchase_qty += qty.product_qty
            
    @api.multi
    def _compute_invoice_quantity(self):
        for line in self:
            invoice_line_ids = self.env['account.invoice.line'].search([('product_id','=',line.product_id.id),('account_analytic_id','=',line.material_job_cost_sheet_id.analytic_ids.id)])
            for qty in invoice_line_ids:
                line.actual_invoice_qty += qty.quantity
        
    @api.onchange('quantity', 'unit_price')
    def onchange_quantity(self):
        for line in self:
            price = line.quantity * line.unit_price
            if line.hours:
                price = line.hours * line.unit_price
            line.subtotal = price
            
    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name
        
    @api.multi
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id



class JobOrder(models.Model):
    _name = 'job.order'
    
    name = fields.Char(string="Name",required="True")
    project_id = fields.Many2one('project.project',string='Project')
    user_id = fields.Many2one('res.users',string='Assigned To')
    planned_hours = fields.Float(string="Initially Planned Hours",default="0.0")
    start_date = fields.Datetime(string="Starting Date",default=datetime.now())
    end_date = fields.Datetime(string="Ending Date")
    deadline_date = fields.Datetime(string="Deadline")
    tag_ids = fields.Many2many('project.tags',string="Tags")
    description = fields.Text(string="Description")
    timesheet_ids = fields.One2many('account.analytic.line','account_analytic_line_id',string="Timesheet")
    material_planning_ids = fields.One2many('material.planning','material_id',string="Product Material Planning")
    consumed_material_ids = fields.One2many('material.planning','consumed_material_id',string="Consumed Material")
    material_requisitions_ids = fields.One2many('stock.picking','material_requisition_id',string="Material Requisitions")
    stock_move_ids = fields.One2many('stock.move','stock_move_id',string="Stock Move")
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    active = fields.Boolean(default=True)
    job_cost_count = fields.Integer('Job Cost', compute='_get_job_cost_count')
    stock_move_count = fields.Integer('Stock Move', compute='_get_stock_move_count')
    job_note_count = fields.Integer('Job Note', compute='_get_job_note_count')



    @api.multi
    def _get_job_note_count(self):
        for job_order in self:
            job_note_ids = self.env['job.note'].search([('job_order_id','=',job_order.id)])
            job_order.job_note_count = len(job_note_ids)
        
    @api.multi
    def job_note_button(self):
        self.ensure_one()
        return {
            'name': 'Job Note',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'job.note',
            'domain': [('job_order_id', '=', self.id)],
        }
        
    @api.multi
    def _get_job_cost_count(self):
        for job_order in self:
            job_cost_ids = self.env['job.cost.sheet'].search([('project_id','=',job_order.id)])
            job_order.job_cost_count = len(job_cost_ids)
        
    @api.multi
    def project_job_cost_button(self):
        self.ensure_one()
        return {
            'name': 'Job Cost Sheet',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'job.cost.sheet',
            'domain': [('job_order_id', '=', self.id)],
        }
    
    @api.multi
    def _get_stock_move_count(self):
        for job_order in self:
            stock_move_ids = self.env['stock.move'].search([('stock_move_id','=',job_order.id)])
            job_order.stock_move_count = len(stock_move_ids)
        
    @api.multi
    def stock_move_button(self):
        self.ensure_one()
        return {
            'name': 'Stock Move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'domain': [('stock_move_id', '=', self.id)],
        }        

    @api.model
    def create(self, vals):
        result = super(JobOrder, self).create(vals)
        product_id =""
        if product_id in vals:
            stock_picking_ids = self.env['stock.picking'].search([('construction_project_id','=',vals['project_id'])])      
            for picking in stock_picking_ids:
                for move in picking.move_lines:
                    move.write({'stock_move_id':result.id})  
                picking.write({'material_requisition_id':result.id})
        return result

    @api.multi
    def write(self,vals):
        res = super(JobOrder, self).write(vals)
        if self.project_id:
            stock_picking_ids = self.env['stock.picking'].search([('construction_project_id','=',self.project_id.id)])
            for picking in stock_picking_ids:
                for move in picking.move_lines:
                    move.write({'stock_move_id':self.id})
                picking.write({'material_requisition_id':self.id})           
        return res
                        
    @api.multi
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id.id
    
class MaterialPlanning(models.Model):
    _name = "material.planning"

    material_id = fields.Many2one('job.order','Job Material Planning')
    consumed_material_id = fields.Many2one('job.order','Job Consumed Material')
    product_id = fields.Many2one('product.product','Product')
    description = fields.Text('Description')
    quantity = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom','Unit Of Measure')
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    product_type = fields.Selection([('material_planning','Material Planning'),('consumed_material','Consumed Material')],string="Product Type")
    
    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name
        
    @api.multi
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id

class StockMove(models.Model):
    _inherit = "stock.move"
    
    stock_move_id = fields.Many2one('job.order','Job Stock Move')
    name = fields.Char('Name')
    
class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    
    account_analytic_line_id = fields.Many2one('job.order','Job Timesheet')

class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    @api.multi
    def _get_job_cost_count(self):
        for project in self:
            job_cost_ids = self.env['job.cost.sheet'].search([('project_id','=',project.id)])
            project.job_cost_count = len(job_cost_ids)
        
    @api.multi
    def project_job_cost_button(self):
        self.ensure_one()
        return {
            'name': 'Job Cost Sheet',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'job.cost.sheet',
            'domain': [('project_id', '=', self.id)],
        }
    @api.multi
    def _get_note_count(self):
        for project in self:
            note_note_ids = self.env['note.note'].search([('construction_proj_id','=',project.id)])
            project.note_count = len(note_note_ids)
        
    @api.multi
    def project_note_button(self):
        self.ensure_one()
        return {
            'name': 'Note Note',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'note.note',
            'domain': [('construction_proj_id', '=', self.id)],
        }
            
    job_cost_sheet_id = fields.Many2one('job.cost.sheet','Responsible Person')
    job_cost_count  =  fields.Integer('Job Cost', compute='_get_job_cost_count')
    note_count = fields.Integer('Note', compute='_get_note_count')

class JobNote(models.Model):
    _name = 'job.note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    def _get_default_stage_id(self):
        return self.env['note.stage'].search([('user_id', '=', self.env.uid)], limit=1)
    
    tag_ids = fields.Many2many('note.tag','note_id','tag_id',string="Tag")
    memo = fields.Html(string="Body")
    job_order_id = fields.Many2one('job.order','Job Order')
    responsible_user = fields.Many2one('res.users','Responsible Person')
    job_note_id = fields.Many2one('job.order','Job Order')
    name = fields.Text(compute='_compute_name', string='Note Summary', store=True)
    user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.uid)
    sequence = fields.Integer('Sequence')
    stage_id = fields.Many2one('note.stage', compute='_compute_stage_id',
        inverse='_inverse_stage_id', string='Stage')
    stage_ids = fields.Many2many('note.stage', 'note_stage_rel', 'note_id', 'stage_id',
        string='Stages of Users',  default=_get_default_stage_id)
    open = fields.Boolean(string='Active', default=True)
    date_done = fields.Date('Date done')
    color = fields.Integer(string='Color Index')
    job_note_id = fields.Many2one('job.order','Job Order')
    
    @api.depends('memo')
    def _compute_name(self):
        """ Read the first line of the memo to determine the note name """
        for note in self:
            text = html2plaintext(note.memo) if note.memo else ''
            note.name = text.strip().replace('*', '').split("\n")[0]

    @api.multi
    def _compute_stage_id(self):
        for note in self:
            for stage in note.stage_ids.filtered(lambda stage: stage.user_id == self.env.user):
                note.stage_id = stage

    @api.multi
    def _inverse_stage_id(self):
        for note in self.filtered('stage_id'):
            note.stage_ids = note.stage_id + note.stage_ids.filtered(lambda stage: stage.user_id != self.env.user)

    @api.model
    def name_create(self, name):
        return self.create({'memo': name}).name_get()[0]

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if groupby and groupby[0] == "stage_id":
            stages = self.env['note.stage'].search([('user_id', '=', self.env.uid)])
            if stages:  # if the user has some stages
                result = [{  # notes by stage for stages user
                    '__context': {'group_by': groupby[1:]},
                    '__domain': domain + [('stage_ids.id', '=', stage.id)],
                    'stage_id': (stage.id, stage.name),
                    'stage_id_count': self.search_count(domain + [('stage_ids', '=', stage.id)]),
                    '__fold': stage.fold,
                } for stage in stages]

                # note without user's stage
                nb_notes_ws = self.search_count(domain + [('stage_ids', 'not in', stages.ids)])
                if nb_notes_ws:
                    # add note to the first column if it's the first stage
                    dom_not_in = ('stage_ids', 'not in', stages.ids)
                    if result and result[0]['stage_id'][0] == stages[0].id:
                        dom_in = result[0]['__domain'].pop()
                        result[0]['__domain'] = domain + ['|', dom_in, dom_not_in]
                        result[0]['stage_id_count'] += nb_notes_ws
                    else:
                        # add the first stage column
                        result = [{
                            '__context': {'group_by': groupby[1:]},
                            '__domain': domain + [dom_not_in],
                            'stage_id': (stages[0].id, stages[0].name),
                            'stage_id_count': nb_notes_ws,
                            '__fold': stages[0].name,
                        }] + result
            else:  # if stage_ids is empty, get note without user's stage
                nb_notes_ws = self.search_count(domain)
                if nb_notes_ws:
                    result = [{  # notes for unknown stage
                        '__context': {'group_by': groupby[1:]},
                        '__domain': domain,
                        'stage_id': False,
                        'stage_id_count': nb_notes_ws
                    }]
                else:
                    result = []
            return result
        return super(JobNote, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.multi
    def action_close(self):
        return self.write({'open': False, 'date_done': fields.date.today()})

    @api.multi
    def action_open(self):
        return self.write({'open': True})
                        
class note_note(models.Model):
    _inherit = 'note.note'
    
    construction_proj_id = fields.Many2one('project.project','Construction Project')
    responsible_user = fields.Many2one('res.users','Responsible Person')
    project_note_id  =  fields.Many2one('project.project', 'Project')
    job_note_id = fields.Many2one('job.order','Job Order')

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    boq_type = fields.Selection([('machine_qui','Machinery / Equipment'),('worker','Worker / Resource'),('work_package','Work Cost Package'),('subcontract','Subcontract')],'BOQ Type')

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    #job_order_id = fields.Many2one('job.order',string="Task / Job Order")  
    material_requisition_id = fields.Many2one('job.order','Job Material Requisition') 
    job_order_user_id = fields.Many2one('res.users',string="Task / Job Order User")
    construction_project_id = fields.Many2one('project.project',string="Construction Project")
    analytic_account_id = fields.Many2one('account.analytic.line',string="Analytic Account")
    
class JobType(models.Model):
    _name = 'job.type'
    
    name = fields.Char("Name")
    code = fields.Char("Code")
    job_type = fields.Selection([('material','Material'),('labour','Labour'),('overhead','Overhead')],"Job Type")
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'    
    
    job_order_id = fields.Many2one('job.order',string="Job Cost Center")
    job_cost_sheet_id = fields.Many2one('job.cost.sheet',string="Job Cost Sheet")
    project_id = fields.Many2one('project.project',string='Project')
    
class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'    
    
    job_cost_sheet_id = fields.Many2one('job.cost.sheet',string="Job Cost Center")

class PruchaseOrder(models.Model):
    _inherit = 'purchase.order'

    job_id = fields.Many2one('job.cost.sheet',string='Job')
    project_id = fields.Many2one('project.project',string='Project')
    
