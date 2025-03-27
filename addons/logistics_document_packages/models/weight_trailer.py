from odoo import models, fields

class Weight(models.Model):
    _name = 'weight.info'
    _description = 'weight of trailers'

    ref_trailer = fields.Many2one(comodel_name='product.product', string="Seleccionar producto")
    name = fields.Text(string="Name")
    weight = fields.Integer(string="Peso remolque")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    
