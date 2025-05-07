from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo import models, fields, api

class PrinterConfig(models.Model):
    _name = 'printer.conf'
    _description = 'Configuración de Impresora'
    _order = 'sequence, id'  # Ordenar por secuencia
    
    name = fields.Char(string='Nombre', required=True)
    printer_ip = fields.Char(string='IP de la Impresora', required=True)
    printer_port = fields.Integer(string='Puerto', default=6000)
    auth_token = fields.Char(string='Token de Autorización', default='123')
    active = fields.Boolean(string='Activo', default=True)
    sequence = fields.Integer(string='Prioridad', default=10)
    printer_api_url = fields.Char(
        string='URL de la API', 
        compute='_compute_api_url',
        store=True
    )
    
    @api.depends('printer_ip', 'printer_port')
    def _compute_api_url(self):
        for record in self:
            record.printer_api_url = f"http://{record.printer_ip}:{record.printer_port}/print"

    