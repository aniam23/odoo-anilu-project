from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class InheritPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _description = 'inherit purchase.order.line'

    mm_factor_l = fields.Float(string="Factor de conversión", related='product_id.mm_factor')
    mm_uom_l = fields.Many2one('uom.uom',string="Unidad de medida de conversión", related='product_id.mm_uom')
    mm_fac_can = fields.Float(string="Cantidad (Factor)")

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if lines.product_id:
            if lines.product_id.mm_factor:
                lines.write({
                    'mm_fac_can': lines.product_qty * lines.mm_factor_l
                })
        return lines
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        print('_onchange_product_id')
        if self.product_id:
            if self.product_id.mm_factor:
                self.mm_fac_can = self.product_qty * self.mm_factor_l
            else:
                self.mm_fac_can = 0
        else:
            self.mm_fac_can = 0

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        print('_onchange_product_qty')
        if self.product_id:
            if self.product_id.mm_factor:
                self.mm_fac_can = self.product_qty * self.mm_factor_l
            else:
                self.mm_fac_can = 0
        else:
            self.mm_fac_can = 0

