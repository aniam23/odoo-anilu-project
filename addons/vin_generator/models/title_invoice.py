from odoo import models,fields,api

class title_invoice(models.Model):
    _inherit = 'account.move'
  
    num_of_titles = fields.Text(compute="calculate_num_of_titles")
    print_button_visible = fields.Boolean(compute="is_invice_line_trailer")

    @api.depends("invoice_line_ids")
    def calculate_num_of_titles(self):
        for record in self:
            record.num_of_titles = len(self.invoice_line_ids)

    @api.depends("invoice_line_ids")
    def is_invice_line_trailer(self):
        for record in self:
            show = False
            for account_move_line in record.invoice_line_ids:
                if account_move_line.product_id.is_trailer:
                    show = True
                    continue
            record.print_button_visible = show
            
            
    def print_title(self):
        self.show_wizard()
        
    def show_wizard(self):
        invoice = ''
        for records in self:
            invoice = records
        sale_order = self.env['sale.order'].search([('name', '=' ,self.invoice_origin)],limit=1)
        return {
            'name': 'Shipping Weight',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shipping.weight.wizard',
            'view_id': self.env.ref('vin_generator.invoice_title_generator_wizard').id,
            'target': 'new',
            'context': {
                'default_invoice': invoice.id,
                'default_sale_order': sale_order.id
            }
        }

        