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
    pdf_file = fields.Binary(string='PDF File', attachment=True)
    pdf_filename = fields.Char(string='PDF Filename', compute='_compute_pdf_filename')
    printer_config_id = fields.Many2one(
    'printer.conf', 
    string='Configuración de Impresora',
    domain="[('active', '=', True)]"
    )
    @api.depends('name')
    def _compute_pdf_filename(self):
        for record in self:
            record.pdf_filename = f"vin_label_{record.name or 'unknown'}.pdf"
    def get_data(self):
        """Obtiene el VIN del modelo HS7 seleccionado"""
        if not self.model_hs7:
            raise UserError("No se ha seleccionado un modelo HS7")
        # Verificamos que exista un VIN y que no esté vacío
        if not self.model_hs7.vin_dispayed:
            raise UserError("El modelo HS7 seleccionado no tiene un VIN asignado")
        return self.model_hs7.vin_dispayed

    def _get_tire_specs(self, product):
        """Obtiene especificaciones de llantas con extracción mejorada del RIN"""
        specs = {
            'tire_rating': "",
            'lbs_wheels': "",
            'rin': "",
            'num_rin': "",
            'wheel_names': [],
            'wheels_count': {},
            'ply_pr': "",
            'tire_description': ""
        }

        if product.bom_ids:
            bom_lines = product.bom_ids[0].bom_line_ids
            for bom_line in bom_lines:
                bom_product = bom_line
                bom_product_name = bom_product.display_name.upper()

                if 'LLANTA' in bom_product_name:
                    # Contar llantas por producto
                    specs['wheels_count'][bom_product.id] = specs['wheels_count'].get(bom_product.id, 0) + bom_line.product_qty
                    specs['wheel_names'].append(bom_product_name)
                    specs['tire_description'] = bom_product_name

                    # Extracción del RIN
                    parts = [p for p in bom_product_name.split() if p.strip()]
                    if len(parts) >= 2:
                        # Buscamos el RIN en el segundo elemento 
                        potential_rin = parts[1]

                        # Validamos formatos comunes de RIN
                        rin_pattern = r'^(R\d{2}(\.5)?)$' 
                        if re.match(rin_pattern, potential_rin):
                            specs['num_rin'] = potential_rin  # También asignamos el valor al num_rin

                    # Extraer y validar PLY/PR
                    ply_match = re.search(r'(\d+PLY|\d+PR)', bom_product_name)
                    if ply_match:
                        specs['ply_pr'] = ply_match.group(1)
                        # Validar que sea un valor conocido
                        valid_ply_pr = ['6PLY', '6PR', '8PLY', '8PR', '10PLY', '10PR', 
                                       '14PLY', '14PR', '18PLY', '18PR']
                        if specs['ply_pr'] not in valid_ply_pr:
                            specs['ply_pr'] = ""

        return specs



    def _get_tire_ratings(self, tire_type, rin, ply_pr):
        """Devuelve (rating_data, lbs_wheels) usando condicionales explícitos"""
        if not ply_pr or not rin:
            return ("", "")

        # Normalización de valores
        tire_type = (tire_type or '').strip().upper()
        rin = rin.strip().upper()
        ply_pr = ply_pr.strip().upper()

        # Primero verificamos el tipo de llanta (DUAL, SS o estándar)
        if tire_type == 'DUAL':
            if rin == 'R17.5':
                if ply_pr == '18PLY' or ply_pr == '18PR':
                    return ('862 KPA/125 PSI', '5675 LBS')
                elif ply_pr == '14PLY' or ply_pr == '14PR':
                    return ('758 KPA/110 PSI', '4400 LBS')
            elif rin == 'R16':
                if ply_pr == '14PLY' or ply_pr == '14PR':
                    return ('758 KPA/110 PSI', '3860 LBS')
                elif ply_pr == '10PLY' or ply_pr == '10PR':
                    return ('550 KPA/80 PSI', '3080 LBS')
                elif ply_pr == '8PLY' or ply_pr == '8PR':
                    return ('448 KPA/65 PSI', '2150 LBS')

        elif tire_type == 'SS':
            if rin == 'R17.5':
                if ply_pr == '18PLY' or ply_pr == '18PR':
                    return ('862 KPA/125 PSI', '6005 LBS')
                elif ply_pr == '14PLY' or ply_pr == '14PR':
                    return ('758 KPA/110 PSI', '4400 LBS')
            elif rin == 'R16':
                if ply_pr == '14PLY' or ply_pr == '14PR':
                    return ('758 KPA/110 PSI', '3860 LBS')

        # Para cualquier otro caso (tipo vacío o no reconocido)
        else:
            if rin == 'R15':
                if ply_pr == '10PLY' or ply_pr == '10PR':
                    return ('550 KPA/80 PSI', '3520 LBS')
                elif ply_pr == '8PLY' or ply_pr == '8PR':
                    return ('448 KPA/65 PSI', '2150 LBS')
                elif ply_pr == '6PLY' or ply_pr == '6PR':
                    return ('334 KPA/50 PSI', '1820 LBS')
            elif rin == 'R16':
                if ply_pr == '10PLY' or ply_pr == '10PR':
                    return ('550 KPA/80 PSI', '2830 LBS')
                elif ply_pr == '14PLY' or ply_pr == '14PR':
                    return ('758 KPA/110 PSI', '4400 LBS')
            elif rin == 'R17.5':
                if ply_pr == '14PLY' or ply_pr == '14PR':
                    return ('758 KPA/110 PSI', '4400 LBS')
                elif ply_pr == '10PLY' or ply_pr == '10PR':
                    return ('550 KPA/80 PSI', '2830 LBS')

        # Si no se encuentra ninguna coincidencia
        return ("", "")

    def generate_pdf(self):
        """Genera un PDF con la información de la etiqueta VIN"""
        if not self.model_hs7:
            raise UserError("No se ha seleccionado un registro en 'HS7'")
            
        product = self.model_hs7.product_id
        
        # Obtener GVWR
        gvwr = self.model_hs7.product_id.gvwr_child or self.model_hs7.product_id.gvwr_related
        if not gvwr:
            raise UserError("No se ha seleccionado un registro para 'GVWR'")
        
        # Obtener GAWR
        gawr = self.model_hs7.product_id.gawr_related
        if not gawr:
            raise UserError("No se ha seleccionado un registro para 'GAWR'")
        
        # Calcular pesos
        gvwr_lb = gvwr.weight_lb
        gvwr_kg = gvwr.weight_kg
        gawr_lb = int(gawr.name[5:8]) if gawr.name and len(gawr.name) >= 8 else 0
        gawr_kg = int(round(gawr_lb * 0.453592, 2))
        weight_lb = self.model_hs7.product_id.dry_weight or 0
        carga_maxima_lb = max(weight_lb - gvwr_lb, 0)
        weight_kg = int(round(carga_maxima_lb * 0.453592))
        
        # Obtener información del producto
        product_name = self.model_hs7.product_id.default_code or ""
        model_string = product_name.split(" ")[0].replace('[','').replace(']','') if product_name else ""
        product_vin = self.get_data()
        current_date = datetime.now().strftime('%m/%d/%Y')
        serial_number = self.model_hs7.name or ""
        
        # Obtener especificaciones de llantas
        tire_specs = self._get_tire_specs(product)
        
        # Obtener ratings de llantas
        rating_data, lbs_wheels = self._get_tire_ratings(
            product.tire_typ,
            tire_specs['rin'],
            tire_specs['ply_pr']
        )
        
        # Actualizar specs con los valores obtenidos
        tire_specs['tire_rating'] = lbs_wheels
        tire_specs['lbs_wheels'] = lbs_wheels
        
        # Generar PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Configurar fuente
        c.setFont("Helvetica", 10)
        y_position = height - 20 * mm
        
        # Contenido completo del PDF con todos los datos
        sections = [
            (f"The weight of the cargo should never exceed {weight_kg} kg or {carga_maxima_lb} lbs", 5),
            (f"Le poids du chargement ne doit jamais dépasser {weight_kg} kg ou {carga_maxima_lb} lb", 5),
            ("", 2),
            (f"{tire_specs['rin']}", 5),
            (f"{rating_data}", 5),
            (f"{tire_specs['rin']}", 5),
            (f"{rating_data}", 5),
            (f"{tire_specs['rin']}", 5),
            (f"{rating_data}", 5),
            (f"{product_vin}", 5),
            ("MANUFACTURED BY/FABRIQUE PAR: HORIZON TRAILERS MEXICO S. DE R.L. DE C.V.", 5),
            (f"GVWR / PNBV {gvwr_kg} KG ({gvwr_lb} LB)", 5),
            (f"DATE: {current_date}", 5),
            (f"GAWR (EACH AXLE) / PNBE (CHAQUE ESSIEU) {gawr_kg} KG ({gawr_lb} LBS)", 5),
            (f"TIRE/PNEU {tire_specs['rin']} RIM/JANTE {tire_specs['num_rin']} {tire_specs['tire_rating']}", 5),
            (f"COLD INFL. PRESS/PRESS. DE GONFL. À FROID {rating_data}/LCP SINGLE", 5),
            ("THIS VEHICLE TO ALL APPLICABLE U.S. FEDERAL MOTOR SAFETY STANDARDS", 5),
            ("IN EFFECT ON THE DATE OF MANUFACTURE SHOWN ABOVE.", 5),
            ("THIS VEHICLE CONFORMS TO ALL APPLICABLE STANDARDS PRESCRIBED UNDER CANADA.", 5),
            ("CE VÉHICULE EST CONFORME À TOUTES LES NORMES EN VIGUEUR À LA DATE DE SA FABRICATION.", 5),
            ("SUR LA SÉCURITÉ DES VÉHICULES AUTOMOBILES DU CANADA EN VIGUEUR À LA DATE DE SA FABRICATION.", 5),
            (f"VIN: {product_vin}", 5),
            ("TYPE: TRA/REM", 5),
            (f"MODEL: {model_string}", 5),
        ]
        
        # Dibujar todas las secciones
        for text, space in sections:
            if text.strip():
                c.drawString(20 * mm, y_position, text)
            y_position -= space * mm
        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        return base64.b64encode(pdf_data)
    
    def print_vins(self):
        
        """Acción principal para generar PDF, enviar JSON a la API e imprimir"""
        pdf_data = self.generate_pdf()
        self.write({'pdf_file': pdf_data})
        #Prepara los datos para la impresion
        print_data = self._prepare_api_data() 
        #Enviar a la impresora vía API
        self._send_to_printer_api(print_data)  
        # Mantener la descarga del PDF 
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/print.vins/{self.id}/pdf_file/{self.pdf_filename}?download=true',
            'target': 'self',
        }

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
        # Obtener especificaciones de llantas y validar los datos
        tire_specs = self._get_tire_specs(product)


        # Validar que tengamos un RIN válido
        if not tire_specs.get('num_rin'):
            raise UserError("No se pudo determinar el RIN de las llantas")

        # Obtener ratings con los valores validados
        rating_data, lbs_wheels = self._get_tire_ratings(
            product.tire_typ,
            tire_specs['num_rin'],
            tire_specs.get('ply_pr', '')
        )

        # Diccionario JSON con todos los datos validados
        api_data = {
            "ip": printer_config.printer_ip,
            "port": printer_config.printer_port,
            "tire_type": product.tire_typ or "",
            "weight_lb": carga_maxima_lb,
            "weight_kg": weight_kg,
            "lbs_wheels": lbs_wheels or "",
            "rim": tire_specs.get('num_rin', ""), 
            "tire_rating": rating_data or "",
            "product_vin": product_vin,
            "gvwr_kg": gvwr_kg,
            "gvwr_lb": gvwr_lb,
            "gawr_kg": gawr_kg,
            "gawr_lb": gawr_lb,
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
                printer.printer_api_url,
                json=data,
                headers={
                    "Authorization": f"Bearer {printer.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            if response.status_code != 200:
                raise UserError(f"Error al imprimir: {response.text}")
            
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con la impresora: {str(e)}")
        

   
              
