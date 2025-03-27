from odoo import models, fields, api

class HS7Dictionary(models.Model):
    _name = 'hs7.dictionary'
    _description = 'HS7 Dictionary'
    send_order_id = fields.Many2many('send.order', string="Send Order")
    customer_name = fields.Char(string="Customer Name")
    customer_email = fields.Char(string="Customer Email")
    product_id = fields.Char(string="Product ID")
    invoice_number = fields.Char(string="Invoice Number")
    shipping_location = fields.Char(string="Shipping Location")
    ship_date = fields.Date(string="Ship Date")
    creation_log = fields.Text(string="Creation Log")
    due_date = fields.Date(string="Due Date")
    ship_to = fields.Char(string="Ship To")
    sale_order = fields.Many2one('sale.order', string='Sales Orders')
    
    def action_clear(self):
        self.unlink()

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
        states = ['Sales Orders','Packing','MSO', 'HS7', 'Factura', 'Declaracion','State Send']
        if current_state:
            current_index = states.index(current_state)
            if current_index > 0:
                next_index = current_index - 1  
            else:
                return 
            self.state = states[next_index]
        return

    def action_open_sales(self):
        id_vista = self.env.ref('sale.view_order_form', False)
        order = self.env['send.order'].browse(self.id)
        if order.exists():  
            if hasattr(order, 'value_state'): 
                    order.value_state()  
        return {
            'name': 'Ver Sale Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': self.sale_order.id,
            'target': 'current',
            'context': {
            },
        }
        