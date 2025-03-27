from odoo import models, fields, api

class PrintVins(models.Model):
    _inherit = 'vin_generator.vin_generator'
    _description = 'Manages the GAWR that are linked to products'
    name = fields.Char(compute="calculate_name")
    weight_lb = fields.Integer(string="Pounds GAWR")
    weight_kg = fields.Integer(string="Kilogram PNBV", compute="calculate_kg_from_pounds")
    products_relation = fields.One2many('product.template', 'gvwr_related')


    @api.depends("weight_lb")
    def calculate_kg_from_pounds(self):
        for record in self:
            record.weight_kg = int(float(record.weight_lb) / 2.205)
    @api.depends("weight_lb")
    def calculate_name(self):
        for record in self:
            record.name = "GAWR " + str(record.weight_lb) + " lb"
