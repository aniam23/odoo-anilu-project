# -*- coding: utf-8 -*-

from odoo import models, fields, api

class gvwr_manager(models.Model):
    _name = 'vin_generator.gvwr_manager'
    _table = 'gvwr_manager_relation'
    _description = 'Manages the GVWR that are linked to products'

    name = fields.Char(compute="calculate_name")
    weight_lb = fields.Integer(string="Pounds GVWR")
    weight_kg = fields.Integer(string="Kilogram PNBV", compute="calculate_kg_from_pounds")

    products_relation = fields.One2many('product.template', 'gvwr_related')
    
    product_child_relation = fields.One2many('product.product', 'gvwr_child')

    @api.depends("weight_lb")
    def calculate_kg_from_pounds(self):
        for record in self:
            record.weight_kg = int(float(record.weight_lb) / 2.205)
    
    @api.depends("weight_lb")
    def calculate_name(self):
        for record in self:
            record.name = "GVWR " + str(record.weight_lb) + " lb"



