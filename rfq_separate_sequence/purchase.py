# -*- coding: utf-8 -*-
from odoo import fields, models, api

class purchase_order(models.Model):
    _inherit = "purchase.order"
    
    rfq_name = fields.Char('Rfq Reference', required=True, index=True, copy=False,
                            help="Unique number of the purchase order, "
                                 "computed automatically when the purchase order is created.")
    interchanging_rfq_sequence = fields.Char('RFQ Sequence')
    interchanging_po_sequence = fields.Char('Sequence')
                
    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
            name = self.env['ir.sequence'].next_by_code('purchase.order.quot') or 'New'
            vals['rfq_name'] = vals['name'] = name
            
        return super(purchase_order, self).create(vals)
        
    @api.multi
    def button_confirm(self):
        res =  super(purchase_order, self).button_confirm()
        for order in self:
            if order.interchanging_rfq_sequence:
                order.write({'name': order.interchanging_po_sequence})
            else:
                new_name = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
                order.write({'interchanging_rfq_sequence':order.name})
                order.write({'name': new_name})
            self.picking_ids.write({'origin': order.interchanging_po_sequence})
            if self.picking_ids:
                for pick in self.picking_ids:
                    pick.move_lines.write({'origin': order.interchanging_po_sequence}) 
        return res
    
    @api.multi
    def button_draft(self):
        res = super(purchase_order, self).button_draft()
        if self.interchanging_rfq_sequence:
            self.write({'interchanging_po_sequence':self.name})
            self.write({'name':self.interchanging_rfq_sequence})
        
        return res