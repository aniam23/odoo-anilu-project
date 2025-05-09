from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import requests
import re

class ManualPrint(models.Model):
    _name = 'print.manual'
    _description = 'Impresión manual de datos de remolques'
    
    # Campos del modelo
    name = fields.Char(string='Referencia')
    name_trailer = fields.Char(string='Nombre del Remolque')
    model_trailer = fields.Char(string="Modelo del Remolque")
    wheel = fields.Char(string="Llanta")
    dry_weight = fields.Float(string="Peso Total (LBS)")
    gvwr_related = fields.Char(string="GVWR")
    gawr_related = fields.Char(string="GAWR")
    tire_typ = fields.Char(string="Tipo de Llanta")
    model_year = fields.Char(string="Año")
    axles = fields.Char(string="Ejes")
    tongue_type = fields.Char(string="Tipo de ")
    length = fields.Char(string="Longitud")
    rin_jante = fields.Char(string="Rin/Jante")
    vin_registry = fields.Many2one('vin_generator.vin_generator', string='VIN')
    date = fields.Date(string='Fecha', default=fields.Date.today)
    printer_config_id = fields.Many2one(
        'printer.conf', 
        string='Configuración de Impresora',
        domain="[('active', '=', True)]"
    )
   
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('manual.print.reference') or 'New'
        return super(ManualPrint, self).create(vals_list)

    def extract_numeric_value(self, value):
        """Extrae el valor numérico de una cadena y la devuelve como float"""
        if not value:
            return 0.0
        numbers = re.findall(r'[\d,\.]+', str(value))
        if not numbers:
            return 0.0
        numeric_value = numbers[0].replace(',', '')
        return float(numeric_value)

    def button_assign_trailer_data(self):
        """Asigna todos los datos del remolque desde product.template"""
        for record in self:
            if not record.model_trailer:
                continue
                
            product = self.env['product.product'].search([
                ('default_code', '=', record.model_trailer)
            ], limit=1)
            
            if product:
                template = product.product_tmpl_id
                record.update({
                    'name_trailer': product.name,
                    'dry_weight': template.dry_weight or 0.0,
                    'gvwr_related': template.gvwr_related.name or '',
                    'gawr_related': template.gawr_related.name or '',
                    'tire_typ': template.tire_typ or '',
                    'model_year': template.model_year or '',
                    'axles': template.axles or '',
                    'tongue_type': template.tongue_type or '',
                    'length': template.length or '',
                })
                
                bom = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', template.id)
                ], limit=1)
                
                if bom:
                    wheels = bom.bom_line_ids.filtered(
                        lambda l: 'llanta' in l.product_id.name.lower()
                    )
                    record.wheel = wheels[0].product_id.name if wheels else ''

    def _get_active_printer(self):
        return self.env['printer.conf'].search([('active', '=', True)], order='sequence', limit=1)

    def _send_to_printer_api(self, data):
        """Envía los datos a la impresora mediante API"""
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
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con la impresora: {str(e)}")

    def _set_tire_ratings(self, specs):
        """Asigna las especificaciones técnicas basadas en la llanta (campo wheel)"""
        if not self.wheel:
            return
        wheel_info = self.wheel.upper()
        rin_match = re.search(r'(?:15|16|17\.5)', wheel_info)
        if not rin_match:
            return  # No se detectó RIN
        rin = rin_match.group()
        # Extraer tipo de llanta (DUAL o SS)
        tire_type = 'DUAL' if re.search(r'\bDUAL\b', wheel_info) else 'SS' if re.search(r'\bSS\b', wheel_info) else ''

        #  Extraer PLY/PR (10PLY, 14PR, etc.)
        ply_match = re.search(r'(\d+PLY|\d+PR)', wheel_info)
        ply_pr = ply_match.group() if ply_match else None

        # Mapa de especificaciones actualizado
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
                },
                '': {  
                    '10PLY': ('550 KPA/80 PSI', '3520 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3520 LBS')
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
                '': {  # Default para 16 sin tipo específico
                    '14PLY': ('758 KPA/110 PSI', '3860 LBS'),
                    '14PR': ('758 KPA/110 PSI', '3860 LBS')
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

        # Asignar valores solo si tenemos todos los datos necesarios
        if rin :
            type_group = ratings_map[rin].get(tire_type, ratings_map[rin].get('', {}))
            if ply_pr in type_group:
                specs['tire_rating'], specs['lbs_wheels'] = type_group[ply_pr]
        #rim_jante
        specs['rim_jante'] = self.rin_jante or ''
        if rin in ratings_map:
            type_group = ratings_map[rin].get(tire_type)
        

      

    def _prepare_api_data(self, weight_kg=None):
        """Prepara los datos para enviar a la API de impresión"""
        printer = self._get_active_printer()
        if not printer:
            raise UserError("No hay impresoras activas configuradas")
        if not self.vin_registry:
            raise UserError("No se ha asignado un VIN")
            
        # Inicializar especificaciones de llantas
        tire_specs = {
            'tire_rating': '',
            'lbs_wheels': '',
            'rin': '',
            'rim_jante': ''
        }
        
        self._set_tire_ratings(tire_specs)
        
        # Calcular pesos
        weight_lb = self.dry_weight or 0
        if weight_kg is None:
            weight_kg = int(weight_lb * 0.453592)
        
        # Extraer valores numéricos
        gvwr_lb = self.extract_numeric_value(self.gvwr_related)
        gvwr_kg = int(gvwr_lb * 0.453592)
        gawr_lb = self.extract_numeric_value(self.gawr_related)
        gawr_kg = int(gawr_lb * 0.453592)

        return {
            "ip": printer.printer_ip,
            "port": printer.printer_port,
            "weight_lb": weight_lb,
            "weight_kg": weight_kg,
            "lbs_wheels": tire_specs['lbs_wheels'],
            "rim": tire_specs['rin'],
            "tire_rating": tire_specs['tire_rating'],
            "product_vin": self.vin_registry.vin,
            "gvwr_kg": gvwr_kg,
            "gvwr_lb": gvwr_lb,
            "gawr_kg": gawr_kg,
            "gawr_lb": gawr_lb,
            "rim_jante": tire_specs['rim_jante'],
            "model_string": self.model_trailer or "",
            "fecha_impresion": self.date.strftime('%m/%Y') if self.date else datetime.now().strftime('%m/%Y'),
            "auth_token": printer.auth_token or ''
        }

    def print_manual_vins(self):
        """Acción principal para imprimir etiquetas manuales"""
        self.ensure_one()
        print_data = self._prepare_api_data()
        self._send_to_printer_api(print_data)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'La etiqueta se ha enviado a la impresora',
                'type': 'success',
                'sticky': False,
            }
        }
