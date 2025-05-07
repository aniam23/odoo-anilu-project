from odoo import api, models, fields
import time
class Hs7Report(models.AbstractModel):
    _name = 'report.logistics_document_packages.report_hs7_template'
    _description = 'Print report HS7'


    def _get_report_values(self, docids, data=None):
       
        sale_order = self.env['sale.order'].search([('id', '=' ,data['sale_order_id'])],limit=100)
       
        invoice = sale_order.invoice_ids
        
        fecha_hoy = time.localtime()
        fecha_formateada = time.strftime('%Y-%m-%d', fecha_hoy)
        print( fecha_formateada)
        
        auto_data = {
        'date2': fecha_formateada,
        'invoice_number1': invoice.display_name,  
        
         }

        return {
            'auto_data': auto_data,
        }
