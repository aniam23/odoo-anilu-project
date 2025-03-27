# from odoo import api, models, fields
# import time

# class PackingReport(models.AbstractModel):
#     _name = 'report.logistics_document_packages.report_packing_fac_template'
#     _description = 'Print report packing'

#     def _get_report_values(self, docids, data=None):
      
#         sale_order = self.env['sale.order'].search([('id', '=', data.get('sale_order_id'))], limit=1)
#         if not sale_order:
#             return {'error': 'Sale order not found'}

#         invoices = sale_order.invoice_ids
#         invoice = invoices[:1]  
#         print(invoice)

#         fecha_hoy = time.localtime()
#         fecha_formateada = time.strftime('%d-%m-%Y', fecha_hoy)
#         print(fecha_formateada)

#         wheels_count = {}
#         rims_info = {}
#         claves_product = {}
#         weight_trailer = {}
#         wheel_trailer = {}
        
#         # numero de birlos:
#         wheel_total = 0
#         if sale_order.mrp_production_ids:
#             for production in sale_order.mrp_production_ids.filtered(lambda p: p.state != 'cancel'):
#                 bom_lines = production.product_id.bom_ids.mapped('bom_line_ids')
#         if bom_lines:
#             tire_id = 0
#             for line in bom_lines:
#                 if 'llanta' in line.product_id.display_name.lower(): 
#                     tire_id = line.product_id
#             wheel_info = self.env['wheel.nut'].search([('ref_product', '=', tire_id.id)])
#             for info in wheel_info:
#                 wheel_trailer[production.product_id.id] = info.number_wheel_nut  
#             if sale_order and sale_order.order_line:
#                 for line in sale_order.order_line:
#                     product_id = line.product_id.id
#                     if product_id in wheel_trailer:
#                         wheel_total = wheel_trailer[product_id] 

#         # peso total de los remolques de sale order:
#         weight_total = 0
#         if sale_order.mrp_production_ids:
#             for production in sale_order.mrp_production_ids.filtered(lambda p: p.state != 'cancel'):
#                 weight_info = self.env['weight.info'].search([('ref_trailer', '=', production.product_id.id)])
#                 for info in weight_info:
#                     weight_trailer[production.product_id.id] = info.weight  
#             if sale_order and sale_order.order_line:
#                 for line in sale_order.order_line:
#                     product_id = line.product_id.id
#                     if product_id in weight_trailer:
#                         weight_total += weight_trailer[product_id]

#         # numero de llantas
#         if sale_order.mrp_production_ids:
#             for production in sale_order.mrp_production_ids.filtered(lambda p: p.state != 'cancel'):
#                 bom_lines = production.product_id.bom_ids.mapped('bom_line_ids')
#                 if bom_lines:
#                     for line in bom_lines:
#                         if 'llanta' in line.product_id.display_name.lower(): 
#                             wheels_count[production.id] = line.product_qty
#                             product_name = line.product_id.display_name
#                             first_4_words = ' '.join(product_name.split()[:4])
#                             rims_info[production.id] = first_4_words

#         # Asignar claves correspondiente segun la categoria de cada producto
#         for line in sale_order.order_line:
#             categoria = line.product_id.categ_id
#             if categoria:
#                 claves_product[line.product_id.id] = categoria
#                 if categoria.name == 'All':
#                     claves_product[line.product_id.id] = '8716399999'  
#                 elif categoria.name == 'accesorio':
#                     claves_product[line.product_id.id] = '8609000100'
#                 elif categoria.name == 'contenedor':
#                     claves_product[line.product_id.id] = '8716909994'

#         # claves SAT por producto
#         clave_sat = None
#         for product_id, clave_producto in claves_product.items():
#             if clave_producto == '8716399999':
#                 clave_sat = '25101602'
#             elif clave_producto == '8609000100':
#                 clave_sat = '24112004'
#             elif clave_producto == '8716909994':
#                 clave_sat = '25101602'

#         auto_data = {
#             'date': fecha_formateada,
#             'invoice_number': invoice.name if invoice else "N/A",
#             'customer': invoice.partner_id.name if invoice else "N/A",
#             'products': [],
#             'address': invoice.partner_id.street if invoice and invoice.partner_id else "N/A"
#         }

#         if sale_order.mrp_production_ids:
#             for production in sale_order.mrp_production_ids.filtered(lambda p: p.state != 'cancel'):
#                 auto_data['products'].append({
#                     'product': production.product_id.display_name,
#                     'vin': production.vin_dispayed if production.vin_dispayed else "N/A",
#                     'qty': production.product_qty,
#                     'wheels': wheels_count.get(production.id, 0.0),
#                     'rims': rims_info.get(production.id, "N/A"),  
#                     'frac': claves_product.get(production.product_id.id, "N/A"),
#                     'clave_sat': clave_sat,
#                     'weight': weight_total,
#                     'wheel_nut': wheel_total,
#                     'color': fecha_formateada
#                 })

#         return {
#             'manual_data': data,
#             'auto_data': auto_data,
#         }
