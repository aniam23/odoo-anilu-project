from odoo import api, models, fields
import time

class MSOreport(models.AbstractModel):
    _name = 'report.logistics_document_packages.report_all_mso_template'
    _description = 'Print report MSO'

    def _get_report_values(self, docids, data=None):
        
        return {
           
            'data': data,
        }

