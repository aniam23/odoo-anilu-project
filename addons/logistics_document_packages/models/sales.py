from odoo import models, fields, api
from PyPDF2 import PdfFileMerger
import base64
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    #modelo heredado para agregar campos a sale order
    email_sent = fields.Integer(string='Email Sent')
    logistics_data = fields.One2many('logistics.log_document', 'sale_order',string='datos de logistica')
    fletero = fields.Text(string="Fletero")
    archive_file = fields.Binary(string="Subir Archivo")
    archive_filename = fields.Char(string="Nombre del Archivo")
    partner_address_full = fields.Char(
        string="Customer Address",
        compute='_compute_partner_address_full',
    )
    #documentos descargados desde modulo logistica
    downloaded_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='sale_order_downloaded_attachment_rel',
        column1='sale_order_id',
        column2='attachment_id',
        string="Archivos Logistica",
    )
    #subir archivos a la sale order (comprobantes de entrega de logistica)
    proof_of_delivery = fields.Many2many(
        comodel_name='ir.attachment',
        relation='sale_order_proof_of_delivery_rel',
        column1='sale_order_id',
        column2='attachment_id',
        string="Evidencias de entrega"
    )
    logistic_documents_generated = fields.Boolean(compute='_compute_logistic_documents_generated', string='Documentos de logistica creados')
    proof_of_delivery_done = fields.Boolean(compute='_compute_proof_of_delivery_done', string='Proof of delivery done')
    #accion que permite editar la orden de venta
    def open_sale_order_edit(self):
        self.ensure_one()
        order_id = self.env.context.get('active_id') or self.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Orden',
            'res_model': 'sale.order',
            'res_id': order_id, 
            'view_mode': 'form',
            'view_id': self.env.ref('logistics_document_packages.custom_sale_order').id,
            'target': 'current',
        }
    #subir archivos
    @api.depends('proof_of_delivery')
    def _compute_proof_of_delivery_done(self):
         # Itera sobre cada registro (orden de venta)
        for record in self:
        # Si existe proof_of_delivery marca como True
            if record.proof_of_delivery:
                record.proof_of_delivery_done = True
        else:
            record.proof_of_delivery_done = False
    #acumula los documentos generados 
    @api.depends('logistics_data')
    def _compute_logistic_documents_generated(self):
        for record in self:
            # Si existe proof_of_delivery marca como True
            if record.logistics_data:
                record.logistic_documents_generated = True
            else:
                record.logistic_documents_generated = False
        
    #direccion completa del cliente
    @api.depends('partner_id')
    def _compute_partner_address_full(self):
         # Itera sobre cada orden
        for order in self:
            # Obtiene el partner asociado
            partner = order.partner_id
            if partner:
                # Construye las líneas de dirección
                address_lines = [
                    partner.name or '',  # Nombre del cliente
                    partner.street or '',  # Calle principal
                    partner.street2 or '',  # Calle secundaria
                    # Ciudad + Estado + Código postal
                    f"{partner.city or ''} {partner.state_id.code or ''} {partner.zip or ''}".strip(),
                    partner.country_id.name or ''  # País
                ]
                # Une las líneas no vacías con saltos de línea
                order.partner_address_full = "\n".join(filter(bool, address_lines))
            else:
                # Si no hay partner, regresa la dirección vacía
                order.partner_address_full = ""


    # documentos generados 
    def action_open_attachments(self):
        # Asegura que se trabaje con un solo registro
        self.ensure_one()
        # Retorna acción de ventana
        return {
        'name': 'Adjuntos',  # Título de la ventana
        'type': 'ir.actions.act_window',  # Tipo de acción
        'res_model': 'ir.attachment',  # Modelo a mostrar
        'view_mode': 'kanban,tree,form',  # Vistas disponibles
        # Filtra adjuntos de esta orden de venta
        'domain': [('res_model', '=', 'sale.order'), ('res_id', '=', self.id)],
        'context': {
            'default_res_model': 'sale.order',  # Modelo por defecto
            'default_res_id': self.id,  # ID por defecto
        },
        'target': 'current'  # Abre en la misma ventana
    }

    
    def write(self, vals):
        # Itera sobre cada registro
        for record in self:
            # Si se está modificando delivery_status
            if 'delivery_status' in vals:
                # Guarda el estado anterior
                delivery_status_old = record.delivery_status
                # Ejecuta el write original
                res = super(SaleOrder, record).write(vals)
                # Obtiene el nuevo estado
                delivery_status_new = record.delivery_status
                # Verifica si cambió a fully_delivered y no se ha enviado email
                if (
                    delivery_status_old != 'fully_delivered' and
                    delivery_status_new == 'fully_delivered' and
                    not record.email_sent
                ):
                    # Envía el email de factura
                    record._send_invoice_email()
                return res
            # Si no se modificó delivery_status, ejecuta write normal
            return super().write(vals)
    #enviar factura por correo 
    @api.onchange("delivery_status")
    def _send_invoice_email(self):
        # Itera sobre cada orden
        for order in self:
            # Si no tiene facturas, no hace nada
            if not order.invoice_ids:
                return
            # Si el cliente no tiene email, no hace nada
            if not order.partner_id.email:
                return
    
            # Toma la primera factura
            invoice = order.invoice_ids[0]
            
            # Genera el PDF de la factura
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'account.report_invoice', [invoice.id]
            )
            # Codifica el PDF en base64
            pdf_base64 = base64.b64encode(pdf_content)
    
            # Crea un adjunto con la factura
            attachment = self.env['ir.attachment'].create({
                'name': f'Factura_{invoice.name}.pdf',  # Nombre del archivo
                'type': 'binary',  # Tipo binario
                'datas': pdf_base64,  # Contenido del PDF
                'res_model': 'sale.order',  # Modelo relacionado
                'res_id': order.id,  # ID del registro
                'mimetype': 'application/pdf'  # Tipo MIME
            })
    
            # Prepara los valores del email
            email_vals = {
                'subject': f'Factura {invoice.name}',  # Asunto
                'body_html': '<p>Adjunto encontrará su factura.</p>',  # Cuerpo
                'email_to': order.partner_id.email,  # Destinatario
                'attachment_ids': [(6, 0, [attachment.id])]  # Adjuntos
            }
    
            # Crea y envía el email
            mail = self.env['mail.mail'].create(email_vals)
            mail.send()
            # Marca que ya se envió el email
            order.email_sent = True


        


   