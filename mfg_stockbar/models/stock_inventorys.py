# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    product_barcode = fields.Char(related='product_id.barcode', readonly=False)
    dummy_id = fields.Char(compute='_compute_dummy_id', inverse='_inverse_dummy_id')

    def _compute_dummy_id(self):
        pass

    def _inverse_dummy_id(self):
        pass


class StockInventory(models.Model):
    _name = 'stock.inventory'
    _inherit = ['stock.inventory', 'barcodes.barcode_events_mixin']

    scan_location_id = fields.Many2one('stock.location', 'Scanned Location', store=False)

    def action_client_action(self):
        """ Open the mobile view specialized in handling barcodes on mobile devices.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'stock_barcode_inventory_client_action',
            'target': 'fullscreen',
            'params': {
                'model': 'stock.inventory',
                'inventory_id': self.id,
            }
        }

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        blablabla.
        """
        inventories = self.read([
            'line_ids',
            'location_id',
            'name',
            'state',
            'company_id',
        ])
        for inventory in inventories:
            inventory['line_ids'] = self.env['stock.inventory.line'].browse(inventory.pop('line_ids')).read([
                'product_id',
                'location_id',
                'product_qty',
                'theoretical_qty',
                'product_uom_id',
                'prod_lot_id',
                'dummy_id',
            ])
            for line_id in inventory['line_ids']:
                line_id['product_id'] = self.env['product.product'].browse(line_id.pop('product_id')[0]).read([
                    'id',
                    'display_name',
                    'tracking',
                    'barcode',
                ])[0]
                line_id['location_id'] = self.env['stock.location'].browse(line_id.pop('location_id')[0]).read([
                    'id',
                    'display_name',
                    'parent_path'
                ])[0]
            inventory['location_id'] = self.env['stock.location'].browse(inventory.pop('location_id')[0]).read([
                'id',
                'display_name',
                'parent_path',
            ])[0]
            inventory['group_stock_multi_locations'] = self.env.user.has_group('stock.group_stock_multi_locations')
            inventory['group_tracking_owner'] = self.env.user.has_group('stock.group_tracking_owner')
            inventory['group_tracking_lot'] = self.env.user.has_group('stock.group_tracking_lot')
            inventory['group_production_lot'] = self.env.user.has_group('stock.group_production_lot')
            inventory['group_uom'] = self.env.user.has_group('uom.group_uom')
            inventory['actionReportInventory'] = self.env.ref('stock.action_report_inventory').id
            if self.env.user.company_id.nomenclature_id:
                inventory['nomenclature_id'] = [self.env.user.company_id.nomenclature_id.id]
        return inventories

    @api.model
    def open_new_inventory(self):
        use_form_handler = self.env['ir.config_parameter'].sudo().get_param('mfg_stockbar.use_form_handler')
        if use_form_handler:
            action = self.env.ref('mfg_stockbar.stock_inventory_action_new_inventory').read()[0]
            if self.env.ref('stock.warehouse0', raise_if_not_found=False):
                new_inv = self.env['stock.inventory'].create({
                    'filter': 'partial',
                    'name': fields.Date.context_today(self),
                })
                new_inv.action_start()
                action['res_id'] = new_inv.id
        else:
            action = self.env.ref('mfg_stockbar.stock_barcode_inventory_client_action').read()[0]
            if self.env.ref('stock.warehouse0', raise_if_not_found=False):
                new_inv = self.env['stock.inventory'].create({
                    'filter': 'partial',
                    'name': fields.Date.context_today(self),
                })
                new_inv.action_start()
                action['res_id'] = new_inv.id

                params = {
                    'model': 'stock.inventory',
                    'inventory_id': new_inv.id,
                }
                action['context'] = {'active_id': new_inv.id}
                action = dict(action, target='fullscreen', params=params)

        return action

    def _add_product(self, product, qty=1.0):
        corresponding_line = self.line_ids.filtered(lambda r: r.product_id.id == product.id and (self.scan_location_id.id == r.location_id.id or not self.scan_location_id))
        if corresponding_line:
            corresponding_line[0].product_qty += qty
        else:
            StockQuant = self.env['stock.quant']
            company_id = self.company_id.id
            if not company_id:
                company_id = self._uid.company_id.id
            dom = [('company_id', '=', company_id), ('location_id', '=', self.scan_location_id.id or self.location_id.id), ('lot_id', '=', False),
                        ('product_id','=', product.id), ('owner_id', '=', False), ('package_id', '=', False)]
            quants = StockQuant.search(dom)
            th_qty = sum([x.quantity for x in quants])
            self.line_ids += self.line_ids.new({
                'location_id': self.scan_location_id.id or self.location_id.id,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'theoretical_qty': th_qty,
                'product_qty': qty,
            })
        return True

    def on_barcode_scanned(self, barcode):
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)
            return

        product_packaging = self.env['product.packaging'].search([('barcode', '=', barcode)])
        if product_packaging.product_id:
            self._add_product(product_packaging.product_id, product_packaging.qty)
            return

        location = self.env['stock.location'].search([('barcode', '=', barcode)])
        if location:
            self.scan_location_id = location[0]
            return
