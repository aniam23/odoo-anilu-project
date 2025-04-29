from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class InheritPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _description = 'inherit purchase.order.line'

    mm_factor_l = fields.Float(string="Factor de conversión", related='product_id.mm_factor')
    mm_uom_l = fields.Many2one('uom.uom', string="Unidad de medida de conversión", related='product_id.mm_uom')
    mm_fac_can = fields.Float(string="Cantidad (Factor)")

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id:
                if line.product_id.mm_factor:
                    line.write({
                        'mm_fac_can': line.product_qty * line.mm_factor_l
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

class InheritStockPicking(models.Model):
    _inherit = "stock.picking"
    _description = 'inherit stock.picking'

    def action_assign(self):
        super(InheritStockPicking, self).action_assign()
        busord = self.env['sale.order'].search([('id', '=', self.sale_id.id)])
        if len(busord.mrp_production_ids) == 1:
            buspro = self.env['mrp.production'].search([('id', '=', busord.mrp_production_ids.id)])
        else:
            buspro = self.env['mrp.production'].search([('id', 'in', busord.mrp_production_ids.ids)])

        lot_u = []
        for line in self.move_line_ids_without_package:
            if line.lot_id:
                lot_u.append(line.lot_id.id)

        for nline in buspro:
            if nline.lot_producing_id.id not in lot_u:
                self.env['stock.move.line'].create({
                    'product_id': nline.product_id.id,
                    'product_uom_id': nline.product_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'picking_id': self.id,
                    #'reserved_uom_qty': nline.product_qty,
                    'lot_id': nline.lot_producing_id.id,
                    'package_id': False,
                    'owner_id': False,
                    #'qty_done': nline.product_qty

                })

        return True



# class InheritStockMoveLine(models.Model):
#     _inherit = "stock.move.line"
#     _description = 'inherit stock.move.line'
#
#     @api.model
#     def create(self, vals):
#         print('*********************************************')
#         res = super(InheritStockMoveLine, self).create(vals)
#         print('lines moves', vals)
#         for line in res:
#             if line.origin:
#                 print('ori', line.origin)
#                 busprod = self.env['mrp.production'].search([('name', '=', line.origin)])
#                 if busprod:
#                     print('busprod', busprod)
#                     sale_order_ids = busprod.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
#                     print('idsale', sale_order_ids[0])
#                     buscot = self.env['sale.order'].search([('id', '=', sale_order_ids[0])])
#                     if buscot:
#                         bussal = self.env['stock.picking'].search([('sale_id', '=', buscot.id)])
#                         bussan = self.env['stock.move.line'].search([('picking_id', '=', bussal.id)])
#                         print('bussal', bussal)
#                         if bussan:
#                             ante = bussan[0]
#                             if buscot:
#                                 line.write({
#                                     'picking_id': bussal.id,
#                                     'location_id': bussan.location_id,
#                                     'location_dest_id': bussan.location_dest_id,
#                                     'state': bussan.state,
#                                     #'reserved_qty': bussan.reserved_qty,
#                                     #'reserved_uom_qty': bussan.reserved_uom_qty,
#                                     #'qty_done': bussan.qty_done,
#                                 })
#
#         return res
#
#
#     def write(self, vals):
#         print('*********************************************')
#         res = super(InheritStockMoveLine, self).write(vals)
#         print('lines moveswrite', vals)
#         return res