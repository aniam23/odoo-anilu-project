from odoo import api, models, fields 
import time 

class PackingReport(models.AbstractModel):
    """Modelo abstracto para generar reportes de empaque"""
    _name = 'report.logistics_document_packages.report_packing_template' 
    _description = 'Print report packing'

    def _get_report_values(self, docids, data=None):
        """
        Método principal que obtiene los valores para el reporte
            docids: IDs de documentos
            data: Datos adicionales
        Returns:
            Diccionario con datos para el reporte
        """
        # Búsqueda de la orden de venta
        sale_order = self.env['sale.order'].search(
            [('id', '=', data.get('sale_order_id'))], 
            limit=1
        )
        
        if not sale_order:  # Validación si no existe la orden
            return {'error': 'Sale order not found'}
        
        # Obtención de facturas relacionadas
        invoices = sale_order.invoice_ids  # Todas las facturas de la orden
        invoice = invoices[:1]  # Tomamos la primera factura
        
        #  Formateo de fecha actual
        fecha_hoy = time.localtime()  # Fecha y hora actual
        fecha_formateada = time.strftime('%d-%m-%Y', fecha_hoy)  # Formato día-mes-año
        
        # Inicialización de diccionarios para almacenamiento de datos
        wheels_count = {}  # {production_id: cantidad_llantas}
        rims_info = {}  # {production_id: info_rin}
        claves_product = {}  # {product_id: clave_producto}
        weight_trailer = {}  # {product_id: peso} (no se usa posteriormente)
        wheel_trailer = {}  # {product_id: numero_tuercas}
        wheel_total = 0  # Contador total de tuercas
        
        #  Procesamiento de órdenes de manufactura (MRP)
        if sale_order.mrp_production_ids:  # Si hay producciones asociadas
            # Filtramos producciones no canceladas
            active_productions = sale_order.mrp_production_ids.filtered(
                lambda p: p.state != 'cancel'
            )
            
            for production in active_productions:
                # Obtenemos líneas de lista de materiales (BOM)
                bom_lines = production.product_id.bom_ids.mapped('bom_line_ids')
                
                # Procesamiento de llantas en BOM
                if bom_lines:
                    tire_id = 0  # Inicializamos ID de llanta
                    for line in bom_lines:
                        # Buscamos productos que sean llantas
                        if 'llanta' in line.product_id.display_name.lower(): 
                            tire_id = line.product_id  # Guardamos el ID de la llanta
                    
                    # Buscamos información de tuercas para estas llantas
                    if tire_id:
                        wheel_info = self.env['wheel.nut'].search([
                            ('ref_product', '=', tire_id.id)
                        ])
                        
                        # Almacenamos info de tuercas por producto
                        for info in wheel_info:
                            wheel_trailer[production.product_id.id] = info.number_wheel_nut
        
        # Cálculo de total de tuercas en la orden
        if sale_order and sale_order.order_line:
            for line in sale_order.order_line:
                product_id = line.product_id.id
                if product_id in wheel_trailer:
                    wheel_total = wheel_trailer[product_id] 

        # Cálculo de peso total de los productos
        weight_total = 0  # Inicializamos contador de peso
        for line in sale_order.order_line:
            product_template = line.product_id.product_tmpl_id 
            if product_template.dry_weight:  # Si tiene peso definido
                weight_total += product_template.dry_weight  # Sumamos al total

        # Procesamiento adicional de producciones para llantas y rines
        if sale_order.mrp_production_ids:
            for production in sale_order.mrp_production_ids.filtered(
                lambda p: p.state != 'cancel'
            ):
                bom_lines = production.product_id.bom_ids.mapped('bom_line_ids')
                if bom_lines:
                    for line in bom_lines:
                        if 'llanta' in line.product_id.display_name.lower():
                            # Guardamos cantidad de llantas por producción
                            wheels_count[production.id] = line.product_qty
                            
                            # Extraemos las 4 primeras palabras del nombre
                            product_name = line.product_id.display_name
                            first_4_words = ' '.join(product_name.split()[:4])
                            rims_info[production.id] = first_4_words

        # Asignación de claves por categoría de producto
        for line in sale_order.order_line:
            categoria = line.product_id.categ_id
            if categoria:
                if categoria.name == 'All':
                    claves_product[line.product_id.id] = '8716399999'
                elif categoria.name == 'accesorio':
                    claves_product[line.product_id.id] = '8609000100'
                elif categoria.name == 'contenedor':
                    claves_product[line.product_id.id] = '8716909994'

        # Determinación de clave SAT
        clave_sat = None  # Inicializamos clave SAT
        for product_id, clave_producto in claves_product.items():
            if clave_producto == '8716399999':
                clave_sat = '25101602'
            elif clave_producto == '8609000100':
                clave_sat = '24112004'
            elif clave_producto == '8716909994':
                clave_sat = '25101602'

        # Estructuración de datos automáticos
        auto_data = {
            'date': fecha_formateada,  # Fecha formateada
            'invoice_number': invoice.name if invoice else "N/A",  # Número factura
            'customer': invoice.partner_id.name if invoice else "N/A",  # Cliente
            'products': [],  # Lista para productos
            'address': invoice.partner_id.street if invoice and invoice.partner_id else "N/A"  # Dirección
        }

        # Llenado de información de productos
        if sale_order.mrp_production_ids:
            for production in sale_order.mrp_production_ids.filtered(
                lambda p: p.state != 'cancel'
            ):
                auto_data['products'].append({
                    'product': production.product_id.display_name,  # Nombre producto
                    'vin': production.vin_dispayed if production.vin_dispayed else "N/A",  # VIN
                    'qty': production.product_qty,  # Cantidad
                    'wheels': wheels_count.get(production.id, 0.0),  # N° llantas
                    'rims': rims_info.get(production.id, "N/A"),  # Info rines
                    'frac': claves_product.get(production.product_id.id, "N/A"),  # Clave
                    'clave_sat': clave_sat,  # Clave SAT
                    'weight': weight_total,  # Peso total
                    'wheel_nut': wheel_total,  # Total tuercas
                    'color': fecha_formateada  # Campo adicional (posiblemente para formato)
                })

        # Retorno de estructura final para el reporte
        return {
            'manual_data': data,  # Datos manuales originales
            'auto_data': auto_data,  # Datos calculados automáticamente
        }

