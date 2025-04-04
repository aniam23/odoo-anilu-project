from odoo import models, fields, api

class MainView(models.Model):
    _name = 'main.view'
    _description = 'Main view of pending shipments'
    
    upcoming_upload = fields.Boolean('PROXIMAS CARGAS')
    rts = fields.Boolean("CARGAS RTS EN ESPERA")
    sos_ready = fields.Boolean("SO LISTOS PARA ENVIAR")
    transit = fields.Boolean("EN TRANSITO")
    proof = fields.Boolean("COMPROBANTE DE ENTREGA")
    delivered = fields.Boolean("ENTREGADO")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    state = fields.Selection([
        ('PROXIMAS CARGAS', 'PROXIMAS CARGAS'),
        ('CARGAS RTS EN ESPERA', 'CARGAS RTS EN ESPERA'),
        ('SO LISTOS PARA ENVIAR', 'SO LISTOS PARA ENVIAR'),
        ('EN TRANSITO', 'EN TRANSITO'),
        ('COMPROBANTE DE ENTREGA', 'COMPROBANTE DE ENTREGA'),
        ('ENTREGADO', 'ENTREGADO'),
    ], string='State', default='PROXIMAS CARGAS')

    sale_order_ids = fields.Many2many(
        'sale.order',
        string="Órdenes de Venta",
        compute="_compute_sale_orders",
        store=False
    )

    @api.depends('state')
    def _compute_sale_orders(self):
        for record in self:
            if record.state == 'PROXIMAS CARGAS':
                record.sale_order_ids = self.env['sale.order'].search([
                    ('state', 'in', ['draft', 'sent']),('picking_ids', '=', False) 
                ])
            elif record.state == 'CARGAS RTS EN ESPERA':
                record.sale_order_ids = self.env['sale.order'].search([
                    ('state', '=', 'sale')
                ])
            elif record.state == 'SO LISTOS PARA ENVIAR':
               record.sale_order_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'waiting')
            ])
            
            elif record.state == 'EN TRANSITO':
                record.sale_order_ids = self.env['sale.order'].search([
                    ('state', '=', 'sale'),
                    ('picking_ids.state', 'in', ['ready', 'assigned'])
                ])
            
            elif record.state == 'COMPROBANTE DE ENTREGA':
                record.sale_order_ids = self.env['sale.order'].search([
                    ('state', '=', 'sale'),
                    ('picking_ids.state', '=', 'done'),
                ])

            elif record.state == 'ENTREGADO':
                record.sale_order_ids = self.env['sale.order'].search([
                    ('state', '=', 'sale'),
                    ('picking_ids.state', '=', 'done'),
                    
                ])

            else:
                record.sale_order_ids = False

    def next_action(self):
        current_state = self.state
        states = ['PROXIMAS CARGAS','CARGAS RTS EN ESPERA', 'SO LISTOS PARA ENVIAR', 'EN TRANSITO', 'COMPROBANTE DE ENTREGA','ENTREGADO']
        if current_state in states:
            current_index = states.index(current_state)
            if current_index < len(states) - 1:
                self.state = states[current_index + 1]
                self._compute_sale_orders()  
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'main.view',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def previous_action(self):
        current_state = self.state
        states = ['PROXIMAS CARGAS','CARGAS RTS EN ESPERA', 'SO LISTOS PARA ENVIAR', 'EN TRANSITO', 'COMPROBANTE DE ENTREGA','ENTREGADO']
        if current_state in states:
            current_index = states.index(current_state)
            if current_index > 0:
                self.state = states[current_index - 1]
                self._compute_sale_orders()  
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'main.view',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }