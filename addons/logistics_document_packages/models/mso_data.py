from odoo import models, fields, api

class MsoData(models.Model):
    _name = 'mso.data'
    _description = 'add values mso data'
   
    name = fields.Char(string='Name')
    log_document_id = fields.Many2one('logistics.log_document',string='Log Document')
    vins_print =fields.Many2many('print.vins', string='print vins')
    vin = fields.Many2one( comodel_name= 'vin_generator.vin_generator',string= 'vin')
    product =fields.Many2one( comodel_name= 'product.product',string= 'product')
    sale_order =fields.Many2one( comodel_name= 'sale.order',string= 'sale order')
    vin_text = fields.Text('Vin')
    checkbox = fields.Boolean(string='Selected', default=False)
    print_all_together = fields.Boolean(string='print_all_together', default=False)
    