from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta, time
import logging
_logger = logging.getLogger(__name__)

class WorkcenterOrderCompletion(models.Model):
    _name = 'workcenter.order.completion'
    _description = 'Workcenter Order Completion'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter', required=True)
    date = fields.Date(string='Date', required=True)
    orders_completed = fields.Integer(string='Orders Completed', required=True)


    def cron_order_byday(self):
        now = datetime.now() + timedelta(hours=-6)
        _logger.warning('nowplan %s', now)
        fein = datetime.combine(now, datetime.min.time())
        fefin = datetime.combine(now, datetime.max.time())
        _logger.warning('fein %s', fein)
        _logger.warning('fefin %s', fefin)
        bus = self.env['mrp.workorder'].search([('state','=','done'),('date_finished','>=', fein), ('date_finished', '<=', fefin)])
        dicwc = {}
        if bus:
            for lineas in bus:
                if lineas.product_id.product_tmpl_id.mm_term:
                    if 'SOLDADURA-' in lineas.workcenter_id.name:
                        _logger.warning('fefin %s', lineas.production_id.name)
                        if not str(lineas.workcenter_id.id) in dicwc:
                            dicwc[str(lineas.workcenter_id.id)] = 1
                        else:
                            dicwc[str(lineas.workcenter_id.id)] = dicwc[str(lineas.workcenter_id.id)] + 1


        _logger.warning('dicwc %s', dicwc)
        for x, y in dicwc.items():
            self.env['workcenter.order.completion'].create({
                'workcenter_id': int(x),
                'date': now,
                'orders_completed': y
            })



    def cron_order_bymonth(self):
        now = datetime.now() + timedelta(hours=-6)
        daymen = now + timedelta(days=-4)
        _logger.warning('nowplanmon %s', now)
        fein = datetime.combine(daymen, datetime.min.time())
        fefin = datetime.combine(now, datetime.max.time())
        _logger.warning('feinmo %s', fein)
        _logger.warning('fefinmo %s', fefin)
        
        bus = self.env['workcenter.order.completion'].search([('date','>=', fein),('date', '<=', fefin)])
        dicwc = {}
        if bus:
            for lineas in bus:
                if not str(lineas.workcenter_id.id) in dicwc:
                    dicwc[str(lineas.workcenter_id.id)] = lineas.orders_completed
                else:
                    dicwc[str(lineas.workcenter_id.id)] = dicwc[str(lineas.workcenter_id.id)] + lineas.orders_completed

        _logger.warning('dicwcmo %s', dicwc)
        
        for x, y in dicwc.items():
            _logger.warning('x %s', x)
            _logger.warning('y %s', y)
            bus = self.env['workcenter.order.media'].search([('workcenter_id', '=', int(x))])
            _logger.warning('bus %s', bus)
            if bus:
                if bus.count_days == 4:
                    _logger.warning('media %s', y/5)
                    bus.update({
                        'media': int(y/5),
                        'count_days': 0
                    })

                else:
                    if now.weekday() == 5:
                        a = 'a'
                    elif now.weekday() == 6:
                        a = 'a'
                    else:
                        bus.update({
                            'count_days': bus.count_days + 1
                        })
            else:
                self.env['workcenter.order.media'].create({
                    'workcenter_id': x,
                    'media': 1,
                    'count_days': 1
                })




class WorkcenterOrderCompletion(models.Model):
    _name = 'workcenter.order.media'
    _description = 'Workcenter Order media'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter', required=True)
    media = fields.Integer(string="media")
    count_days = fields.Integer(string='count_days')




