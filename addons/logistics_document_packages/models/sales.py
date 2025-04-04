from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
  
    show_send_order_button = fields.Boolean(
        string='Show Send Order Button',
        compute='_compute_show_send_order_button',
        store=True,
    )
   
    conexsend = fields.Many2one('send.order', string="Estado de envio")
    fletero = fields.Text(string="Fletero")
    @api.depends('state')
    def _compute_show_send_order_button(self): 
        for order in self:
            print(f"Order ID: {order.id}, State: {order.state}")
            order.show_send_order_button = order.state == 'sale'

    def send_action(self):
        conexsend = self.mapped('conexsend')
        action = self.env.ref('send_state_form_action_window', raise_if_not_found=False)
        if not action:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Send Order Form',
                'res_model': 'send.order',
                'view_mode': 'form',
                'view_id': False,  
                'target': 'current',
            }
        if len(conexsend) > 1:
            action.domain = [('id', 'in', conexsend.ids)]
        else:
            action.domain = [('id', '=', conexsend.id)]
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send Order Form',
            'res_model': 'send.order',
            'view_mode': 'form',
            'view_id': action.view_id.id if action.view_id else False,
            'flags': {'action_buttons': True},
            'domain': action.domain,
        }

        


   