# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class MealType(models.Model):
    _name = "meal.type" 



    name = fields.Char('Meal Type',  required=True)


      
      

