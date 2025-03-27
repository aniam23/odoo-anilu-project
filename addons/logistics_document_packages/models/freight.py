
from odoo import models, fields

class CustomerFreight(models.Model):
    _name = 'freight.partner'
    _description = 'Price of Freight'


    ref_cliente = fields.Many2many(comodel_name='res.partner', string="Cliente")
    name = fields.Text(string="Name")
    freight_prices = fields.Float(string="Freight Price")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    def freight_registry(self, docids, data=None):
        sale_order = self.env['sale.order'].browse(data.get('sale_order_id'))
        if not sale_order:
            return {'error': 'Sale order not found'}
        partner = sale_order.partner_id
        if not partner:
            return {'error': 'No partner associated with this sale order'}
        freight_partner = self.env['freight.partner'].search([
            ('ref_cliente', 'in', [partner.id])
        ], limit=1)
        if freight_partner:
            freight_price = freight_partner.freight_prices
            freight_number = freight_partner.id
        else:
            freight_price = 0.0
            freight_number = "No registrado"

        return {
            'sale_order_id': sale_order.id,
            'partner_name': partner.name,
            'freight_price': freight_partner.freight_prices,
            'freight_number': freight_number,
            'freight_price': freight_price
        }


