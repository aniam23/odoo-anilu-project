from odoo import models, fields, api
import base64
import logging

class MainView(models.Model):
    _name = 'main.view'
    _description = 'Main view of pending shipments'
    sale_order_next_ids = fields.Many2many(
        'sale.order',
        relation='main_view_sale_order_next_rel',
        column1='main_view_id',
        column2='sale_order_id',
        string="Próximas Cargas",
        compute="_update_sale_order_next_ids",
        ondelete='cascade'
    )

    sale_orders_pending_to_manufacure = fields.Many2many(
        'sale.order',
        relation='main_view_sale_order_pending_rel',
        column1='main_view_id',
        column2='sale_order_id',
        string="En Espera de Manufactura",
        compute="_update_sale_orders_pending_to_manufacure",
        ondelete='cascade'
    )

    sale_order_waiting_ids = fields.Many2many(
        'sale.order',
        relation='main_view_sale_order_waiting_rel',
        column1='main_view_id',
        column2='sale_order_id',
        string="Cargas RTS en Espera",
        compute="_update_sale_order_waiting_ids",
        ondelete='cascade'
    )

    sale_order_in_wait_of_docuemnts = fields.Many2many(
        'sale.order',
        relation='main_view_sale_order_wait_docs_rel',
        column1='main_view_id',
        column2='sale_order_id',
        string="En Espera de Documentos",
        compute="_update_sale_order_in_wait_of_docuemnts",
        ondelete='cascade'
    )

    sale_order_in_transit_ids = fields.Many2many(
        'sale.order',
        relation='main_view_sale_order_transit_rel',
        column1='main_view_id',
        column2='sale_order_id',
        string="En Tránsito",
        compute="_update_sale_order_in_transit_ids",
        ondelete='cascade'
    )

    sale_order_pod_ids = fields.Many2many(
        'sale.order',
        relation='main_view_sale_order_pod_rel',
        column1='main_view_id',
        column2='sale_order_id',
        string="Comprobante de Entrega",
        compute="_update_sale_order_pod_ids",
        ondelete='cascade'
    )

    
    def _update_sale_order_next_ids(self):
        self.sale_order_next_ids = self.env['sale.order'].search([
                ('state', 'in', ['draft', 'sent']),
                ('picking_ids', '=', False)
            ], order='fechapro asc')  

    def _update_sale_orders_pending_to_manufacure(self):
        self.sale_orders_pending_to_manufacure = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'waiting')
            ], order='fechapro asc ')

    def _update_sale_order_waiting_ids(self):
        self.sale_order_waiting_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'assigned')
            ], order='fechapro asc')

    def _update_sale_order_in_wait_of_docuemnts(self):
        sale_order_in_transit_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'done')
            ], order='fechapro asc')  
        other_list = []
        for so in sale_order_in_transit_ids:
            if so.proof_of_delivery_done == False:
                other_list.append(so.id)
        self.sale_order_in_wait_of_docuemnts = other_list  

    def _update_sale_order_in_transit_ids(self):
        sale_order_in_transit_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'done')
            ], order='fechapro asc') 
        aux_list = []
        for so in sale_order_in_transit_ids:
            if so.logistic_documents_generated == True and so.proof_of_delivery_done == False:
                aux_list.append(so.id)
        self.sale_order_in_transit_ids = aux_list if aux_list else []

    def _update_sale_order_pod_ids(self):
        sale_order_pod_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'done')
            ], order='fechapro asc')  
        aux_list = []
        for so in sale_order_pod_ids:
            if so.proof_of_delivery_done == True:
                aux_list.append(so.id)
        self.sale_order_pod_ids = aux_list

    def update(self):
        """Actualiza todos los conjuntos de órdenes."""
        self._update_sale_order_next_ids()
        self._update_sale_orders_pending_to_manufacure()
        self._update_sale_order_waiting_ids()
        self._update_sale_order_in_wait_of_docuemnts()
        self._update_sale_order_in_transit_ids()
        self._update_sale_order_pod_ids()
