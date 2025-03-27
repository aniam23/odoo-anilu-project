from odoo import api, models, fields

class FacturaReport(models.AbstractModel):

    _name = 'report.logistics_document_packages.report_factura_template'
    _description = 'Print Invoice'

    def _get_report_values(self, docids, data=None):
        print(data)
        sale_order = self.env['sale.order'].browse(data['sale_order_id'])
        print(sale_order)
        
        invoice = data['invoice']

        print(invoice)
    
       
        return {
            
            'data': data,
        }

