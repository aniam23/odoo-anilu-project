from odoo import api, models, fields

class TitleReport(models.AbstractModel):
    _name = 'report.vin_generator.title_print_template'
    _description= 'title print'

   

    def _get_report_values(self, docids, data=None):
        return{
            'doc_model': 'account.move',
            'id':data['id'],
            'full_data': data['full_data'],
        }