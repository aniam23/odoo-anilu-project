
from odoo import models, fields

class FreightPartner(models.Model):
    _name = 'freight.partner'
    _description = 'Price of Freight'
    #Carga inicial para dar de alta a los fleteros
    ref_cliente = fields.Many2many(comodel_name='res.partner', string="Cliente")
    name = fields.Text(string="Name")
    freight_prices = fields.Float(string="Freight Price")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    #busqueda del partner en la orden de venta para obtener el precio designado.
    def freight_registry(self, docids, data=None):
        """
        Gestiona la información  sobre los costos de fletes asociados a órdenes de venta.
        Esta función:
        busca en la orden de venta el cliente y lo compara con los registros dados de alta en 
        la carga inicial para los fletes para despues retornar el valor del flete asignado.
        """
        sale_order = self.env['sale.order'].browse(data.get('sale_order_id')) #busca la orden de venta
        if not sale_order: #si no encuentra una orden de venta
            return {'error': 'Sale order not found'} 
        partner = sale_order.partner_id
        if not partner: #si la venta no tiene un cliente asociado
            return {'error': 'No partner associated with this sale order'}
        #busca en el modelo freight.partner la referencia del cliente para posteriormente regresar el valor correspondiente del flete.
        freight_partner = self.env['freight.partner'].search([
            ('ref_cliente', 'in', [partner.id])
        ], limit=1)
        if freight_partner: #si encuentra el partner 
            freight_price = freight_partner.freight_prices #devuelve el valor del flete correspondiente al cliente
            freight_number = freight_partner.id # id del partner
        else: #si no lo encuentra regresa un mensaje de no registrado
            freight_price = 0.0
            freight_number = "No registrado"
        return {
            'sale_order_id': sale_order.id,
            'partner_name': partner.name,
            'freight_price': freight_partner.freight_prices,
            'freight_number': freight_number,
            'freight_price': freight_price
        }


