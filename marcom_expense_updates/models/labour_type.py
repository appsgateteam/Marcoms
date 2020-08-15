# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class LabourType(models.Model):
    _name = "labour.type" 



    name = fields.Char('Labour Type',  required=True)


      
      

