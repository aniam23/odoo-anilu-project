from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from datetime import date, datetime, timedelta, time

_logger = logging.getLogger(__name__)


class InheritWorkOrder(models.Model):
    _inherit = "mrp.workorder"
    _description = 'inherit mrp.workorder'

    mm_state_fab = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string="state produ", related='production_id.state')
    mm_prio = fields.Char(string="priori", related='production_id.priori')
    mm_date = fields.Date(string="mm_date")


class InheritProduction(models.Model):
    _inherit = "mrp.production"
    _description = 'inherit mrp.production'

    fcreate = fields.Boolean(string='fcreate')
    priori = fields.Char(string="prioridad")
    is_pdos = fields.Boolean(string="cam", compute="_get_is_pdos")
    date_planned_start = fields.Datetime(
        'Scheduled Date', copy=False,
        help="Date at which you plan to start the production.",
        index=True, required=True)

    def _get_is_pdos(self):
        if self.priori:
            if 'P2' in self.priori:
                if self.state == 'draft':
                    self.is_pdos = True
                else:
                    self.is_pdos = False
            else:
                self.is_pdos = False
        else:
            self.is_pdos = False

    def change_priori(self):
        con = self.env['sequence.fab'].get_seq_mm('P1')
        self.update({
            'priori': 'P1-' + str(con)
        })

    def action_confirm(self):
        _logger.warning('action_confirm-mm %s')
        self._check_company()
        have_sale = False
        for production in self:
            sale_order_ids = production.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
            if sale_order_ids:
                have_sale = True
            _logger.warning('sale_order_ids-mm %s', sale_order_ids)
            if production.bom_id:
                production.consumption = production.bom_id.consumption
            # In case of Serial number tracking, force the UoM to the UoM of product
            if production.product_tracking == 'serial' and production.product_uom_id != production.product_id.uom_id:
                production.write({
                    'product_qty': production.product_uom_id._compute_quantity(production.product_qty,
                                                                               production.product_id.uom_id),
                    'product_uom_id': production.product_id.uom_id
                })
                for move_finish in production.move_finished_ids.filtered(
                        lambda m: m.product_id == production.product_id):
                    move_finish.write({
                        'product_uom_qty': move_finish.product_uom._compute_quantity(move_finish.product_uom_qty,
                                                                                     move_finish.product_id.uom_id),
                        'product_uom': move_finish.product_id.uom_id
                    })
            production.move_raw_ids._adjust_procure_method()
            if sale_order_ids:
                if production.fcreate:
                    (production.move_raw_ids | production.move_finished_ids)._action_confirm(merge=False)
                    production.workorder_ids._action_confirm()
            else:
                (production.move_raw_ids | production.move_finished_ids)._action_confirm(merge=False)
                production.workorder_ids._action_confirm()
        # run scheduler for moves forecasted to not have enough in stock
        self.move_raw_ids._trigger_scheduler()
        self.picking_ids.filtered(
            lambda p: p.state not in ['cancel', 'done']).action_confirm()
        # Force confirm state only for draft production not for more advanced state like
        # 'progress' (in case of backorders with some qty_producing)
        for line in self:
            if have_sale:
                if line.fcreate:
                    line.filtered(lambda mo: mo.state == 'draft').state = 'confirmed'
                if not line.fcreate:
                    line.fcreate = True
            else:
                line.filtered(lambda mo: mo.state == 'draft').state = 'confirmed'

        return True

    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        res = super(InheritProduction, self).create(vals)
        isfa = True
        haveord = True

        busprod = self.env['product.product'].search([('id', '=', vals['product_id'])])

        if busprod.route_ids:
            if len(busprod.route_ids) == 1:
                for mmrute in busprod.route_ids:
                    if mmrute.name == 'Fabricar':
                        isfa = False

                bus = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', vals['product_id'])])
                if bus:
                    haveord = False

        if isfa or haveord:
            if vals['product_qty'] > 1:
                self.create_all_productions(vals['product_qty'], vals)
                nomp = res.name + '-001'
                res.update({
                    'product_qty': 1.0,
                    'name': nomp,
                })

        sale_h = res.sale_order_count
        if sale_h > 0:
            if not res.priori:
                con = self.env['sequence.fab'].get_seq_mm('P1')
                res.update({
                    'priori': 'P1-' + str(con)
                })

            # res.action_confirm()
        else:
            if not res.priori:
                con = self.env['sequence.fab'].get_seq_mm('P2')
                res.update({
                    'priori': 'P2-' + str(con)
                })

        if sale_h > 0:
            res.action_confirm()

        return res

    def set_new_date(self, workcenter, dateset, order):
        print('#######################set_new_date#############################')
        print('orderName--------->', order.name)
        print('FabriName--------->', order.production_id.name)
        print('workcenter--------->', workcenter.id)
        ctime = time(hour=11, minute=34, second=56)
        date =datetime.combine(dateset, ctime)
        # obtener media
        med = self.env['workcenter.order.media'].search([('workcenter_id', '=', workcenter.id)])
        priorimm = order.mm_prio
        # verificar si es dia fin de semana
        datemm = date.date()
        if date.weekday() == 5:
            date = date + timedelta(days=2)
            dateset = dateset + timedelta(days=1)
        elif date.weekday() == 6:
            date = date + timedelta(days=1)
            dateset = dateset + timedelta(days=1)

        # si tiene media buscar fecha para asignar
        if med:
            # verificar prioridades de las ordenes actual prioprim-prioridad de la orden enviada
            ppriori = order.mm_prio
            prioprim = 0
            if 'P1' in ppriori:
                prioprim = 1
            elif 'P2' in ppriori:
                prioprim = 2

            # while para asignar fecha hasta que encuentre espacio segun la media
            stop = 0
            print('med', med.media)
            print('date', date)
            print('dateset', dateset)

            while stop < 1:
                # verificar si es dia fin de semana en bucle
                if date.weekday() == 5:
                    date = date + timedelta(days=2)
                    dateset = dateset + timedelta(days=2)
                elif date.weekday() == 6:
                    date = date + timedelta(days=1)
                    dateset = dateset + timedelta(days=1)



                #busqueda de ordenes de trabajo del dia
                getall = self.env['mrp.workorder'].search( [('workcenter_id', '=', workcenter.id), ('id', '!=', order.id), ('mm_date', '=', dateset)])
                print('getall', getall)
                #si tengo lineas de esse dia checar prioridades y reasignar fechas
                print('date2', date)
                print('dateset2', dateset)
                if getall:
                    #ver que sean mas que la media si no asignar directo la fecha
                    if len(getall) < med.media:
                        print('no media')
                        # reasignar orden de trabajo
                        order.update({
                            'production_date': date,
                            'mm_date': dateset
                        })
                        print('date2', date)
                        # reasignar orden de produccion
                        order.production_id.update({
                            'date_planned_start': date
                        })

                        # checar si tienen hijos las ordenes de produccion
                        mrp_production_ids = order.production_id._get_children()
                        if mrp_production_ids:
                            # asignar fecha a orden de produccion hijasw
                            for child in mrp_production_ids:
                                child.update({
                                    'date_planned_start': date
                                })

                        # checar si tiene ordenes de ventas las producciones
                        if order.production_id:
                            sale_order_ids2 = order.production_id.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
                            idpod = 0
                            # obtener el id de producto template
                            if order.production_id.product_id.product_tmpl_id:
                                idpod = order.production_id.product_id.product_tmpl_id.id
                            else:
                                idpod = order.production_id.product_id.id
                            # buscar venta
                            salebus = self.env['sale.order'].search([('id', 'in', sale_order_ids2)])
                            if salebus:
                                # buscar en todas las ventas
                                for sale in salebus:
                                    if sale.order_line:
                                        # buscar en todas las lineas el producto
                                        for line in sale.order_line:
                                            if line.product_template_id.id == idpod:
                                                # si ya tiene fecha previa ver si es mayor la nueva
                                                if line.fechalst:
                                                    if line.fechalst < date:
                                                        line.update({
                                                            'fechalst': date
                                                        })
                                                # si no tiene fecha asignarle la fecha
                                                else:
                                                    line.update({
                                                        'fechalst': date
                                                    })

                                    # buscar compra de us
                                    if sale.client_order_ref:
                                        busus = self.env['purchase.order'].sudo().search(
                                            [('name', '=', sale.client_order_ref)])
                                        if busus:
                                            if busus.origin:
                                                # buscar venta en us
                                                salebusus = self.env['sale.order'].sudo().search(
                                                    [('name', '=', busus.origin)])
                                                # asiganr fecha en venta us
                                                if not salebusus.fechapro:
                                                    salebusus.update({
                                                        'fechapro': date
                                                    })
                                                elif salebusus.fechapro < date:
                                                    salebusus.update({
                                                        'fechapro': date
                                                    })

                                                # asiganr fecha en lienas de venta us
                                                if salebusus.order_line:
                                                    for linep in salebusus.order_line:
                                                        if linep.product_template_id.id == idpod:
                                                            if not linep.fechalst:
                                                                linep.update({
                                                                    'fechalst': date
                                                                })
                                                            elif linep.fechalst < date:
                                                                linep.update({
                                                                    'fechalst': date
                                                                })

                                    # asiganr fecha en venta
                                    if sale.fechapro:
                                        if sale.fechapro < date:
                                            sale.update({
                                                'fechapro': date
                                            })
                                    else:
                                        sale.update({
                                            'fechapro': date
                                        })




                        stop = 2
                    else:
                        #for de las ordenes de trabajo
                        sum = 0
                        restamm = 0
                        for con in getall:
                            #si no tiene prioridad asignar
                            if not con.mm_prio:
                                #buscar si es de ventas
                                sale_h = con.production_id.sale_order_count
                                if sale_h > 0:
                                    consss = self.env['sequence.fab'].get_seq_mm('P1')
                                    con.production_id.update({
                                        'priori': 'P1-' + str(consss)
                                    })
                                else:
                                    consss = self.env['sequence.fab'].get_seq_mm('P2')
                                    con.production_id.update({
                                        'priori': 'P2-' + str(consss)
                                    })

                            # verificar prioridades de las ordenes actual si no se ha asignado
                            if prioprim == 0:
                                ppriorimm = con.production_id.priori
                                if 'P1' in ppriorimm:
                                    prioprim = 1
                                elif 'P2' in ppriorimm:
                                    prioprim = 2

                            # verificar prioridades de la orden del for priact-prioridad del for
                            priact = con.mm_prio
                            prioseg = 0
                            if 'P1' in priact:
                                prioseg = 1
                            elif 'P2' in priact:
                                prioseg = 2

                            #sum - ordenes que se pueden mover | restamm - ordenes que NO se pueden mover
                            print('prioprim', prioprim)
                            print('prioseg', prioseg)
                            print('state', con.state)
                            #verificar cuantas ordenes hay en hecho y cuantas en borrador
                            #casos donde los 2 son prioridad 1
                            if prioseg == 1 and prioprim == 1:
                                if con.state == 'pending' or con.state == 'cancel':
                                    sum = sum + 1
                                if con.state == 'waiting' or con.state == 'ready' or con.state == 'progress' or con.state == 'done':
                                    restamm = restamm + 1
                            elif prioprim < prioseg:
                                #actual es p1 y se tiene una p2
                                if con.state == 'pending' or con.state == 'waiting' or con.state == 'cancel':
                                    sum = sum + 1
                                if con.state == 'ready' or con.state == 'progress' or con.state == 'done':
                                    restamm = restamm + 1
                            #cuando la prioridad es menor
                            elif prioprim  == 2 and prioseg == 1:
                                if con.state == 'pending' or con.state == 'cancel':
                                    sum = sum + 1
                                if con.state == 'waiting' or con.state == 'ready' or con.state == 'progress' or con.state == 'done':
                                    restamm = restamm + 1
                            #verificar si las 2 son prioridad 2
                            elif prioseg == 2 and prioprim == 2:
                                if con.state == 'pending' or con.state == 'cancel':
                                    sum = sum + 1
                                elif con.state == 'waiting' or con.state == 'ready' or con.state == 'progress' or con.state == 'done' :
                                    restamm = restamm + 1

                        print('sum', sum)
                        print('restamm', restamm)
                        #si las ordenes que no se pueden mover es menor a la media
                        if restamm < med.media:
                            #for de las ordenes de trabajo
                            salfor = 0
                            for every in getall:
                                print('orderNameevery--------->', every.name)
                                print('FabriNameevery--------->', every.production_id.name)
                                if salfor == 0:
                                    #prioridad de la orden del for prioseg
                                    priact = every.mm_prio
                                    prioseg = 0
                                    if 'P1' in priact:
                                        prioseg = 1
                                    elif 'P2' in priact:
                                        prioseg = 2

                                    print('priosegprioseg', prioseg)

                                    if prioprim < prioseg:
                                        print('<<<<<<<')
                                        print('state', every.state)
                                        #asegurar que se pueda reasignar el registro
                                        if every.state == 'pending' or every.state == 'waiting':
                                            #reasignar orden de trabajo
                                            order.update({
                                                'production_date': date,
                                                'mm_date': dateset
                                            })
                                            print('date3', date)
                                            # reasignar orden de produccion
                                            order.production_id.update({
                                                'date_planned_start': date
                                            })

                                            #buscar y reasignar fecha a ordes de produccion hijas
                                            mrp_production_ids = order.production_id._get_children()
                                            if mrp_production_ids:
                                                for child in mrp_production_ids:
                                                    child.update({
                                                        'date_planned_start': date
                                                    })

                                            #buscar ordenes de venta para asignar fechas a las lineas
                                            if order.production_id:
                                                sale_order_ids2 = order.production_id.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
                                                idpod = 0
                                                #buscar id de product.product o de product.template
                                                if order.production_id.product_id.product_tmpl_id:
                                                    idpod = order.production_id.product_id.product_tmpl_id.id
                                                else:
                                                    idpod = order.production_id.product_id.id

                                                print('idpod', idpod)

                                                #buscar las ventas
                                                salebus = self.env['sale.order'].search([('id', 'in', sale_order_ids2)])
                                                print('salebus', salebus)

                                                #for de las ventas para buscar linea
                                                if salebus:
                                                    for sale in salebus:
                                                        #asignar fecha global a venta
                                                        if sale.fechapro:
                                                            if sale.fechapro < date:
                                                                sale.update({
                                                                    'fechapro': date
                                                                })
                                                        else:
                                                            sale.update({
                                                                'fechapro': date
                                                            })

                                                        #si tiene lineas buscar el producto
                                                        if sale.order_line:
                                                            for line in sale.order_line:
                                                                print('product_template_id', line.product_template_id.id)
                                                                if line.product_template_id.id == idpod:
                                                                    #si ya tiene una fecha verificar si la fecha actual es mayor o menor
                                                                    if line.fechalst:
                                                                        if line.fechalst < date:
                                                                            line.update({
                                                                                'fechalst': date
                                                                            })
                                                                    else:
                                                                        line.update({
                                                                            'fechalst': date
                                                                        })


                                                        #buscar compra y venta de us
                                                        if sale.client_order_ref:
                                                            busus = self.env['purchase.order'].sudo().search([('name', '=', sale.client_order_ref)])
                                                            #si tiene compra us
                                                            if busus:
                                                                #si tiene venta us
                                                                if busus.origin:
                                                                    #buscar venta us
                                                                    salebusus = self.env['sale.order'].sudo().search([('name', '=', busus.origin)])
                                                                    #si tiene venta us
                                                                    if salebusus:
                                                                        #asignar fecha global a venta us
                                                                        if not salebusus.fechapro:
                                                                            salebusus.update({
                                                                                'fechapro': date
                                                                            })
                                                                        elif salebusus.fechapro < date:
                                                                            salebusus.update({
                                                                                'fechapro': date
                                                                            })
                                                                        #buscar producto en la linea de venta us
                                                                        if salebusus.order_line:
                                                                            for linep in salebusus.order_line:
                                                                                if linep.product_template_id.id == idpod:
                                                                                    #asignar fecha en lineas venta us
                                                                                    if not linep.fechalst:
                                                                                        linep.update({
                                                                                            'fechalst': date
                                                                                        })
                                                                                    elif linep.fechalst < date:
                                                                                        linep.update({
                                                                                            'fechalst': date
                                                                                        })

                                                                    #si no tiene fecha mayor asigna la fecha
                                                                    else:
                                                                        line.update({
                                                                            'fechalst': date
                                                                        })
                                            stop = 2
                                            salfor = 2
                                            print('dateset',dateset)
                                            self.set_new_date(every.workcenter_id, dateset, every)


                                    #si los 2 son grado 2
                                    elif prioprim == 2 and prioseg == 2:
                                        print('son 2 los 2')
                                        #checar ue sean los estados que se pueden mover
                                        if every.state == 'pending' :
                                            print('cambio de los 2')
                                            #cambiar fecha de orden de trabajo
                                            order.update({
                                                'production_date': date,
                                                'mm_date': dateset,
                                            })
                                            print('date4', date)
                                            #cambiar fecha de orden de produccion
                                            order.production_id.update({
                                                'date_planned_start': date
                                            })
                                            #cambiar fechas de ordes de produccion hijas
                                            mrp_production_ids = order.production_id._get_children()
                                            if mrp_production_ids:
                                                for child in mrp_production_ids:
                                                    child.update({
                                                        'date_planned_start': date
                                                    })

                                            # buscar ordenes de venta para asignar fechas a las lineas
                                            if order.production_id:
                                                sale_order_ids2 = order.production_id.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
                                                idpod = 0
                                                # buscar id de product.product o de product.template
                                                if order.production_id.product_id.product_tmpl_id:
                                                    idpod = order.production_id.product_id.product_tmpl_id.id
                                                else:
                                                    idpod = order.production_id.product_id.id

                                                # buscar las ventas
                                                salebus = self.env['sale.order'].search(  [('id', 'in', sale_order_ids2)])
                                                # for de las ventas para buscar linea
                                                if salebus:
                                                    for sale in salebus:
                                                        # asignar fecha global a venta
                                                        if sale.fechapro:
                                                            if sale.fechapro < date:
                                                                sale.update({
                                                                    'fechapro': date
                                                                })
                                                        else:
                                                            sale.update({
                                                                'fechapro': date
                                                            })

                                                        # si tiene lineas buscar el producto
                                                        if sale.order_line:
                                                            for line in sale.order_line:
                                                                if line.product_template_id.id == idpod:
                                                                    # si ya tiene una fecha verificar si la fecha actual es mayor o menor
                                                                    if line.fechalst:
                                                                        if line.fechalst < date:
                                                                            line.update({
                                                                                'fechalst': date
                                                                            })
                                                                    else:
                                                                        line.update({
                                                                            'fechalst': date
                                                                        })

                                                        # buscar compra y venta de us
                                                        if sale.client_order_ref:
                                                            busus = self.env['purchase.order'].sudo().search([('name', '=', sale.client_order_ref)])
                                                            # si tiene compra us
                                                            if busus:
                                                                # si tiene venta us
                                                                if busus.origin:
                                                                    # buscar venta us
                                                                    salebusus = self.env['sale.order'].sudo().search([('name', '=', busus.origin)])
                                                                    # si tiene venta us
                                                                    if salebusus:
                                                                        # asignar fecha global a venta us
                                                                        if not salebusus.fechapro:
                                                                            salebusus.update({
                                                                                'fechapro': date
                                                                            })
                                                                        elif salebusus.fechapro < date:
                                                                            salebusus.update({
                                                                                'fechapro': date
                                                                            })
                                                                        # buscar producto en la linea de venta us
                                                                        if salebusus.order_line:
                                                                            for linep in salebusus.order_line:
                                                                                if linep.product_template_id.id == idpod:
                                                                                    # asignar fecha en lineas venta us
                                                                                    if not linep.fechalst:
                                                                                        linep.update({
                                                                                            'fechalst': date
                                                                                        })
                                                                                    elif linep.fechalst < date:
                                                                                        linep.update({
                                                                                            'fechalst': date
                                                                                        })
                                                                    # si no tiene fecha mayor asigna la fecha
                                                                    else:
                                                                        line.update({
                                                                            'fechalst': date
                                                                        })
                                            stop = 2
                                            salfor = 2
                                    else:
                                        print('suma dia,,,,,,')
                                        print('suma diaprioprim',prioprim)
                                        print('suma dia,prioseg',prioseg)
                                        print('suma dia,,,,,,', order.production_id.name)

                                        #date = date + timedelta(days=1)
                                        #dateset = dateset + timedelta(days=1)

                            stop = 2

                            if salfor == 0:
                                print('No se entro nada====')
                                print('p1====', prioprim)
                                print('p2====', prioseg)
                                #no hubo uno menor o igual a 2
                                # asignar fecha a orden de trabajo
                                order.update({
                                    'production_date': date,
                                    'mm_date': dateset,
                                })
                                print('date5', date)
                                # asignar fecha a orden de produccion
                                order.production_id.update({
                                    'date_planned_start': date
                                })

                                # checar si tienen hijos las ordenes de produccion
                                mrp_production_ids = order.production_id._get_children()
                                if mrp_production_ids:
                                    # asignar fecha a orden de produccion hijasw
                                    for child in mrp_production_ids:
                                        child.update({
                                            'date_planned_start': date
                                        })

                                # checar si tiene ordenes de ventas las producciones
                                if order.production_id:
                                    sale_order_ids2 = order.production_id.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
                                    idpod = 0
                                    # obtener el id de producto template
                                    if order.production_id.product_id.product_tmpl_id:
                                        idpod = order.production_id.product_id.product_tmpl_id.id
                                    else:
                                        idpod = order.production_id.product_id.id
                                    # buscar venta
                                    salebus = self.env['sale.order'].search([('id', 'in', sale_order_ids2)])
                                    if salebus:
                                        # buscar en todas las ventas
                                        for sale in salebus:
                                            if sale.order_line:
                                                # buscar en todas las lineas el producto
                                                for line in sale.order_line:
                                                    if line.product_template_id.id == idpod:
                                                        # si ya tiene fecha previa ver si es mayor la nueva
                                                        if line.fechalst:
                                                            if line.fechalst < date:
                                                                line.update({
                                                                    'fechalst': date
                                                                })
                                                        # si no tiene fecha asignarle la fecha
                                                        else:
                                                            line.update({
                                                                'fechalst': date
                                                            })

                                            # buscar compra de us
                                            if sale.client_order_ref:
                                                busus = self.env['purchase.order'].sudo().search(
                                                    [('name', '=', sale.client_order_ref)])
                                                if busus:
                                                    if busus.origin:
                                                        # buscar venta en us
                                                        salebusus = self.env['sale.order'].sudo().search(
                                                            [('name', '=', busus.origin)])
                                                        # asiganr fecha en venta us
                                                        if not salebusus.fechapro:
                                                            salebusus.update({
                                                                'fechapro': date
                                                            })
                                                        elif salebusus.fechapro < date:
                                                            salebusus.update({
                                                                'fechapro': date
                                                            })

                                                        # asiganr fecha en lienas de venta us
                                                        if salebusus.order_line:
                                                            for linep in salebusus.order_line:
                                                                if linep.product_template_id.id == idpod:
                                                                    if not linep.fechalst:
                                                                        linep.update({
                                                                            'fechalst': date
                                                                        })
                                                                    elif linep.fechalst < date:
                                                                        linep.update({
                                                                            'fechalst': date
                                                                        })

                                            # asiganr fecha en venta
                                            if sale.fechapro:
                                                if sale.fechapro < date:
                                                    sale.update({
                                                        'fechapro': date
                                                    })
                                            else:
                                                sale.update({
                                                    'fechapro': date
                                                })


                #si no tengo lineas(no getall) asignar la fecha a esta linea
                else:
                    print('no hay lineas del dia')
                    #asignar fecha a orden de trabajo
                    order.update({
                        'production_date': date,
                        'mm_date': dateset,
                    })
                    print('date5', date)
                    # asignar fecha a orden de produccion
                    order.production_id.update({
                        'date_planned_start': date
                    })

                    # checar si tienen hijos las ordenes de produccion
                    mrp_production_ids = order.production_id._get_children()
                    if mrp_production_ids:
                        # asignar fecha a orden de produccion hijasw
                        for child in mrp_production_ids:
                            child.update({
                                'date_planned_start': date
                            })

                    # checar si tiene ordenes de ventas las producciones
                    if order.production_id:
                        sale_order_ids2 = order.production_id.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
                        idpod = 0
                        # obtener el id de producto template
                        if order.production_id.product_id.product_tmpl_id:
                            idpod = order.production_id.product_id.product_tmpl_id.id
                        else:
                            idpod = order.production_id.product_id.id
                        # buscar venta
                        salebus = self.env['sale.order'].search([('id', 'in', sale_order_ids2)])
                        if salebus:
                            # buscar en todas las ventas
                            for sale in salebus:
                                if sale.order_line:
                                    # buscar en todas las lineas el producto
                                    for line in sale.order_line:
                                        if line.product_template_id.id == idpod:
                                            # si ya tiene fecha previa ver si es mayor la nueva
                                            if line.fechalst:
                                                if line.fechalst < date:
                                                    line.update({
                                                        'fechalst': date
                                                    })
                                            # si no tiene fecha asignarle la fecha
                                            else:
                                                line.update({
                                                    'fechalst': date
                                                })

                                # buscar compra de us
                                if sale.client_order_ref:
                                    busus = self.env['purchase.order'].sudo().search(
                                        [('name', '=', sale.client_order_ref)])
                                    if busus:
                                        if busus.origin:
                                            # buscar venta en us
                                            salebusus = self.env['sale.order'].sudo().search(
                                                [('name', '=', busus.origin)])
                                            # asiganr fecha en venta us
                                            if not salebusus.fechapro:
                                                salebusus.update({
                                                    'fechapro': date
                                                })
                                            elif salebusus.fechapro < date:
                                                salebusus.update({
                                                    'fechapro': date
                                                })

                                            # asiganr fecha en lienas de venta us
                                            if salebusus.order_line:
                                                for linep in salebusus.order_line:
                                                    if linep.product_template_id.id == idpod:
                                                        if not linep.fechalst:
                                                            linep.update({
                                                                'fechalst': date
                                                            })
                                                        elif linep.fechalst < date:
                                                            linep.update({
                                                                'fechalst': date
                                                            })

                                # asiganr fecha en venta
                                if sale.fechapro:
                                    if sale.fechapro < date:
                                        sale.update({
                                            'fechapro': date
                                        })
                                else:
                                    sale.update({
                                        'fechapro': date
                                    })
                    stop = 2

                date = date + timedelta(days=1)
                dateset = dateset + timedelta(days=1)



    def action_confirm(self):
        print('action_confirm', self)
        for prodd in self:
            for trab in self.workorder_ids:
                mrp_production_ids = prodd._get_sources().ids
                _logger.warning('self prod------.......>>>>: %s', self)
                _logger.warning('mrp_production_ids: %s', mrp_production_ids)
                if not mrp_production_ids:
                    if 'SOLDADURA L' in trab.workcenter_id.name:
                        print('name#######################################', trab.workcenter_id.name)
                        now = datetime.today()
                        print('today', now)
                        now = now + timedelta(hours=-6)
                        print('-6horas', now)
                        now = now.date()
                        print('fecha', now)
                        self.set_new_date(trab.workcenter_id, now, trab)
        return super(InheritProduction, self).action_confirm()

    def create_all_productions(self, prod_qty, vals_c):
        print('create cada produccion')
        nombrep = vals_c['name']
        rman = int(prod_qty) - 1
        for i in range(rman):
            cole = str(i + 2).zfill(3)
            print('create produccion', cole)
            vals_c['name'] = nombrep + '-' + cole
            vals_c['product_qty'] = 1
            vals_c['fcreate'] = True
            new_prod = self.env['mrp.production'].create(vals_c)
            new_prod.update({
                'product_qty': 2.0,
            })
            new_prod.update({
                'product_qty': 1.0,
            })

    def write(self, vals):
        _logger.warning('vals %s', vals)
        res = super(InheritProduction, self).write(vals)
        if 'lot_producing_id' in vals:
            nmspl = self.name.split('-')
            namepr = ''
            if len(nmspl) > 0:
                namepr = nmspl[0]
            else:
                namepr = self.name

            busSto = self.env['stock.move'].search([('reference', '=', self.name)])

            if not busSto:
                nam = self.name
                spn = nam.split('-')
                print('no spn', spn[0])
                busSto = self.env['stock.move'].search([('reference', '=', spn[0])])

            busSub = self.env['mrp.production'].search([('move_dest_ids', 'in', busSto.ids)])
            if busSub:
                getLot = self.env['stock.lot'].search([('id', '=', vals['lot_producing_id'])])
                print('getLot', getLot.name)
                for subp in busSub:
                    print('subp', subp)
                    print('id_lot prod', subp.product_id.name)
                    if not subp.lot_producing_id or subp.lot_producing_id.name != getLot.name:
                        print('tracking', subp.product_id.tracking)
                    if subp.product_id.tracking == 'serial':
                        # Verificar si el lote ya existe antes de crear uno nuevo
                        existing_lot = self.env['stock.lot'].search([
                            ('product_id', '=', subp.product_id.id),
                            ('name', '=', getLot.name),
                        ])
                        if existing_lot:
                            # Si ya existe, actualizar la orden de producción con el lote existente
                            subp.write({'lot_producing_id': existing_lot.id})
                        else:
                            # Si no existe, crear un nuevo lote y actualizar la orden de producción
                            id_lot = self.env['stock.lot'].create({
                                'name': getLot.name,
                                'product_id': subp.product_id.id,
                                'company_id': subp.env.company.id,
                            })
                            print('id_lot name', id_lot.name)
                            print('id_lot prod', id_lot.product_id.name)
                            subp.write({'lot_producing_id': id_lot.id})

        return res

    def action_merge(self):
        _logger.warning('merge: %s', self)
        busprod = self.product_id
        isfa = True
        haveord = True
        if busprod.route_ids:
            if len(busprod.route_ids) == 1:
                for mmrute in busprod.route_ids:
                    _logger.warning('nameme: %s', mmrute.name)
                    if mmrute.name == 'Fabricar':
                        isfa = False

                bus = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', busprod.id)])
                _logger.warning('busmw: %s', bus)
                if bus:
                    haveord = False

        if not isfa and not haveord:
            return super(InheritProduction, self).action_merge()
        else:
            raise UserError('Estas ordenes no pueden ser fucionadas')
