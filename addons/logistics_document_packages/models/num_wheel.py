from odoo import models, fields

class WhellNut(models.Model):
    _name = 'wheel.nut'
    _description = 'Whell Nut'
   
    ref_product = fields.Many2many(comodel_name='product.product', string="Seleccionar producto (llantas)")
    name = fields.Char(string="Name")
    number_wheel_nut = fields.Integer(string="Número de Birlos")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    
    def whell_nut_registry(self, docids, data=None):
       
        sale_order = self.env['sale.order'].browse(data.get('sale_order_id'))
        if not sale_order:
            return {'error': 'Sale order not found'}
        tires_wheel = sale_order.order_line.filtered(lambda line: line.product_id).mapped('product_id')
        if not tires_wheel:
            return {'error': 'No associated product with this sale order'}
        product_whell = self.env['whell.nut'].search([
            ('ref_whell_nut', 'in', [product.id for product in tires_wheel])
        ], limit=1)
        if product_whell:
            wheel_num = product_whell.number_wheel_nut
        else:
            wheel_num = 0.0

   
        return {
            'sale_order_id': sale_order.id,
            'wheel_name': tires_wheel[0].name if tires_wheel else 'No product found',
            'wheel_num': wheel_num,
        }

