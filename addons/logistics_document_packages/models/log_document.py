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
        ('Declaracion', 'Declaracion'),
        ('State Send', 'State Send')
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
    comentarios = fields.Text('COMMENTS')
    tramitador = fields.Text('TRAMITADOR')
  
    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super(LogisticsLogDocument, self)._valid_field_parameter(field, name)
    
    @api.model_create_multi
    def create(self, vals):
        if 'name' not in vals[0]:
            unique_name = f"Document_{random.randint(1, 9999)}"
            vals[0]['name'] = unique_name  
        record = super(LogisticsLogDocument, self).create(vals) 
        record.setDate()
        return record
        
    def _compute_send_button_visible(self):
        for record in self:
            my_model_records = self.env['my.model'].search([('sale_order_id', '=', record.id)])
            record.send_button_visible = bool(my_model_records)

    def setDate(self):
        for record in self:
            record.date = datetime.today()

    @api.onchange('sale_order')
    def _onchange_sale_order(self):
        # self.mso_state()
        if self.sale_order:
            for invoice in self.sale_order.invoice_ids:
               if not invoice.print_button_visible:
                    raise UserError(
                        f"La factura asociada con la orden de venta ({self.sale_order.name}) no tiene el título generado. No puede seleccionarse esta orden de venta."
                    )
            else:
                manufacturing_orders = self.env['mrp.production'].search([('origin', '=', self.sale_order.name)])
            if not manufacturing_orders:
                    raise UserError(f"La factura asociada con la orden de venta ({self.sale_order.name}) no tiene una orden de produccion asociada.")
            
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
    
   
    
    
    
    def send_action(self):
        order = None
        send_state_form_action_window = self.env.ref('send_order.send_state_form_action_window', False)
        self.ensure_one()
        sale_order = self.sale_order
        document_id = self.id 
        fecha_hoy = time.localtime()
        fecha_formateada = time.strftime('%Y-%m-%d', fecha_hoy)
        print(fecha_formateada)
        if sale_order:
            customer_email = sale_order.partner_id.email  
            if not customer_email:
                print("No se encontró el email del cliente en la orden de venta.") 
            sale_order.write({'show_send_order_button': True})
            sale_order.action_confirm()
            order = self.env['send.order'].browse(self.id)
        if order.exists():  
            if hasattr(order, 'value_state'): 
                try:
                    order.value_state()  
                    print("Send Order encontrado y value_state ejecutado:", order)
                except Exception as e:
                    print(f"Error al ejecutar value_state: {e}")
            else:
                print("Método value_state no encontrado en el objeto send.order.")
        else:
            if sale_order:
                customer_name = sale_order.partner_id.display_name
                customer_email = sale_order.partner_id.email  
                product_id = sale_order.order_line[0].product_id.id  
                invoice_number = sale_order.name
                shipping_location = sale_order.warehouse_id.name
                ship_date = fecha_formateada
                creation_log = sale_order.create_date
                due_date = self.sale_order.validity_date
                ship_to = self. sale_order.partner_id.contact_address
          
                
                new_order = self.env['send.order'].create({
                    'customer_name': customer_name, 
                    'customer_email': customer_email,  
                    'product_id': product_id,
                    'invoice_number': invoice_number,
                    'shipping_location': shipping_location,
                    'ship_date': ship_date,
                    'creation_log': creation_log,
                    'due_date': due_date,
                    'ship_to': ship_to,
                    'sale_order': self.sale_order.id
               
                })
                print("Nuevo Send Order creado:", new_order)

               
                try:
                    if hasattr(new_order, 'value_state'):
                        new_order.value_state()
                        print("Nuevo Send Order ejecutando value_state:", new_order)
                except Exception as e:
                    print(f"Error al ejecutar value_state en el nuevo orden: {e}")
        return {
            'name': 'Send Order Form',
            'type': 'ir.actions.act_window',
            'res_model': 'send.order',
            'view_mode': 'form',
            'view_id': send_state_form_action_window.view_id.id if send_state_form_action_window else False,
            'flags': {'action_buttons': True},
            'context': {
                'default_document_id': document_id,
                'default_sale_order_id': sale_order.id if sale_order else False
            }
        }


    
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
        if "_" in bodyTypeString:
            return "ROLL OFF DUMP"
        else:
            return bodyTypeString
        
    def format_gvwr(self, product):
        lb = product.gvwr_related.weight_lb
        kg = product.gvwr_related.weight_kg
        name = product.display_name
        return {
            "gvwr": str(kg)+" KG ("+str(lb)+" LBS)",
            "model": name
        }
    def get_data(self):
        list_of_data = []
        mo_orders = []
        manufacturing_order_list = self.env['mrp.production'].search([])
        for order in manufacturing_order_list:
            if order.origin != False and order.origin == self.sale_order.name:
                mo_orders.append(order)

        for mo_order in mo_orders:
            mo_date = mo_order.date_planned_start
            product_vin = mo_order.vin_dispayed
            product_body_type = mo_order.vin_relation.trailer_type
            dateAndYear = self.format_date(str(mo_date))
            bodyType = self.format_body_type(product_body_type)
            productInfo = self.format_gvwr(mo_order.product_id)
            invoice_name = self.invoice.display_name
            weight = self.weight
            
            list_of_data.append({
                "date": dateAndYear["date"],
                "vin":product_vin,
                "body_type": bodyType,
                "gvwr": productInfo["gvwr"],
                "invoice_number": invoice_name,
                "year": dateAndYear["year"],
                "shipping_weight": weight,
                "model_name": productInfo["model"],
                "last_data": False
            })
        
        list_of_data[len(list_of_data)-1]["last_data"] = True
        return list_of_data
    
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
               

    def print_action(self):
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
                        "comentarios": self.comentarios,
                        "tramitador": self.tramitador
                    })
        
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
        
        elif current_state == 'Sales Orders':
            return self.env.ref('logistics_document_packages.report_log_document_sale_order').report_action(self)
        
        elif current_state == 'MSO':
            fullData = []
            if self.sale_order:
                sale_order = self.sale_order
                trailers_weight_details = {}
                selected_products = []
                selected_count = 0  
                for mso_data in self.mso_dictionary:
                    if mso_data.checkbox == True:
                        selected_count += 1
                        product = mso_data.product
                        if product:
                            weight_info = self.env['weight.info'].search([('ref_trailer', '=', product.id)])
                            for weight in weight_info:
                                trailers_weight_details = weight.weight
                                selected_products.append({
                                    'weight': weight.weight
                                })
                        
                       
                if selected_count > 1:
                    fullData = []
                    for data in self.get_data():  
                        for msodata in self.mso_dictionary:
                            if msodata.vin_text == data['vin']:
                                weight_info = self.env['weight.info'].search([('ref_trailer', '=', msodata.product.id)])
                                counter = 0
                                data["shipping_weight"] = weight_info.weight
                                counter+= 1
                                fullData.append(data)
                    return self.env.ref('logistics_document_packages.report_all_mso_action').report_action(self, data={
                        'id': sale_order.id,
                        'full_data': fullData,
                        'selected_products': selected_products,
                    })
                else:
                    fullData = []
                    if self.sale_order:
                        sale_order = self.sale_order
                        trailers_weight_details = {}
                        selected_products = []
                        for mso_data in self.mso_dictionary:
                            if mso_data.checkbox == True:
                                product = mso_data.product
                                if product:
                                    weight_info = self.env['weight.info'].search([('ref_trailer', '=', product.id)])
                                    for weight in weight_info:
                                        trailers_weight_details = weight.weight
                                        selected_products.append({
                                            'weight': weight.weight
                                        })
                    if selected_products:
                        fullData = selected_products
                        for product in selected_products:
                            print(f"Producto seleccionado: Peso: {product['weight']}")
                    else:
                        raise UserError("Por favor, seleccione al menos un producto para imprimir.")        
                    return self.env.ref('logistics_document_packages.report_mso_action').report_action(self, data={
                    'id': sale_order.id,
                    'full_data': self.get_data(), 
                    'trailers_weight_details': trailers_weight_details,
                    'selected_products': selected_products,
                    })

        elif current_state == 'Factura':
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
             return self.env.ref('logistics_document_packages.report_HS7_action').report_action(self,data={
                 "sale_order_id": self.sale_order.id,
            })
            
        
        elif current_state == 'HS7':
            manufacturing_orders = self.env['mrp.production'].search([('origin', '=', self.sale_order.name)])
            reports = [] 
            for order in manufacturing_orders:
                if order.product_id and order.vin_dispayed:
                    reports.append({
                        'report_ref': 'logistics_document_packages.report_decla_action',
                        'data': {
                            "sale_order_id": self.sale_order.id,
                            "product": order.product_id.name,
                            "vin": order.vin_dispayed,
                        }
                    })
        
 
        merger = PdfFileMerger()
        for report_data in reports:
            report_ref = self.env.ref(report_data['report_ref'])
            if not report_ref:
                raise UserError(f"Report reference {report_data['report_ref']} not found.")
            if report_data['data'] != None:
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(report_data['report_ref'],data=report_data['data'])

            if pdf_content:
                pdf_io = BytesIO(pdf_content)
                merger.append(pdf_io)  
    
        output = BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        data = base64.b64encode(output.read())
        output.close()
        attachment = self.env['ir.attachment'].create({
            'name': 'Logistics_document_packages.pdf',
            'datas': data,
            'type': 'binary',
            'mimetype': 'application/pdf',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'web/content/{attachment.id}?download=true',
            'target': 'self',
        }
        

    def action_print_all_documents(self):
        email = self.env.context.get('email', False)  
        if not email:
            raise UserError('Debe proporcionar un correo electrónico para enviar los documentos.')
        merger = PdfFileMerger()
        reports = []
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
                    "comentarios": self.comentarios,
                    "tramitador": self.tramitador
                }
                
            })
      
        reports.append({
                'report_ref': 'logistics_document_packages.report_HS7_action',
                'data':{
                    "sale_order_id": self.sale_order.id,
                }
            })
        
        if self.sale_order.invoice_ids:
            factura = self.sale_order.invoice_ids[0]
            if factura:
                report_action = self.env['ir.actions.report'].search([('report_name', '=', 'account.report_invoice')], limit=1)
                reports.append({
                    'report_ref': report_action.xml_id,
                    'docids':factura.id,
                    'data':None
                })

        fullData =[]
        if self.sale_order:
            for data in self.get_data():
                for msodata in self.mso_dictionary:
                    if msodata.vin_text ==  data['vin']:
                        weight_info = self.env['weight.info'].search([('ref_trailer', '=', msodata.product.id)])
                        counter = 0
                        data["shipping_weight"] = weight_info.weight
                        counter+= 1
                        fullData.append(data)
            reports.append({
                'report_ref': 'logistics_document_packages.report_all_mso_action',
                'data': {
                    'id': self.sale_order.id,
                    'full_data': fullData,
                }
            })



        fecha_hoy = time.localtime()
        fecha_formateada = time.strftime('%d-%m-%Y', fecha_hoy)
        manufacturing_orders = self.env['mrp.production'].search([('origin', '=', self.sale_order.name)])
        for order in manufacturing_orders:
            if order.product_id and order.vin_dispayed:
                reports.append({
                'report_ref': 'logistics_document_packages.report_decla_action',
                'data': {
                    "sale_order_id": self.sale_order.id,
                    "product": order.product_id.name,
                    "vin": order.vin_dispayed,
                    "date": fecha_formateada,
                }
            })
                

        print(reports)
        for report_data in reports:
            report_ref = self.env.ref(report_data['report_ref'])
            if not report_ref:
                raise UserError(f"Report reference {report_data['report_ref']} not found.")
            if report_data['data'] != None:
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(report_data['report_ref'],data=report_data['data'])
            elif report_data['data'] == None and report_data['docids'] != None:
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(report_data['report_ref'],report_data['docids'], data=None)
            else:
                pdf_content, _ = report_ref.sudo()._render_qweb_pdf(report_data['report_ref'])
            if pdf_content:
                pdf_io = BytesIO(pdf_content)
                merger.append(pdf_io)

        
            output = BytesIO()
            merger.write(output)
            merger.close()
            output.seek(0)
            data = base64.b64encode(output.read())
            output.close()
            attachment = self.env['ir.attachment'].create({
                'name': 'Logistics_document_packages.pdf',
                'datas': data,
                'type': 'binary',
                'mimetype': 'application/pdf',
            })

        
            mail_values = {
                'subject': f'Documentos de Logística - Pedido {self.sale_order.name}',
                'body_html': '''
                    <p>Estimado cliente,</p>
                    <p>Adjunto encontrará todos los documentos relacionados con su pedido.</p>
                ''',
                'email_to': email,
                'attachment_ids': [(4, attachment.id)],
            }
        
            self.env['mail.mail'].create(mail_values).send()
        
            return {
                "email": email,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Documentos enviados',
                    'message': f"Todos los documentos han sido enviados a {email}",
                    'sticky': False,
                    'type': 'success',
                }
            }

    
    def mso_state(self):
        if self.mso_dictionary != False:
            aux_array = []
            production = self.env['mrp.production'].search([('origin', '=', self.sale_order.name)])
            for production in self.sale_order.mrp_production_ids:
                if production.product_id and production.vin_relation and self.sale_order:
                    aux_array.append(self.env['mso.data'].create({
                        'vin': production.vin_relation.id,
                        'vin_text': production.vin_relation.vin,
                        'product': production.product_id.id,
                        'sale_order': self.sale_order.id,
                    }).id)
                else:
                    raise ValueError("Uno de los campos requeridos no está definido.")
            self.mso_dictionary = aux_array


            
           


   
   

    




    







    
    


    
