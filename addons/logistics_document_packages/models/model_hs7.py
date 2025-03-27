
from odoo import models, fields

class CustomerStickers(models.Model):
    _name = 'model.hs7'
    _description = 'model for hs7 trailers'
    ref_trailer = fields.Many2one(comodel_name='product.product', string="Seleccionar producto")
    name = fields.Char(string="Name")
    model = fields.Char(string="Modelo HS7")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")


  