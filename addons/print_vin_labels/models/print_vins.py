from odoo import models, fields, api
from odoo.exceptions import UserError
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import base64
import requests
import re

class PrintVins(models.Model):
    _name = 'print.vins'
    _description = 'Print VIN Labels'
    # Campos del modelo
    name = fields.Char(string='Name')
    sale_order = fields.Many2one('sale.order', string='Sales Order')
    model_hs7 = fields.Many2many('mrp.production', string='MODEL HS7')
    gvwr = fields.Many2many('vin_generator.gvwr_manager', string='GVWR Related')
    gawr = fields.Many2many('print.gawr', string='GAWR')
    gawr_lb = fields.Float(string='GAWR lb')
    printer_port = fields.Integer(string='Printer Port', default=9100)
    weight_total = fields.Float(string='Total Weight')
    product_name = fields.Char(string='Product Name')
    printer_config_id = fields.Many2one(
        'printer.conf', 
        string='Configuración de Impresora',
        domain="[('active', '=', True)]"
    )
    
    def get_data(self):
        """Obtiene el VIN del modelo HS7 seleccionado"""
        if not self.model_hs7:
            raise UserError("No se ha seleccionado un modelo HS7")
        if not self.model_hs7.vin_dispayed:
            raise UserError("El modelo HS7 seleccionado no tiene un VIN asignado")
        return self.model_hs7.vin_dispayed


    def _get_tire_specs(self, product):
        """Obtiene especificaciones de llantas"""
        specs = {
            'tire_rating': "",
            'lbs_wheels': "",
            'rin': "",
            'wheel_names': [],
            'wheels_count': {},
            'ply_pr': "",
            'rim_jante':"",
            'tire_description': ""
        }
        #si no encuentra las especificaciones de llantas en el producto
        if not product or not product.bom_ids:
            return specs
        try:
            bom = product.bom_ids[0]
            for bom_line in bom.bom_line_ids:
                if not bom_line.product_id:
                    continue

                product_name = bom_line.product_id.display_name
                if not product_name:
                    continue

                clean_name = product_name.upper()
                if 'LLANTA' in clean_name:
                    parts = [p.strip() for p in clean_name.split() if p.strip()]
                    if len(parts) >= 2:
                        specs['rin'] = parts[1]  # ST225/75R15
                        specs['wheel_names'].append(clean_name)
                        specs['wheels_count'][bom_line.product_id.id] = bom_line.product_qty
                        specs['tire_description'] = clean_name
    
                        # Extracción precisa de rim_jante 
                        rim_jante_parts = []
                        if len(parts) > 8:  # Aseguramos que existan las partes 8,9,10
                            if "''" in parts[8] and 'X' in parts[9] and "''" in parts[10]:
                                rim_jante_parts = parts[8:11]  # Toma partes 8, 9 y 10
    
                        specs['rim_jante'] = ' '.join(rim_jante_parts) if rim_jante_parts else parts[1]
    
                        if len(parts) >= 3:
                            ply_match = re.search(r'(\d+PLY|\d+PR)', parts[2])
                            if ply_match:
                                specs['ply_pr'] = ply_match.group(1)
    
                        self._set_tire_ratings(specs, clean_name, parts[1])
                    break

        except Exception as e:
            raise UserError(f"Error al procesar especificaciones de llanta: {str(e)}")

        return specs

    

    def _set_tire_ratings(self, specs, product_name, rin):
        """Asigna las especificaciones técnicas basadas en el tipo de llanta y RIN detectado desde el nombre"""

        product_name = product_name.upper()

        # Detectar el RIN 
        rin_match = re.search(r'(?:15|16|17\.5)', product_name)
        if not rin_match:
            return  # No se detectó RIN
        rin = rin_match.group()

        # Detectar tipo de llanta con palabras completas
        if re.search(r'\bDUAL\b', product_name):
            tire_type = 'DUAL'
        elif re.search(r'\bSS\b', product_name):
            tire_type = 'SS'
        else:
            tire_type = ''

        # Detectar PLY o PR
        ply_match = re.search(r'(\d+PLY|\d+PR)', product_name)
        if not ply_match:
            return  # No se encontró PLY/PR
        ply_pr = ply_match.group()

        # Mapa de especificaciones
        ratings_map = {
            '17.5': {
                'DUAL': {
                    '18PLY': ('862 KPA/125 PSI', '5675 LBS'),
                    '18PR': ('862 KPA/125 PSI', '5675 LBS'),
                    '14PLY': ('758 KPA/110 PSI', '4400 LBS'),
                    '14PR': ('758 KPA/110 PSI', '4400 LBS'),
                    '10PLY': ('550 KPA/80 PSI', '3520 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3520 LBS')
                },
                'SS': {
                    '18PLY': ('862 KPA/125 PSI', '6005 LBS'),
                    '18PR': ('862 KPA/125 PSI', '6005 LBS'),
                    '14PLY': ('758 KPA/110 PSI', '4400 LBS'),
                    '14PR': ('758 KPA/110 PSI', '4400 LBS')
                }
            },
            '16': {
                'DUAL': {
                    '14PLY': ('758 KPA/110 PSI', '3860 LBS'),
                    '14PR': ('758 KPA/110 PSI', '3860 LBS'),
                    '10PLY': ('550 KPA/80 PSI', '3080 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3080 LBS')
                },
                'SS': {
                    '14PLY': ('758 KPA/110 PSI', '3860 LBS'),
                    '14PR': ('758 KPA/110 PSI', '3860 LBS')
                },
                '': {
                    '10PLY': ('550 KPA/80 PSI', '3520 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3520 LBS'),
                    '14PLY': ('758 KPA/110 PSI', '4400 LBS'),
                    '14PR': ('758 KPA/110 PSI', '4400 LBS')
                }
            },
            '15': {
                '': {
                    '10PLY': ('550 KPA/80 PSI', '2830 LBS'),
                    '10PR': ('550 KPA/80 PSI', '2830 LBS'),
                    '8PLY': ('448 KPA/65 PSI', '2150 LBS'),
                    '8PR': ('448 KPA/65 PSI', '2150 LBS'),
                    '6PLY': ('334 KPA/50 PSI', '1820 LBS'),
                    '6PR': ('334 KPA/50 PSI', '1820 LBS')
                }
            }
        }

        if rin in ratings_map:
            type_group = ratings_map[rin].get(tire_type)
            if type_group and ply_pr in type_group:
                specs['tire_rating'], specs['lbs_wheels'] = type_group[ply_pr]

   

    def _prepare_api_data(self):
        printer_config = self.env['printer.conf'].search([('active', '=', True)], limit=1)
        """Prepara los datos para la API buscando automáticamente la impresora"""
        if not printer_config:
            raise UserError("No hay impresoras configuradas como activas en el sistema")
        if not self.model_hs7:
            raise UserError("No se ha seleccionado un modelo HS7")
    
        product = self.model_hs7.product_id
        gvwr = product.gvwr_child or product.gvwr_related
        gawr = product.gawr_related
        if not gvwr or not gawr:
            raise UserError("Faltan datos de GVWR o GAWR")
    
        # Obtener especificaciones de llantas
        tire_specs = self._get_tire_specs(product)
    
        # Cálculo de pesos
        gvwr_lb = gvwr.weight_lb
        gvwr_kg = gvwr.weight_kg
        gawr_lb = int(gawr.name[5:8]) if gawr.name and len(gawr.name) >= 8 else 0
        gawr_kg = int(round(gawr_lb * 0.453592, 2))
        weight_lb = product.dry_weight or 0
        carga_maxima_lb = max(weight_lb - gvwr_lb, 0)
        weight_kg = int(round(carga_maxima_lb * 0.453592))
        
        # Datos del producto
        product_name = product.default_code or ""
        model_string = product_name.split(" ")[0].replace('[','').replace(']','') if product_name else ""
        product_vin = self.get_data()
        #Obtener fecha
        fecha_impresion = (
        self.sale_order.fechapro.strftime('%m/%Y') 
        if self.sale_order and hasattr(self.sale_order, 'fechapro') and self.sale_order.fechapro
        else datetime.now().strftime('%m/%Y')
)
        # Diccionario JSON con todos los datos validados
        api_data = {
            "ip": printer_config.printer_ip,
            "port": printer_config.printer_port,
            "weight_lb": carga_maxima_lb,
            "weight_kg": weight_kg,
            "lbs_wheels": tire_specs.get('lbs_wheels', ""),
            "rim": tire_specs.get('rin', ""),
            "tire_rating": tire_specs.get('tire_rating', ""),
            "product_vin": product_vin,
            "gvwr_kg": gvwr_kg,
            "fecha_impresion": fecha_impresion,
            "gvwr_lb": gvwr_lb,
            "gawr_kg": gawr_kg,
            "gawr_lb": gawr_lb,
            "rim_jante": tire_specs.get('rim_jante', ""),
            "model_string": model_string,
        }
        return api_data

    def _get_active_printer(self):
        return self.env['printer.conf'].search([('active', '=', True)], order='sequence', limit=1)

    def _send_to_printer_api(self, data):
        printer = self._get_active_printer()
        if not printer:
            raise UserError("No hay impresoras activas configuradas")
        
        try:
            response = requests.post(
                f"http://{printer.printer_ip}:{printer.printer_port}/print",
                json=data,
                headers={
                    "Authorization": f"Bearer {printer.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=1000
            )
            
            if response.status_code != 200:
                raise UserError(f"Error al imprimir: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con la impresora: {str(e)}")

    def print_vins(self):
        """Acción principal para generar e imprimir etiquetas VIN"""
        print_data = self._prepare_api_data()
        self._send_to_printer_api(print_data)
        
       

    

   
              
