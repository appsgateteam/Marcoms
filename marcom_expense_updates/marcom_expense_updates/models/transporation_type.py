# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class TransportaionType(models.Model):
    _name = "transportaion.type" 



    name = fields.Char('Type',  required=True)


      
      

