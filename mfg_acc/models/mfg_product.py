from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_cost_structure(self):
        products = self.mapped('product_variant_id')
        return self.env.ref('mfg_acc.action_cost_struct_product_template').report_action(products, config=False)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_cost_structure(self):
        return self.env.ref('mfg_acc.action_cost_struct_product_template').report_action(self, config=False)
