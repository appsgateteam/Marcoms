# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math

class MaterialPurchaseRequisition(models.Model):
    _inherit = "material.purchase.requisition"

    job_order_id = fields.Many2one('job.order','Project / Job Order')