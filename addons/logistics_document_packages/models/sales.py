from odoo import models, fields, api
from PyPDF2 import PdfFileMerger
import base64
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    # email_sent = fields.Integer(string='Email Sent', compute= "_send_invoice_email")
    email_sent = fields.Integer(string='Email Sent')
    logistics_data = fields.One2many('logistics.log_document', 'sale_order',string='datos de logistica')
    fletero = fields.Text(string="Fletero")
    archive_file = fields.Binary(string="Subir Archivo")
    archive_filename = fields.Char(string="Nombre del Archivo")
    partner_address_full = fields.Char(
        string="Customer Address",
        compute='_compute_partner_address_full',
    )
    downloaded_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='sale_order_downloaded_attachment_rel',
        column1='sale_order_id',
        column2='attachment_id',
        string="Archivos Logistica",
    )

    proof_of_delivery = fields.Many2many(
        comodel_name='ir.attachment',
        relation='sale_order_proof_of_delivery_rel',
        column1='sale_order_id',
        column2='attachment_id',
        string="Evidencias de entrega"
    )


    logistic_documents_generated = fields.Boolean(compute='_compute_logistic_documents_generated', string='Documentos de logistica creados')
    proof_of_delivery_done = fields.Boolean(compute='_compute_proof_of_delivery_done', string='Proof of delivery done')
    
    # sequence = fields.Integer(string="Number", compute='_compute_sequence',  options="{'style': 'text-align: center;'}", store=False)

    def _compute_sequence(self):
        for i, record in enumerate(self, start=1):
            record.sequence = str(i)


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
            # 'flags': {
            #     'form': {
            #         'action_buttons': True,
            #         'options': {'mode': 'edit'}  
            #     }
            # },
            # 'context': {
            #     'form_view_ref': 'tu_modulo.sale_order_form_custom_edit',
            #     'default_fletero': self.env['sale.order'].browse(order_id).fletero
            # }
        }
    @api.depends('proof_of_delivery')
    def _compute_proof_of_delivery_done(self):
        for record in self:
            if record.proof_of_delivery:
                record.proof_of_delivery_done = True
            else:
                record.proof_of_delivery_done = False

    @api.depends('logistics_data')
    def _compute_logistic_documents_generated(self):
        for record in self:
            if record.logistics_data:
                record.logistic_documents_generated = True
            else:
                record.logistic_documents_generated = False
        

    @api.depends('partner_id')
    def _compute_partner_address_full(self):
        for order in self:
            partner = order.partner_id
            if partner:
                address_lines = [
                    partner.name or '',
                    partner.street or '',
                    partner.street2 or '',
                    f"{partner.city or ''} {partner.state_id.code or ''} {partner.zip or ''}".strip(),
                    partner.country_id.name or ''
                ]
                order.partner_address_full = "\n".join(filter(bool, address_lines))
            else:
                order.partner_address_full = ""

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': 'Adjuntos',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', 'sale.order'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'sale.order',
                'default_res_id': self.id,
            },
            'target': 'current'
        }

    def action_show_downloads(self):
        self.ensure_one()
        return {
            'name': 'Archivos Descargados',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', 'logistics.log_document'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'logistics.log_document',
                'default_res_id': self.id,
            },
            'target': 'current'
        }

    def write(self, vals):
        for record in self:
            if 'delivery_status' in vals:
                delivery_status_old = record.delivery_status
                res = super(SaleOrder, record).write(vals)
                delivery_status_new = record.delivery_status
                if (
                    delivery_status_old != 'fully_delivered' and
                    delivery_status_new == 'fully_delivered' and
                    not record.email_sent
                ):
                    record._send_invoice_email()
                return res
        return super().write(vals)
    # @api.depends("picking_ids","picking_ids.state")
    @api.onchange("delivery_status")
    def _send_invoice_email(self):
        for order in self:
            if not order.invoice_ids:
                return
            if not order.partner_id.email:
                return

            invoice = order.invoice_ids[0]
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'account.report_invoice', [invoice.id]
            )
            pdf_base64 = base64.b64encode(pdf_content)

            attachment = self.env['ir.attachment'].create({
                'name': f'Factura_{invoice.name}.pdf',
                'type': 'binary',
                'datas': pdf_base64,
                'res_model': 'sale.order',
                'res_id': order.id,
                'mimetype': 'application/pdf'
            })

            email_vals = {
                'subject': f'Factura {invoice.name}',
                'body_html': '<p>Adjunto encontrará su factura.</p>',
                'email_to': order.partner_id.email,
                'attachment_ids': [(6, 0, [attachment.id])]
            }

            mail = self.env['mail.mail'].create(email_vals)
            mail.send()
            order.email_sent = True



        


   