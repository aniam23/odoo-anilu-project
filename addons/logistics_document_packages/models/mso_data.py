from odoo import models, fields, api

class MsoData(models.Model):
    _name = 'mso.data'
    _description = 'add values mso data'
    #obtener campos para generar mso correctamente
    name = fields.Char(string='Name')
    log_document_id = fields.Many2one('logistics.log_document', string='Log Document')
    vins_print = fields.Many2many('print.vins', string='Print Vins')
    vin = fields.Many2one(
        comodel_name='vin_generator.vin_generator', 
        string='VIN',
        store=True
    )
    product = fields.Many2one(
        comodel_name='product.product', 
        string='Product',
        store=True
    )
    sale_order = fields.Many2one(
        comodel_name='sale.order', 
        string='Sale Order',
        store=True
    )
    vin_text = fields.Char(
        string='Vin', 
        store=True
    )
    checkbox = fields.Boolean(
        string='Selected', 
        default=False
    )
    print_all_together = fields.Boolean(
        string='Print All Together', 
        default=False
    )
    reference_field = fields.Char()
