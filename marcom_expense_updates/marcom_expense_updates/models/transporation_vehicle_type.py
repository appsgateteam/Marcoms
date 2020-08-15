# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class TransportaionVehicleType(models.Model):
    _name = "transportaion.vehicle.type" 



    name = fields.Char('Vehicle Type',  required=True)


      
      

