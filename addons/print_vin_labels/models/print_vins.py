from odoo import models, fields
import zebra_day.print_mgr as zdpm
from odoo.exceptions import UserError
import socket
import time

class PrintVins(models.Model):
    _name = 'print.vins'
    _description = 'Print VIN Labels'
    name = fields.Char(string='Name')
    sale_order = fields.Many2one('sale.order', string='Sales Orders')
    wheel_nut_id = fields.Many2many(comodel_name='wheel.nut', string='Wheel Nut Registry')
    printer_ids = fields.Many2many('iot.device', string='Impresoras disponibles')
    model_hs7 = fields.Many2many(comodel_name='model.hs7', string='MODEL HS7')
    gvwr= fields.Many2many(comodel_name='vin_generator.gvwr_manager', string='gvwr_related')
    gawr= fields.Many2many(comodel_name='vin_generator.vin_generator',  string='gawr_related')
    gawr_lb = fields.Float(string='Gawr lb')
    printer_port = fields.Integer(string='Puerto de la Impresora', default=9100)
    weight_total = fields.Float(string='Peso total')
    product_name =fields.Char(string='Product_name')
    
    def get_data(self):
        list_of_data = []
        manufacturing_order_list = self.env['mrp.production'].search([])
        for order in manufacturing_order_list:
            if hasattr(order, 'vin_dispayed') and order.vin_dispayed:
                product_vin = order.vin_dispayed
                product_name = order.product_id.display_name
                date = order.date_planned_start
                list_of_data.append({
                    "vin": product_vin,
                    "date":date,
                    "product_name": product_name,
                    "order_id": order.id,
                })
        if not list_of_data:
            raise ValueError("No se encontraron órdenes de producción con el campo 'vin_dispayed'.")
        return list_of_data

    
    def print_vins(self): 
        # Validar que se haya seleccionado una impresora
        if not self.printer_ids:
            raise UserError("Debe seleccionar al menos una impresora.")
            
        zlab = zdpm.zpl()
        data_list = self.get_data()
        
        if not self.gvwr:
            raise ValueError("No se ha seleccionado un registro para 'gvwr'.")
        gvwr_lb = self.gvwr.weight_lb
        gvwr_kg = self.gvwr.weight_kg
        
        if not self.gawr:
            raise ValueError("No se ha seleccionado un registro para 'gawr'.")
        
        gawr_libras = self.gawr.name
        gawr_lb = gawr_libras[5:9]
        gawr_kg = round(float(gawr_lb) * 0.453592, 2)
        gawr_kg = round(gawr_kg, 2)
        
        if not self.model_hs7:
            raise ValueError("No se ha seleccionado un registro en 'Wheel Nut Registry'.")
            
        product_name = self.model_hs7.ref_trailer.display_name
        model_string = self.model_hs7.model
        product = self.model_hs7.ref_trailer  
        weight_lb = product.dry_weight
        weight_kg = int(round(weight_lb * 0.453592)) 
        
        data_list = self.get_data()
        product_vin = None
        for data in data_list:
            if product_name.strip() == data["product_name"].strip(): 
                product_vin = data.get("vin")
                if product_vin:
                    print("Product VIN:", product_vin)
                    
        if not self.wheel_nut_id:
            raise ValueError("No se ha seleccionado un registro en 'Wheel Nut Registry'.")
            
        wheel_nut_string = self.wheel_nut_id.ref_product 
        wheel = wheel_nut_string.display_name.upper()  # Convertir a mayúsculas
        result = wheel[7:19]
        rin = wheel[50:60]
        lbs_wheels = ''
        tire_rating = ''
        
        if 'SINGLE' in wheel and 'R15' in wheel and ('10PLY' in wheel or '10PR' in wheel):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '2830 LBS'
        elif 'SINGLE' in wheel and 'R15' in wheel and ('8PLY' in wheel or '8PR' in wheel):
            lbs_wheels = '448 KPA/65 PSI'
            tire_rating = '2150 LBS'
        elif 'SINGLE' in wheel and 'R15' in wheel and ('6PLY' in wheel or '6PR' in wheel):
            lbs_wheels = '334 KPA/50 PSI'
            tire_rating = '1820 LBS'
        elif 'SINGLE' in wheel and 'R16' in wheel and ('10PLY' in wheel or '10PR' in wheel):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3520 LBS'
        elif 'DUAL' in wheel and 'R16' in wheel and ('10PLY' in wheel or '10PR' in wheel):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3080 LBS'
        elif 'SINGLE' in wheel and 'R16' in wheel and ('14PLY' in wheel or '14PR' in wheel):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '4400 LBS'
        elif 'DUAL' in wheel and 'R16' in wheel and ('14PLY' in wheel or '14PR' in wheel):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '3860 LBS'
        elif 'SUPER SINGLE' in wheel and 'R17.5' in wheel and ('18PLY' in wheel or '18PR' in wheel):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '6005 LBS'
        elif 'DUAL' in wheel and 'R17.5' in wheel and ('18PLY' in wheel or '18PR' in wheel):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '5675 LBS'
        
        print(f'Wheel: {wheel}')
        print(f'LBS: {lbs_wheels}')
        print(f'Tire Rating: {tire_rating}')
        print(f'RIN: {rin}')

        zpl_template = """
        ^XA
         ^FO650,50^ADR,20,10^FDThe weight of the cargo should never exceed {weight_kg} kg or {weight_lb} lbs^FS
         ^FO630,50^ADR,20,10^FDle poids du chargement ne doit jamais depasser {weight_kg} kg ou {weight_lb} lb.^FS
         ^FO490,5^ADR,20,10^FD      
            {result}  ^FS   
         ^FO490,210^ADR,20,10^FD  
                {lbs_wheels}  ^FS
             ^FO450,5^ADR,20,10^FD      
            {result}  ^FS   
         ^FO450,210^ADR,20,10^FD  
                {lbs_wheels}  ^FS
               ^FO400,5^ADR,20,10^FD      
            {result}  ^FS   
         ^FO400,210^ADR,20,10^FD  
                {lbs_wheels}  ^FS
         ^FO390,800^ADR,15,10^FWN^FDR^FD {product_vin} ^FS
         ^FO300,50^ADR,25,10^FDMANUFACTURED BY/FABRIQUE PAR: HORIZON TRAILERS MEXICO S. DE R.L. DE C.V.^FS
         ^FO280,50^ADR,25,10^FDGVWR / PNBV  {gvwr_kg} KG ( {gvwr_lb} LB) 
                                      DATE: 26/03/2025^FS  
         ^FO260,50^ADR,25,10^FDGAWR (EACH AXLE) / PNBE ( CHAQUE ESSIEU) {gawr_kg} KG({gawr_lb} )^FS
         ^FO240,50^ADR,25,10^FDTIRE/PNEU {result}  RIM/JANTE {rin} {tire_rating} ^FS
         ^FO215,50^ADR,25,10^FDCOLD INFL. PRESS/PRESS. DE GONFL. A FROID {lbs_wheels}/LCP SINGLE^FS
         ^FO190,50^A0R,20,20^FDTHIS VEHICLE TO ALL APPLICABLE U.S. FEDERAL MOTOR SAFETY STANDARDS IN EFFECT ON THE DATE OF MANUFACTURE ^FS
         ^FO170,50^A0R,20,20^FDSHOWN ABOVE.THIS VEHICLE CONFORMS TO ALL APPLICABLE STANDARDS PRESCRIBED UNDER CANADA.^FS
         ^FO150,50^A0R,20,20^FDATE OF MANUFACTURE./.. CE VEHICLE EST CONFORME A TOUS LES NORMES EN VIGUEUR A LA DATE DE SA FABRICATION.^FS
         ^FO130,50^A0R,20,20^FDSUR LA SECURITÉ DES VARIÉGLES AUTOMOBILES DU CANADA EN VIGUEUR A LA DATE DE SA FABRICATION.^FS
         ^FO90,50^ADR,15,10^FDVIN.:{product_vin}^FS
         ^FO90,500^ADR,15,10^FDTYPE: TRA/REM^FS
         ^FO90,800^ADR,15,10^FDMODEL: {model_string} ^FS
         ^XZ
         """
       
        zpl_code = zpl_template.format(
            result=result,
            weight_lb=weight_lb,
            weight_kg=weight_kg,
            lbs_wheels=lbs_wheels,
            rin=rin,
            tire_rating=tire_rating,
            product_vin=product_vin,
            gvwr_kg=gvwr_kg,
            gvwr_lb=gvwr_lb,
            gawr_kg=gawr_kg,
            gawr_lb=gawr_libras,
            model_string=model_string
        )
        
        # Función para enviar ZPL a la impresora
        def send_zpl_to_printer(printer_ip, zpl_code):
            try:
                print(f"Conectando a la impresora en {printer_ip}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # Timeout de 10 segundos para la conexión
                sock.connect((printer_ip, self.printer_port))
                sock.sendall(zpl_code.encode())  # Enviar el código ZPL
                sock.close()
                return True
            except Exception as e:
                print(f"Error al enviar ZPL a {printer_ip}: {e}")
                return False
        
        # Enviar a todas las impresoras seleccionadas
        success = False
        for printer in self.printer_ids:
            # Obtener la dirección IP del dispositivo IoT
            # Asumiendo que la IP está en el campo 'device_identifier' o similar
            printer_ip = None
            
            # Primero intentamos con device_identifier que es común en iot.device
            if hasattr(printer, 'device_identifier'):
                printer_ip = printer.device_identifier
            # Si no, buscamos en los campos del dispositivo
            elif hasattr(printer, 'ip'):
                printer_ip = printer.ip
            # Si sigue sin encontrarse, buscamos en la conexión asociada
            elif hasattr(printer, 'connection') and printer.connection and hasattr(printer.connection, 'host'):
                printer_ip = printer.connection.host
            
            if printer_ip:
                if send_zpl_to_printer(printer_ip, zpl_code):
                    success = True
                    print(f"Código ZPL enviado correctamente a la impresora {printer.name} ({printer_ip})")
                else:
                    print(f"Fallo al enviar a la impresora {printer.name} ({printer_ip})")
            else:
                print(f"La impresora {printer.name} no tiene dirección IP configurada")
                # Si sabemos que la IP es 192.168.60.25 pero no está en el modelo
                # Podemos forzarla (esto es temporal hasta corregir el modelo)
                printer_ip = '192.168.60.25'
                if send_zpl_to_printer(printer_ip, zpl_code):
                    success = True
                    print(f"Código ZPL enviado correctamente a la impresora {printer.name} (IP forzada: {printer_ip})")
        
        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Éxito',
                    'message': 'La etiqueta se ha enviado correctamente a la(s) impresora(s)',
                    'sticky': False,
                    'type': 'success'
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Hubo un error al intentar enviar la etiqueta a todas las impresoras seleccionadas.',
                    'sticky': False,
                    'type': 'error'
                }
            }
           
        
