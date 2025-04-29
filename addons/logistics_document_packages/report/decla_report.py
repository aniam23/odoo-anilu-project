from odoo import api, models, fields
import time

class DeclaReport(models.AbstractModel):
    _name = 'report.logistics_document_packages.report_decla_template'
    _description = 'Print Declaracion'
    def _get_report_values(self, docids, data=None , auto_data=None):
        sale_order = self.env['sale.order'].search([('id', '=', data.get('sale_order_id'))], limit=1)
        if not sale_order:
            return {'error': 'Sale order not found'}
        fecha_hoy = time.localtime()
        fecha_formateada = time.strftime('%d-%m-%Y')
        # trailers_hs7_list = []  
        # for line in sale_order.order_line:
        #     product = line.product_id
        #     model_info = self.env['model.hs7'].search([('ref_trailer', '=', product.id)], limit=1)
        #     if model_info:
        #         trailers_hs7_list.append(model_info.model)  
        # if trailers_hs7_list:
        auto_data = {
                'date2': fecha_formateada,
                'id': sale_order.id,
            }
            # for trailer in trailers_hs7_list:
            #     print(trailer)  
       
        return {
            'auto_data': auto_data,
            'doc_model': 'logistics.log_document',
            'data': data,
        }

 

    
    
        
        
        
        
       
    

        
    
        
       
        