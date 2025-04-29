from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class InheritSaleOrderLine(models.Model):
    _inherit = "sale.order"
    _description = 'inherit sale.order'

    fechapro = fields.Datetime(string="Última fecha programada")
    camp = fields.Boolean(string="Última", compute='_mm_compute_fecha')

    def _mm_compute_fecha(self):
        self._onchange_order_line()
        self.camp = True

    @api.onchange('order_line')
    def _onchange_order_line(self):
        for sale in self:
            if sale.order_line:
                for line in self.order_line:
                    if line.fechalst:
                        if sale.fechapro:
                            if line.fechalst > sale.fechapro:
                                sale.update({
                                    'fechapro': line.fechalst
                                })
                        else:
                            sale.update({
                                'fechapro': line.fechalst
                            })


class InheritSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = 'inherit sale.order.line'

    fechalst = fields.Datetime(string="Fecha programada")
