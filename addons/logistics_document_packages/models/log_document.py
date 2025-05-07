from odoo import models, fields, api
import base64
import time
import random
import logging
from odoo.exceptions import UserError
from datetime import datetime
from PyPDF2 import PdfFileMerger
from io import BytesIO
import os
class LogisticsLogDocument(models.Model):
    _name = 'logistics.log_document'
    _description = 'Log Document for Sale Order' 
    name = fields.Text() 
    date = fields.Datetime(string="Creation Date",readonly=True)
    mo_date = fields.Text()
    product_vin = fields.Text()
    product_body_type = fields.Text()
    email = fields.Char(string="Customer Email")
    sale_order = fields.Many2one('sale.order', string='Sales Orders')
    packing_list = fields.Text('Packing List')
    mso = fields.Char(string="MSO")
    hs7 = fields.Char(string="Declaracion")
    product_lines = fields.One2many('sale.order.line', string="Productos de la Orden", related='sale_order.order_line',)
    select_product = fields.Boolean(string="Seleccionar Producto", default=False)
    factura = fields.Char(string="Factura")
    declara = fields.Char(string="HS7")
    send = fields.Text(string="State Send")
    weight = fields.Integer(string="Peso remolque")
    state = fields.Selection([
        ('Sales Orders', 'Sales Orders'),
        ('Packing', 'Packing'),
        # ('Packing Finanzas', 'Packing Finanzas'),
        ('MSO', 'MS0'),
        ('HS7', 'HS7'),
        ('Factura', 'Factura'),
        ('Declaracion', 'Declaracion')
        
    ], string='State', default='Sales Orders', store=True, tracking=True)
    invoice = fields.Many2one(comodel_name='account.move',                                                                                                                                                         )
    mso_dictionary = fields.One2many('mso.data','log_document_id', string='MSOs')
    checkbox = fields.Boolean(string='Selected', default=False)
    conexsend = fields.Many2one('send.order', string="Estado de envio")
    sale_order_id = fields.Many2one('sale.order', string="Orden de Venta")
    packing_name = fields.Text('NAME')
    packing_scac = fields.Text('SCAC')
    packing_caat = fields.Text('CAAT')
    packing_truck = fields.Text('TRUCK')
    packing_plates = fields.Text('PLATES')
    packing_trailer = fields.Text('TRAILER')
    packing_plates_trailer = fields.Text('PLATES TRAILER')
    comentarios = fields.Text('COMMENTS')
    tramitador = fields.Text('TRAMITADOR')
    downloaded_attachment_ids = fields.Many2one(
    comodel_name='ir.attachment',      
    string="Archivos Descargados",store=True
    )

    def _valid_field_parameter(self, field, name):
        """
        Este método sobreescribe la función base para autorizar el uso del parámetro 'tracking'
        en cualquier campo del modelo. Otros parámetros personalizados deben ser validados
        por la implementación padre.
        bool: True si el parámetro es 'tracking', de lo contrario delega al padre
        """
        if name == 'tracking':
            return True
        return super(LogisticsLogDocument, self)._valid_field_parameter(field, name)
    @api.model_create_multi
    def create(self, vals):
        """
        Asigna a cada documento creado un id unico para identificarlo mas facilmente
        """
        if 'name' not in vals[0]:
            unique_name = f"Document_{random.randint(1, 9999)}"
            vals[0]['name'] = unique_name  
        record = super(LogisticsLogDocument, self).create(vals) 
        record.setDate()
        return record
        
    # def _compute_send_button_visible(self):
    #     """
    #     Asigna a cada documento creado un id unico para identificarlo mas facilmente
    #     """
    #     for record in self:
    #         my_model_records = self.env['my.model'].search([('sale_order_id', '=', record.id)])
    #         record.send_button_visible = bool(my_model_records)

    def setDate(self):
        for record in self:
            record.date = datetime.today()

    @api.onchange('sale_order')
    def _onchange_sale_order(self):
        """Verifica y actualiza el estado al seleccionar una orden de venta.
         y despues realiza las siguientes verificaciones:
        1. Comprueba que la factura asociada a la orden de venta seleccionada  tengan el título generado.
        2. Verifica que exista  una orden de producción relacionada.
        3. Si todo es correcto, transiciona al estado 'Packing'
        """
        self.mso_state() 
        if self.sale_order:
            for invoice in self.sale_order.invoice_ids:
                if not invoice.print_button_visible:
                    raise UserError(
                        f"La factura {invoice.name} de la orden {self.sale_order.name} no tiene el título generado."
                    )
            manufacturing_orders = self.env['mrp.production'].search([
                ('origin', '=', self.sale_order.name)
            ])
            if not manufacturing_orders:
                raise UserError(
                    f"La orden de venta {self.sale_order.name} no tiene órdenes de producción asociadas."
                )
            self.state = 'Packing'
            

    def previous_action(self):
        current_state = self.state
        states = ['Sales Orders','Packing','MSO', 'HS7', 'Factura', 'Declaracion','State Send']
        if current_state:
            current_index = states.index(current_state)
            if current_index > 0:
                next_index = current_index - 1  
            else:
                return 
            self.state = states[next_index]
        return

    def next_action(self):
        current_state = self.state
        states = ['Sales Orders', 'Packing', 'MSO', 'HS7', 'Factura', 'Declaracion','State Send']
        if current_state:
            current_index = states.index(current_state)
            if current_index < 7: 
                next_index = current_index + 1 
            else:
                return
            self.state = states[next_index]
        return
    
    #region 
    # def send_action(self):
    #     order = None
    #     send_state_form_action_window = self.env.ref('send_order.send_state_form_action_window', False)
    #     self.ensure_one()
    #     sale_order = self.sale_order
    #     document_id = self.id 
    #     fecha_hoy = time.localtime()
    #     fecha_formateada = time.strftime('%Y-%m-%d', fecha_hoy)
    #     print(fecha_formateada)
    #     if sale_order:
    #         customer_email = sale_order.partner_id.email  
    #         if not customer_email:
    #             print("No se encontró el email del cliente en la orden de venta.") 
    #         sale_order.write({'show_send_order_button': True})
    #         sale_order.action_confirm()
    #         order = self.env['send.order'].browse(self.id)
    #     if order.exists():  
    #         if hasattr(order, 'value_state'): 
    #             try:
    #                 order.value_state()  
    #                 print("Send Order encontrado y value_state ejecutado:", order)
    #             except Exception as e:
    #                 print(f"Error al ejecutar value_state: {e}")
    #         else:
    #             print("Método value_state no encontrado en el objeto send.order.")
    #     else:
    #         if sale_order:
    #             customer_name = sale_order.partner_id.display_name
    #             customer_email = sale_order.partner_id.email  
    #             product_id = sale_order.order_line[0].product_id.id  
    #             invoice_number = sale_order.name
    #             shipping_location = sale_order.warehouse_id.name
    #             ship_date = fecha_formateada
    #             creation_log = sale_order.create_date
    #             due_date = self.sale_order.validity_date
    #             ship_to = self. sale_order.partner_id.contact_address
          
                
    #             new_order = self.env['send.order'].create({
    #                 'customer_name': customer_name, 
    #                 'customer_email': customer_email,  
    #                 'product_id': product_id,
    #                 'invoice_number': invoice_number,
    #                 'shipping_location': shipping_location,
    #                 'ship_date': ship_date,
    #                 'creation_log': creation_log,
    #                 'due_date': due_date,
    #                 'ship_to': ship_to,
    #                 'sale_order': self.sale_order.id
               
    #             })
    #             print("Nuevo Send Order creado:", new_order)

               
    #             try:
    #                 if hasattr(new_order, 'value_state'):
    #                     new_order.value_state()
    #                     print("Nuevo Send Order ejecutando value_state:", new_order)
    #             except Exception as e:
    #                 print(f"Error al ejecutar value_state en el nuevo orden: {e}")
    #     return {
    #         'name': 'Send Order Form',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'send.order',
    #         'view_mode': 'form',
    #         'view_id': send_state_form_action_window.view_id.id if send_state_form_action_window else False,
    #         'flags': {'action_buttons': True},
    #         'context': {
    #             'default_document_id': document_id,
    #             'default_sale_order_id': sale_order.id if sale_order else False
    #         }
    #     }
    #endregion 
    def transform_to_lbs(self, kg):
        lb = int(float(kg) * 2.205)
        shipping_text = str(kg)+"KG ("+str(lb)+"LB)"
        return shipping_text
    
    def format_date(self, dateToFormat):
        auxArrayOfStrings = dateToFormat.split()
        auxArrayOfStrings = auxArrayOfStrings[0].split("-")
        return {
            "date": str(auxArrayOfStrings[2])+"/"+str(auxArrayOfStrings[1])+"/"+str(auxArrayOfStrings[0]),
            "year": str(auxArrayOfStrings[0])
        }
    
    def format_body_type(self,bodyTypeString):
        """
        Esta función funciona como un  traductor automático para los tipos de carrocerías 
        de los  vehículos. Toma
        los nombres técnicos que usan los sistemas internos y los convierte en nombres mas legibles.
        """
        if "_" in bodyTypeString:
            return "ROLL OFF DUMP"
        else:
            return bodyTypeString
        
    def format_gvwr(self, product):
        """
        formato para convertir los gvwr de libras a kg
        """
        lb = product.gvwr_related.weight_lb
        kg = product.gvwr_related.weight_kg
        name = product.default_code
        return {
            "gvwr": str(kg)+" KG ("+str(lb)+" LBS)",
            "model": name
        }
    def get_data(self):
        """
        Esta función recolecta y organiza información clave sobre órdenes de producción relacionadas con una venta específica
        Su propósito principal es preparar los datos para su uso en documentos o reportes.
        """
        list_of_data = []
        mo_orders = []
        manufacturing_order_list = self.env['mrp.production'].search([])
        for order in manufacturing_order_list:
            #despues de la busqueda de la orden de produccion, busca el origen relacionado con el nombre de la orden de venta.
            if order.origin and order.origin == self.sale_order.name:
                mo_orders.append(order)
        for mo_order in mo_orders:
            mo_date = mo_order.date_planned_start
            product_vin = mo_order.vin_dispayed
            product_body_type = mo_order.vin_relation.trailer_type
            dateAndYear = self.format_date(str(mo_date))
            bodyType = self.format_body_type(product_body_type)
            productInfo = self.format_gvwr(mo_order.product_id)
            weight = self.weight
            dry_weight =mo_order.product_tmpl_id.dry_weight 
            invoice = self.sale_order.invoice_ids[0]
            invoice_name = invoice.display_name
            list_of_data.append({
                "date": dateAndYear["date"],
                "vin": product_vin,
                "body_type": bodyType,
                "gvwr": productInfo["gvwr"],
                "invoice_number": invoice_name,  
                "year": dateAndYear["year"],
                "shipping_weight": weight,
                "dry_weight": dry_weight,
                "model_name": productInfo["model"],
                "last_data": False
            })
        #Devuelve la lista completa de datos formateados
        if list_of_data:
            list_of_data[-1]["last_data"] = True
        return list_of_data

    # region
    # def print_packing(self):
    #     current_state = self.state
    #     if current_state == 'Packing': 
    #         if self.sale_order:
    #             for line in self.sale_order.order_line:
    #                 return self.env.ref('logistics_document_packages.report_packing_fac_action').report_action(self, data={
    #                     "sale_order_id": self.sale_order.id,
    #                     "packing_name": self.packing_name,
    #                     "packing_scac": self.packing_scac,
    #                     "packing_caat": self.packing_caat,
    #                     "packing_truck": self.packing_truck,
    #                     "packing_plates": self.packing_plates,
    #                     "packing_trailer": self.packing_trailer,
    #                     "comentarios": self.comentarios,
    #                     "tramitador": self.tramitador
    #                 }) 
    # endregion        
    #imprime cada documento por separado
    def print_action(self):
        """
        almacena los valores manuales que el usurio ingrese y posteriormente genera el reporte packing
        """
        current_state = self.state
        if current_state == 'Packing':
            if self.sale_order:
                for line in self.sale_order.order_line:
                    return self.env.ref('logistics_document_packages.report_packing_action').report_action(self, data={
                        "sale_order_id": self.sale_order.id,
                        "packing_name": self.packing_name,
                        "packing_scac": self.packing_scac,
                        "packing_caat": self.packing_caat,
                        "packing_truck": self.packing_truck,
                        "packing_plates": self.packing_plates,
                        "packing_trailer": self.packing_trailer,
                        "packing_plates_trailer": self.packing_plates_trailer,
                        "comentarios": self.comentarios,
                        "tramitador": self.tramitador
                    })
    
        # region hello
        # elif current_state == 'Packing Finanzas':
            # if self.sale_order:
            #     for partner in self.sale_order.partner_id:
            #         freight_partner = self.env['freight.partner'].search([('ref_cliente', 'in', [partner.id])], limit=1)
            # if freight_partner:
            #     print(f"Cliente encontrado: {self.sale_order.partner_id} - {self.sale_order.partner_id}")
            #     print(f"Número de Freight: {freight_partner.id}, Precio de flete: {freight_partner.freight_prices}")
            # else:
            #     print(f"No se encontró un número de freight asociado para el cliente: {freight_partner.freight_prices}")
            
            # data = []

            # # precio menos 400 de cada remolque
            # ganancia_fija = 400
            # ganancias = {}

            # if self.sale_order and self.sale_order.order_line:
            #     for line in self.sale_order.order_line:
            #         if line.product_id:
            #             ganancias[line.product_id.id] = line.product_id.list_price - ganancia_fija 
                       
            # else:
            #     ganancias = {}
            #     print(ganancias)


            # # suma de las ganancias
            # ganancia_total = 0.0
            # if self.sale_order and self.sale_order.order_line:
            #     for line in self.sale_order.order_line:
            #         if line.product_id.id in ganancias:
            #             ganancia_total += ganancias[line.product_id.id] 

            # print(f"Ganancia total de la orden seleccionada: ${ganancia_total:,.0f}")


 
            # for production in self.sale_order.mrp_production_ids:
            #     bom_lines = production.product_id.bom_ids.bom_line_ids
            #     wheels_count = {}
            #     for line in self.sale_order.order_line:
            #                   if bom_lines:
            #                       for bom_line in bom_lines:
            #                           if 'llanta' in bom_line.product_id.display_name.lower():
            #                               if production.id in wheels_count:
            #                                   wheels_count[line.product_id.id] += bom_line.product_qty
            #                               else:
            #                                   wheels_count[line.product_id.id] = bom_line.product_qty

            #     # calculo para packing finanzas
            #     precio_total_individual = {}
            #     if self.sale_order.order_line:
            #         for line in self.sale_order.order_line:
            #             if ganancia_total != 0: 
            #                 precio_producto = (freight_partner.freight_prices * ganancias[line.product_id.id] / ganancia_total) + ganancias[line.product_id.id]
            #                 precio_total_individual_formateado = "${:,.0f}".format(precio_producto)
            #                 precio_total_individual[line.product_id.id] = precio_total_individual_formateado
            #                 print(precio_total_individual_formateado)
                           
            #     discount = 0.0 
            #     for line in self.sale_order.order_line:  
            #         bom_lines = line.product_id.bom_ids.bom_line_ids 
            #         discount = line.discount  
            #         print(f"Producto: {line.product_id.display_name}, Descuento: {discount:.2f}%")

            #         # agrega precio opciones para el remolque
            #         price_final = {}
            #         for line in self.sale_order.order_line:
            #             price_unit = line.product_id.list_price
            #             price_extra = 0.0
            #             for variant in line.product_id.product_template_attribute_value_ids:
            #                 if variant.price_extra:
            #                     price_extra = variant.price_extra
            #             price_final[line.product_id.id] = (price_unit + price_extra) - discount
            #         price_extra = price_final.get(production.product_id.id, 0.0)
  
               
              
            #     if self.sale_order:
            #         for invoice in self.sale_order.invoice_ids:
            #             invoices = self.sale_order.invoice_ids
            #             invoice = invoices[:1]  

            #         fecha_hoy = time.localtime()
            #         fecha_formateada = time.strftime('%d-%m-%Y', fecha_hoy)
            #         auto_data = {
            #             'date': fecha_formateada,
            #             'invoice_number': invoice.name,
            #             'customer': invoice.partner_id.name,
            #             'address': invoice.partner_id.street,
            #             "packing_name": self.packing_name,
            #             "packing_scac": self.packing_scac,
            #             "packing_caat": self.packing_caat,
            #             "packing_truck": self.packing_truck,
            #             "packing_trailer": self.packing_trailer,
            #             "comentarios": self.comentarios,
            #             "tramitador": self.tramitador
            #             }
                    
            #         data.append({
            #         'color': production.product_qty,
            #         'description': production.product_id.display_name,
            #         'qty': production.product_qty,  
            #         'unit_price': production.product_id.list_price,
            #         'price_extra': price_final.get(production.product_id.id, 0.0),
            #         'total price':ganancia_total,
            #         'disc':discount,
            #         'wheels': wheels_count.get(production.product_id.id, 0.0),
            #         'freight_price': freight_partner.freight_prices,
            #         'ganancia': ganancias.get(production.product_id.id, 0.0),
            #         'total': precio_total_individual.get(production.product_id.id, 0.0)
            #         })
            # print(data)
            # return self.env.ref('logistics_document_packages.report_packing_fin_action').report_action(self, data={
            # 'sale_order_id': self.sale_order.id,
            # 'data': data,
            # 'auto_data': auto_data,
            # })
        # endregion
        elif current_state == 'Sales Orders':
            #Verifica si el estado actual (current_state) es igual a 'Sales Orders
            return self.env.ref('logistics_document_packages.report_log_document_sale_order').report_action(self)
        #mso
        elif current_state == 'MSO':
          
            # Esta sección del código maneja 
            # la generación de reportes para documentos MSO , 
            # con dos flujos distintos según la 
            # cantidad de productos seleccionados. 
           
            fullData = []
            if self.sale_order:
                #orden de venta seleccionada 
                sale_order = self.sale_order
                #almacena los pesos de cada producto de la sale order
                trailers_weight_details = {}
                #almacena todos los productos de la orden de venta
                selected_products = []
                #contador para productos
                selected_count = 0  
                #se ejecuta solo cuando se selecciona un producto
                for mso_data in self.mso_dictionary:
                    #contiene los productos disponibles para seleccion
                    if mso_data.checkbox == True:
                        selected_count += 1
                        product = mso_data.product
                        if product:
                            weight_info = product.dry_weight
                            trailers_weight_details = weight_info
                            selected_products.append({
                                    'weight': weight_info
                            })
                #se ejecuta cuando se selecciona mas de un producto       
                if selected_count > 1:
                    fullData = [] #almacena todos los datos estructurados para el reporte
                    for data in self.get_data(): #manda llamar los campos declarados en get data  
                        for msodata in self.mso_dictionary: # busca los productos dentro del modelo mso dictionary
                            if msodata.vin_text == data['vin']: # obtiene el vin
                                counter = 0 # contador para el numero de productos seleccionados
                                data["shipping_weight"] = product.dry_weight #obtiene el peso del producto 
                                counter+= 1
                                fullData.append(data)#genera el reporte con los datos acumulados 
                    return self.env.ref('logistics_document_packages.report_all_mso_action').report_action(self, data={
                        'id': sale_order.id,
                        'full_data': fullData,
                        'selected_products': selected_products,
                    })
                #si solo selecciona un producto
                else:
                    fullData = []
                    if selected_products:
                        fullData = selected_products
                        for product in selected_products:
                            print(f"Producto seleccionado: Peso: {product['weight']}")
                    #cuando no selecciona ningun producto
                    else:
                        raise UserError("Por favor, seleccione al menos un producto para imprimir.")  
                    #manda llamar la accion relacionada al xml de mso para generar los reportes en pdf      
                    return self.env.ref('logistics_document_packages.report_mso_action').report_action(self, data={
                    'id': sale_order.id,
                    'full_data': self.get_data(), 
                    'trailers_weight_details': trailers_weight_details,
                    'selected_products': selected_products,
                    })
        #factura   
        elif current_state == 'Factura':
            # Obtiene la factura asociada a la orden de venta y la imprime. 
            sale_order = self.env['sale.order'].browse(self.sale_order.id)
            if sale_order.invoice_ids:
                factura = sale_order.invoice_ids[0]
                if factura:
                    report_action = self.env['ir.actions.report'].search([
                ('report_name', '=', 'account.report_invoice')
            ], limit=1)

            if report_action:
                return report_action.report_action(factura)
            else:
                raise UserError("Error al imprimir el reporte de factura.")
        

        elif current_state == 'Declaracion':
            
            # Manda llamar la accion que 
            # ejecuta el xml correspondiente para generar el reporte de la declaracion 
           
            return self.env.ref('logistics_document_packages.report_HS7_action').report_action(self,data={
                 "sale_order_id": self.sale_order.id,
            })
            
        #HS7
        elif current_state == 'HS7':
            
            # Busca la orden de produccion relacionada a la orden de venta que 
            # se haya seleccionado para despues obtener el producto y el vin
           
            manufacturing_orders = self.env['mrp.production'].search([('origin', '=', self.sale_order.name)])
            reports = [] 
            for order in manufacturing_orders:
                if order.product_id and order.vin_dispayed:
                    reports.append({
                        'report_ref': 'logistics_document_packages.report_decla_action',
                        'data': {
                            "sale_order_id": self.sale_order.id,
                            "product": order.product_id.trailer_code,
                            "vin": order.vin_dispayed,
                        }
                    })
            
        
        # combina múltiples archivos PDF en uno solo
        merger = PdfFileMerger()
        # Itera sobre cada reporte definido en la lista 'reports'
        for report_data in reports:
            # Obtiene la referencia al reporte en Odoo usando el XML ID
            report_ref = self.env.ref(report_data['report_ref'])
            # Valida si el reporte existe, de lo contrario lanza error
            if not report_ref:
                raise UserError(f"Report reference {report_data['report_ref']} not found.")
            # Verifica si el reporte tiene datos asociados
            if report_data['data'] != None:
                # Renderiza el reporte a PDF con los datos proporcionados
                # _render_qweb_pdf devuelve el contenido PDF 
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(
                    report_data['report_ref'],
                    data=report_data['data']
                )
            # Si se generó contenido PDF correctamente crea un objeto BytesIO para manejar el contenido PDF en memoria
            if pdf_content:
                pdf_io = BytesIO(pdf_content)
                merger.append(pdf_io)
        # Crea un nuevo buffer de bytes para el PDF combinado final
        output = BytesIO()
        # Escribe todos los PDFs combinados en el buffer de salida
        merger.write(output)
        # Cierra el merger para liberar recursos
        merger.close()
        # Rebobina el buffer al inicio para lectura
        output.seek(0)
        # Codifica el contenido PDF en base64 para almacenamiento
        data = base64.b64encode(output.read())
        # Cierra el buffer de salida
        output.close()
        # Crea un registro de adjunto en Odoo con el PDF combinado
        attachment = self.env['ir.attachment'].create({
            'name': 'Logistics_document_packages.pdf',  # Nombre del archivo
            'datas': data,  # Contenido del PDF en base64
            'type': 'binary',  # Tipo de archivo
            'res_model': self._name,  # Modelo al que se asocia
            'mimetype': 'application/pdf',  # Tipo MIME
        })

        # Retorna una acción para descargar el archivo PDF
        return {
            'type': 'ir.actions.act_url',  # Tipo de acción: URL
            'url': f'/web/content/{attachment.id}?download=true',  # URL de descarga
            'target': 'self',  # Abrir en la misma ventana
        }

  
        # #ver historial de descargas
        # def action_show_downloads(self):
        #     return {
        #         'name': 'Archivos Descargados',
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'ir.attachment',
        #         'view_mode': 'tree,form',
        #         'domain': [('id', 'in', self.downloaded_attachment_ids.ids)],
        #         'target': 'current',
        #         'context': {'create': False}, 
        #     }

        # Define la acción para descargar un documento
    def action_download(self):
        # Asegura que solo se trabaje con un registro (evita operaciones por lotes)
        self.ensure_one()
        # Crea un registro de adjunto (attachment) en Odoo con el documento PDF
        attachment = self.env['ir.attachment'].create({
            'name': f'Documento_{self.name or self.id}.pdf', # Nombre del archivo 
            'type': 'binary',  # Tipo de archivo (binario)
            'datas': self.file,  # Contenido del archivo en base64 
            'res_model': 'logistics.log_document',  # Modelo relacionado
            'res_id': self.id,  # ID del registro relacionado
            'mimetype': 'application/pdf'  # Tipo (PDF)
        })

        # Actualiza el documento actual para vincular el nuevo adjunto
        self.write({
            'downloaded_attachment_ids': [(4, attachment.id)],
        })

        # Crea un registro de log para rastrear la descarga
        self.env['logistics.download.log'].create({
            'document_id': self.id,  # ID del documento descargado
            'download_time': fields.Datetime.now(),  # Marca temporal de la descarga
            'user_id': self.env.user.id,  # Usuario que realizó la descarga
            'attachment_id': attachment.id  # Referencia al adjunto creado
        })

        # Retorna una acción para descargar el archivo en el navegador
        return {
            'type': 'ir.actions.act_url',  # Tipo de acción: abrir URL
            'url': f'/web/content/{attachment.id}?download=true',  # URL de descarga del adjunto
            'target': 'self',  # Abre en la misma pestaña/ventana
        }
    
    def action_print_all_documents(self):
        """
        esta funcion envia por correo electronico 
        todos los reportes de logistica
        adjuntos en un solo pdf
        """
        self.ensure_one()
        if not self.email:
            raise UserError("Debe ingresar un correo electrónico.") 
        merger = PdfFileMerger()
        reports = []
        #Generacion del documento de paking y registro de datos manuales en data
        reports.append({
                'report_ref': 'logistics_document_packages.report_packing_action',
                'data': {
                    "sale_order_id": self.sale_order.id,
                    "packing_name": self.packing_name,
                    "packing_scac": self.packing_scac,
                    "packing_caat": self.packing_caat,
                    "packing_truck": self.packing_truck,
                    "packing_plates": self.packing_plates,
                    "packing_trailer": self.packing_trailer,
                    "packing_plates_trailer": self.packing_plates_trailer,
                    "comentarios": self.comentarios,
                    "tramitador": self.tramitador
                }
                
            })
        #Generacion del documento de HS7
        reports.append({
                'report_ref': 'logistics_document_packages.report_HS7_action',
                'data':{
                    "sale_order_id": self.sale_order.id,
                }
            })
        # Busca la factura en la orden de venta seleccionada y la imprime
        if self.sale_order.invoice_ids:
            factura = self.sale_order.invoice_ids[0]
            if factura:
                report_action = self.env['ir.actions.report'].search([('report_name', '=', 'account.report_invoice')], limit=1)
                reports.append({
                    'report_ref': report_action.xml_id,
                    'docids':factura.id,
                    'data':None
                })
        #MSO
        fullData = [] #almacena todos los datos estructurados para el reporte
        if self.sale_order: #orden de venta seleccionada
            for data in self.get_data(): # manda llamar los datos declarados en get data
                for msodata in self.mso_dictionary: #busca los campos en el modelo mso data
                    if msodata.vin_text == data['vin']: #obtiene el vin
                        product_info = self.env['product.template'].search([('dry_weight', '=', msodata.product.id)], limit=1) #obtener el peso del producto
                        if product_info: 
                            # Agrega el peso del producto a los datos actuales
                            data["dry_weight"] = product_info.dry_weight 
                            # Crea una COPIA del diccionario de datos y lo agrega a la lista fullData
                        fullData.append(data.copy())
                        break 
            # Agrega un nuevo reporte a la lista de reports (reportes a generar)
            reports.append({
                'report_ref': 'logistics_document_packages.report_all_mso_action',
                'data': {
                    'id': self.sale_order.id,
                    'full_data': fullData,
                }
            })
            
        #declaracion
        fecha_hoy = time.localtime() #fecha actual
        fecha_formateada = time.strftime('%d-%m-%Y', fecha_hoy) #formato de fecha dia/mes/año
        manufacturing_orders = self.env['mrp.production'].search([('origin', '=', self.sale_order.name)]) #busca la orden de manufactura origen en la orden de venta
        for order in manufacturing_orders: #busca valores en la orden de manufactura
            if order.product_id and order.vin_dispayed: #obtiene el vin del producto
                reports.append({
                'report_ref': 'logistics_document_packages.report_decla_action',
                'data': {
                    "sale_order_id": self.sale_order.id,
                    "product": order.product_id.trailer_code,
                    "vin": order.vin_dispayed,
                    "date": fecha_formateada,
                }
            })
                
        # Imprime la lista de reportes 
        print(reports)
        # Procesa cada reporte en la lista 'reports'
        for report_data in reports:
            # Obtiene la referencia al reporte 
            report_ref = self.env.ref(report_data['report_ref'])
            # Valida si el reporte existe en el sistema
            if not report_ref:
                # Lanza error si no encuentra el reporte
                raise UserError(f"No se encontró el reporte: {report_data['report_ref']}")
            if report_data['data'] != None: #si encuentra el reporte lo renderiza
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(
                    report_data['report_ref'],  
                    data=report_data['data']   
                )
            elif report_data['data'] == None and report_data['docids'] != None: #verifica si el reporte tiene datos personalizados
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(
                report_data['report_ref'],  #Identificador del reporte xml
                report_data['docids'],      
                data=None                   
                )
            else:
                #Genera reporte básico (sin datos ni IDs específicos)
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(
                    report_data['report_ref'] 
                )

            # Si se generó contenido PDF exitosamente
            if pdf_content:
                # Crea un archivo en memoria con el contenido PDF
                pdf_io = BytesIO(pdf_content)
                # Agrega el PDF al objeto 'merger' que combina múltiples PDFs
                merger.append(pdf_io)
        #los convierte a pdf y los envia a un correo especifico
        output = BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        data = base64.b64encode(output.read())
        output.close()
        self.downloaded_attachment_ids = self.env['ir.attachment'].create({
            'name': 'Logistics_document_packages.pdf',
            'datas': data,
            'type': 'binary',
            'mimetype': 'application/pdf',
        })
        self.sale_order.downloaded_attachment_ids = self.downloaded_attachment_ids
        self.sale_order.logistics_data = self
        attachment = self.downloaded_attachment_ids
        # self.write({
        #     'downloaded_attachment_ids': [(4, attachment.id)],
        # })
        #contenido del correo
        mail_values = {
        'subject': f'Documentos - Pedido {self.sale_order.name}',
        'body_html': f'''
            <p>Estimado cliente,</p>
            <p>Adjunto encontrará los documentos del pedido {self.sale_order.name}.</p>
        ''',
        'email_to': self.email,
        'attachment_ids': [(4, attachment.id)],
        }
        self.env['mail.mail'].create(mail_values).send()
        #notificacion de correo enviado
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': f'Documentos enviados a {self.email}',
                'type': 'success',
            }
        }
        # Método para actualizar el estado MSO 
    def mso_state(self):
        # Verifica si el campo mso_dictionary está vacío 
        if self.mso_dictionary != False:
            # Crea un array auxiliar para almacenar los nuevos registros MSO
            aux_array = []
            # Busca órdenes de producción relacionadas con la orden de venta actual
            production = self.env['mrp.production'].search([
                ('origin', '=', self.sale_order.name)
            ])
            # Itera sobre todas las órdenes de producción vinculadas a la orden de venta
            for production in self.sale_order.mrp_production_ids:
                # Valida que existan los campos requeridos
                if production.product_id and production.vin_relation and self.sale_order:
                    # Crea un nuevo registro en el modelo mso.data con:
                    aux_array.append(self.env['mso.data'].create({
                        'vin': production.vin_relation.id,      # vin
                        'vin_text': production.vin_relation.vin, # Número de VIN
                        'product': production.product_id.id,     # ID del producto
                        'sale_order': self.sale_order.id,       # ID de la orden de venta
                    }).id)  # Guarda el ID del nuevo registro
                else:
                    # Lanza error si falta algún campo obligatorio
                    raise ValueError("Uno de los campos requeridos no está definido.")

            # Actualiza el campo mso_dictionary con los nuevos IDs creados
            self.mso_dictionary = aux_array

            
           


   
   

    




    







    
    


    
