from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InheritProductTemplate(models.Model):
    _inherit = "product.template"
    _description = 'inherit product.template'

    mm_factor = fields.Float(string="Factor de conversión", default=1)
    mm_uom = fields.Many2one('uom.uom', 'Unidad de medida de conversión',)
    mm_term = fields.Boolean(string="Producto terminado")
    
