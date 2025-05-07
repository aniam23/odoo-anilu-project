from odoo import models, fields

class WhellNut(models.Model):
    _name = 'wheel.nut'
    _description = 'Whell Nut'
    # carga inicial para agregar los birlos de las llantas
    ref_product = fields.Many2many(comodel_name='product.product', string="Seleccionar llantas")
    name = fields.Char(string="Name")
    number_wheel_nut = fields.Integer(string="Número de Birlos")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    # buscar en el submenu las llantas registradas en la carga inicial para obtener el numero de birlos
    def whell_nut_registry(self, docids, data=None):
        """
        registra la carga inicial del numero de birlos de cada llanta que se utiliza
        """
        sale_order = self.env['sale.order'].browse(data.get('sale_order_id')) #busca la orden de venta
        if not sale_order:
            return {'error': 'Sale order not found'}
        tires_wheel = sale_order.order_line.filtered(lambda line: line.product_id).mapped('product_id') #busca en la lista de materiales del producto la llanta
        if not tires_wheel: #si no encuentra la llanta en el producto
            return {'error': 'No associated product with this sale order'}
        # despues busca en la carga inicial un registro que coincida con la llanta del producto para regresar el numero de birlos
        product_whell = self.env['whell.nut'].search([
            ('ref_whell_nut', 'in', [product.id for product in tires_wheel])
        ], limit=1)
        if product_whell:#si encuentra alguna coincidencia en la carga inicial
            wheel_num = product_whell.number_wheel_nut #regresa el numero de birlos
        else:
            wheel_num = 0.0
        return {
            'sale_order_id': sale_order.id,
            'wheel_name': tires_wheel[0].name if tires_wheel else 'No product found',
            'wheel_num': wheel_num,
        }

