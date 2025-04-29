from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from datetime import date, datetime
_logger = logging.getLogger(__name__)


class InheritWorkCenter(models.Model):
    _inherit = "mrp.workcenter"
    _description = 'inherit mrp.workcenter'

    mediamm = fields.Integer(string='Promedio de órdenes al día', compute='_compute_prom_mm')
    lstday = fields.Datetime(string='Última fechas planeada', compute='_compute_lstday_mm')

    def _compute_prom_mm(self):
        for center in self:
            bus = self.env['workcenter.order.media'].search([('workcenter_id', '=', center.id)])
            if bus:
                center.mediamm = bus[0].media
            else:
                center.mediamm = 0


    def _compute_lstday_mm(self):
        for center in self:
            bus = self.env['mrp.workorder'].search([('workcenter_id', '=', center.id)], order='production_date desc', limit=1)
            if bus:
                center.lstday = bus[-1].production_date
            else:
                center.lstday = datetime.now()