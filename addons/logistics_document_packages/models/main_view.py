from odoo import models, fields, api
import base64
import logging
#vista principal del modelo de logistica
class MainView(models.Model):
    _name = 'main.view'
    _description = 'Main view of pending shipments'
    #estados de envio de las cargas
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

   
    def _update_sale_orders_pending_to_manufacure(self):
    # ordenes de venta confirmadas 
        self.sale_orders_pending_to_manufacure = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'waiting')
            ])
    #ordenes de venta en estado ready en delivery
    def _update_sale_order_waiting_ids(self):
        self.sale_order_waiting_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'assigned')
            ])
    #ordenes de venta en espera de documentos de logistica en estado done en delivery
    def _update_sale_order_in_wait_of_docuemnts(self):
        sale_order_in_transit_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'done')
            ])  
        other_list = []
        for so in sale_order_in_transit_ids:
            if so.proof_of_delivery_done == False:
                other_list.append(so.id)
        self.sale_order_in_wait_of_docuemnts = other_list  
    #ordenes en transito 
    def _update_sale_order_in_transit_ids(self):
        sale_order_in_transit_ids = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('picking_ids.state', '=', 'done')
            ]) 
        aux_list = []
        for so in sale_order_in_transit_ids:
            if so.logistic_documents_generated == True and so.proof_of_delivery_done == False:
                aux_list.append(so.id)
        self.sale_order_in_transit_ids = aux_list if aux_list else []
    
    #enviar notificacion a finanzas despues de generar el comprobante de entrega de la orden de venta.
    def _update_sale_order_pod_ids(self):
        # Busca todas las órdenes de venta que ya tengan adjuntos los comprobantes de la entrega
        orders = self.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('picking_ids.state', '=', 'done')
        ], order='fechapro asc')
        
        # Filtra solo las órdenes con comprobante de entrega (POD) completado
        pod_completed = orders.filtered(lambda so: so.proof_of_delivery_done)
        # Obtiene los IDs de órdenes ya procesadas anteriormente
        already_processed = self.sale_order_pod_ids.ids
        # Identifica órdenes nuevas (que no estaban en el listado anterior)
        new_orders = pod_completed.filtered(lambda so: so.id not in already_processed)
        # Actualiza el campo con TODAS las órdenes con POD completado
        self.sale_order_pod_ids = pod_completed
        # Si no hay órdenes nuevas, termina el proceso
        if not new_orders:
            return
        # Obtiene el equipo de contabilidad (grupo 'account.group_account_manager')
        accounting_team = self.sudo().env.ref('account.group_account_manager').users
        if not accounting_team:
            return
        # Busca el canal de notificaciones o lo crea si no existe
        channel = self.sudo().env['mail.channel'].search([
            ('name', '=', '🚚 POD Completado - Facturación')
        ], limit=1) or self.sudo().env['mail.channel'].sudo().create({
            'name': '🚚 POD Completado - Facturación',
            'channel_type': 'channel',
            'group_public_id': self.sudo().env.ref('account.group_account_manager').id
        })
        # Para cada orden nueva, envía notificación
        for order in new_orders:
            # Publica mensaje en el canal con formato HTML
            msg = channel.sudo().message_post(
                body=f"""
                <div style='background-color: #e3fae3; padding: 15px; border-radius: 8px;'>
                    <b style="color:#000000;">📦 CARGA ENTREGADA AL DEALER</b>
                    <p style='margin-top: 10px; color:#000000;'>
                        <b>Orden:</b> <a href="/web#id={order.id}&model=sale.order" style="color: #000000;">{order.name}</a><br/>
                        <b>Cliente:</b> {order.partner_id.name}<br/>
                        <b>Total:</b> {order.amount_total} {order.currency_id.name}<br/>
                        <b>Fecha:</b> {fields.Date.today()}
                    </p>
                    <p style='color: #056608; font-weight: bold;'>
                        ✅ Carga entregada con exito, Verificar Factura
                    </p>
                </div>
                """,
                subject=f"Carga entregada con exito - {order.name}",
                message_type='comment',
                partner_ids=accounting_team.mapped('partner_id').ids,
                email_layout_xmlid='mail.mail_notification_light'
            )
            
            # Registra también en el chatter de la orden
            order.sudo().message_post(
                body=f"<p>Notificación enviada al equipo de contabilidad: {msg.body}</p>",
                message_type='comment',
                subtype_xmlid='mail.mt_note' 
            )

    def update(self):
        """Actualiza todos los conjuntos de órdenes."""
        self._update_sale_order_next_ids()
        self._update_sale_orders_pending_to_manufacure()
        self._update_sale_order_waiting_ids()
        self._update_sale_order_in_wait_of_docuemnts()
        self._update_sale_order_in_transit_ids()
        self._update_sale_order_pod_ids()
