from odoo import models, fields, api

class scrap_percentage(models.Model):
    _inherit = 'mrp.bom'

    decimal_scrap= fields.Float()
    percentage_scrap= fields.Float(string="Percentage Of Scrap")
    
    weight_scrap= fields.Float(string="Weight Of Scrap")

    def compute_decimal_scrap(self):
        for record in self:
            record.decimal_scrap = record.percentage_scrap
            
    def calculate_total_scrap(self):
        for record in self: 
            if len(record.bom_line_ids) > 0:
                record.compute_decimal_scrap()
                product_weight = record.bom_line_ids[0].product_id.total_weight
                self.weight_scrap= product_weight * record.decimal_scrap
    
