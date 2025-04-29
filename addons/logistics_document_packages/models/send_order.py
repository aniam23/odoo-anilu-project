from odoo import models, fields, api
from odoo.exceptions import UserError
from io import BytesIO
import base64
import time
from PyPDF2 import PdfFileMerger
class SendOrder(models.Model):
    _name = 'send.order'
    _description = 'State of Send Orders Logistics'
    log_document_id = fields.Many2one('logistics.log_document', string='Log Document')
    sale_order = fields.Many2one('sale.order', string='Sales Orders')
    upcoming_upload = fields.Boolean('UPCOMING UPLOADS')
    rts = fields.Boolean("LOADS RTS DEALER")
    sos_ready = fields.Boolean("SOS READY TO SHIP")
    transit = fields.Boolean("IN TRANSIT")
    proof = fields.Boolean("PROOF OF DELIVERY")
    delivered = fields.Boolean("DELIVERED TO CUSTOMER")
    state = fields.Selection([
        ('UPCOMING UPLOADS', 'UPCOMING UPLOADS'),
        ('LOADS RTS DEALER', 'LOADS RTS DEALER'),
        ('SOS READY TO SHIP', 'SOS READY TO SHIP'),
        ('IN TRANSIT', 'IN TRANSIT'),
        ('PROOF OF DELIVERY', 'PROOF OF DELIVERY'),
        ('DELIVERED TO CUSTOMER', 'DELIVERED TO CUSTOMER'),
    ], string='State', default='UPCOMING UPLOADS')

    load = fields.Char('Load')
    name = fields.Char(string='Name')
    customer_name = fields.Char(string='Customer Name')
    customer_email = fields.Char(string='Customer Email')
    product_id = fields.Char(string='Product ID')
    invoice_number = fields.Char(string='Invoice Number')
    shipping_location = fields.Char(string='Shipping Location')
    ship_date = fields.Date(string='Ship Date')
    creation_log = fields.Text(string='Creation Log')
    due_date = fields.Date(string='Due Date')
    ship_to = fields.Char(string='Ship To')
    invoice_pdf = fields.Binary("Invoice PDF")
    hs7_dictionary_id = fields.Many2many('hs7.dictionary', 'send_order_id', string="HS7 Dictionary")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.depends('log_document_id')
    def _compute_log_document_name(self):
        for record in self:
            record.log_document_name = record.log_document_id.name if record.log_document_id else False

    @api.onchange('trigger_value_state')
    def _onchange_trigger_value_state(self):
        if self.trigger_value_state:
            self.trigger_value_state = False

    
    def create_send_order(self):
        sale_order = self.env.context.get('default_sale_order_id', False)
        if sale_order:
            sale_order = self.env['sale.order'].browse(sale_order)
            self.write({'sale_order_id': sale_order.id})
        return True
    
 
    def value_state(self):
        if not self:
            return {'error': 'No send order available'}
        if not self.hs7_dictionary_id:
            new_record = self.env['hs7.dictionary'].create({
                "customer_name": self.customer_name,
                "customer_email": self.customer_email,
                "product_id": self.product_id,
                "invoice_number": self.invoice_number,
                "shipping_location": self.shipping_location,
                "ship_date": self.ship_date,
                "creation_log": self.creation_log,
                "due_date": self.due_date,
                "ship_to": self.ship_to,
                "sale_order": self.sale_order.id
            })
            self.hs7_dictionary_id = [(4, new_record.id)]
            return {'success': 'HS7 Dictionary record created and associated'}

    def add_archive_in_state(self):
        if self.state == 'PROOF OF DELIVERY':
            finance_users = self.env.ref('account.group_account_manager').users
        if finance_users:
            body = f"""
            <p>Documento: <strong>{self.name}</strong></p>
            <p>Estado actual: <strong>PROOF OF DELIVERY</strong></p>
            <p>Por favor actualice el estado de la factura relacionada.</p>
            """
            self.message_notify(
                partner_ids=finance_users.mapped('partner_id').ids,
                body=body,
                subject=f"Proof of Delivery - {self.name}",
                record_name=self.name,
                attachments=[(attachment.name, attachment.datas) 
                           for attachment in self.attachment_ids],
                email_layout_xmlid='mail.mail_notification_light'
            )
            self.message_post(
                body=body,
                subject="Notificación enviada a Finanzas",
                message_type="comment"
            )

            attachment = self.env['ir.attachment'].create({
                'name': 'archive.pdf',  
                'datas': 'base64_encoded_data', 
                'type': 'binary',  
                'res_model':'ir.attachment', 
                'res_id': self.id, 
            })
            self.attachment_ids = [(4, attachment.id)]  
    
    def next_action(self):
        current_state = self.state
        states = ['UPCOMING UPLOADS','LOADS RTS DEALER', 'SOS READY TO SHIP', 'IN TRANSIT', 'PROOF OF DELIVERY','DELIVERED TO CUSTOMER']
        if current_state:
            current_index = states.index(current_state)
            if current_index < 6: 
                next_index = current_index + 1 
                self.state = states[next_index]
        return
    def previous_action(self):
        current_state = self.state
        states = ['UPCOMING UPLOADS','LOADS RTS DEALER', 'SOS READY TO SHIP', 'IN TRANSIT', 'PROOF OF DELIVERY','DELIVERED TO CUSTOMER']
        if current_state:
            current_index = states.index(current_state)
            if current_index > 0:
                next_index = current_index - 1  
            else:
                return 
            self.state = states[next_index]
        return
            
    @api.onchange('state')
    def get_customer_email_and_invoice_number(self):
        if self.state == 'IN TRANSIT':
            if not self.hs7_dictionary_id:
                return {'error': 'No HS7 Dictionary record available'}

            hs7_record = self.hs7_dictionary_id
            customer_email = hs7_record.customer_email
            invoice_number = hs7_record.invoice_number
            pdf_content = self.generate_pdf(invoice_number)

            mail_values = {
                'subject': f'Invoice {invoice_number}',
                'body_html': '<p>Please find attached the invoice.</p>',
                'email_to': customer_email,
                'attachment_ids': [(4, pdf_content.id)],
            }
            self.env['mail.mail'].create(mail_values).send()
            return {
                'warning': {
                    'title': 'Notificación',
                    'message': f"La factura {invoice_number} ha sido enviada a {customer_email}.",
                }
            }

    def generate_pdf(self, invoice_number):
        invoice = self.env['sale.order'].search([('display_name','=', invoice_number)]).invoice_ids[0]
        merger = PdfFileMerger()
        invoice_pdf = ""
        report_action = self.env['ir.actions.report'].search([
            ('report_name', '=', 'account.report_invoice')], limit=1)
        invoice_pdf = {
                    'report_ref': report_action.xml_id,
                    'docids':invoice.id,
                    'data':None
                }
        report_ref = self.env.ref(invoice_pdf['report_ref'])

        pdf_content, _ = report_ref.sudo()._render_qweb_pdf(invoice_pdf['report_ref'],invoice_pdf['docids'], data=None)
        pdf_io = BytesIO(pdf_content)
        merger.append(pdf_io)

        output = BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        data = base64.b64encode(output.read())
        output.close()
        attachment = self.env['ir.attachment'].create({
            'name': 'Logistics_document_packages.pdf',
            'datas': data,
            'type': 'binary',
            'mimetype': 'application/pdf',
        })
        return attachment
    

    def write(self, values):
            if 'customer_email' not in values or not values.get('customer_email'):
                result = super(SendOrder, self).write(values)
            return result

   