from odoo import models,fields,api

class weight_calculation(models.Model):
    _inherit = 'product.template'

    total_weight= fields.Float(string="Total Weight (KG)", default=0.0)
    total_scrap= fields.Float(string="Total Scrap", default=0.0)

    piece_scrap_weight = fields.Float(compute="piece_scrap_weight_calculation")
    piece_weight= fields.Float(compute="piece_scrap_weight_calculation")

    has_more_than_one_bom = fields.Boolean(compute="calulate_num_of_boms")
    @api.depends("bom_ids")
    def calulate_num_of_boms(self):
        for product in self:
            num_of_boms = self.env['mrp.bom'].sudo().search_count(['|', ('product_tmpl_id', '=', product.id), ('byproduct_ids.product_id.product_tmpl_id', '=', product.id)])
        if num_of_boms >= 1:
            self.has_more_than_one_bom = True
        else:
            self.has_more_than_one_bom = False
    def calculate_weight(self):
        for product in self:
            num_of_boms = self.env['mrp.bom'].sudo().search_count(['|', ('product_tmpl_id', '=', product.id), ('byproduct_ids.product_id.product_tmpl_id', '=', product.id)])

        if num_of_boms == 1:
            if len(self.bom_ids[0].bom_line_ids)>1:
                self.total_weight = 0
                for bom_line in self.bom_ids[0].bom_line_ids:
                    bom_line.product_id.calculate_weight()
                    self.total_weight = self.total_weight + (bom_line.product_id.total_weight* bom_line.product_qty)
                self.total_weight = self.total_weight/ self.bom_ids[0].product_qty
            elif len(self.bom_ids[0].bom_line_ids) == 1: 
                self.piece_scrap_weight_calculation()
            else:
                self.env['bus.bus']._sendone(self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": "Custom Notification",
                        "message": "No bom lines.",
                        "sticky": True
                    })         
        else:
            self.env['bus.bus']._sendone(self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": "Custom Notification",
                        "message": "Too may BOM's.",
                        "sticky": True
                    })

    def piece_scrap_weight_calculation(self):
        for record in self:
            record.bom_ids[0].calculate_total_scrap()
            record.piece_scrap_weight = record.bom_ids[0].weight_scrap/ record.bom_ids[0].product_qty
            record.piece_weight= (record.bom_ids[0].bom_line_ids[0].product_id.total_weight/record.bom_ids[0].product_qty)-record.piece_scrap_weight
            record.total_weight = record.piece_weight  

    def compute_final_priece(self):
        for product in self:
            num_of_boms = self.env['mrp.bom'].sudo().search_count(['|', ('product_tmpl_id', '=', product.id), ('byproduct_ids.product_id.product_tmpl_id', '=', product.id)])
        if num_of_boms == 1:
            self.standard_price = 0
            for bom_line in self.bom_ids[0].bom_line_ids:
                bom_line.product_id.compute_final_priece()
                self.standard_price = self.standard_price + (bom_line.product_id.standard_price * bom_line.product_qty)   

class weight_calculation(models.Model):
    _inherit = 'product.product'

    has_more_than_one_bom = fields.Boolean(compute="calulate_num_of_boms")
    @api.depends("bom_ids")
    def calulate_num_of_boms(self):
        for product in self:
            num_of_boms = self.env['mrp.bom'].sudo().search_count(['|', ('product_tmpl_id', '=', product.id), ('byproduct_ids.product_id.product_tmpl_id', '=', product.id)])
        if num_of_boms >= 1:            
            self.has_more_than_one_bom = True
        else:
            self.has_more_than_one_bom = False
    
    def calculate_weight(self):
        for product in self:
            num_of_boms = self.env['mrp.bom'].sudo().search_count(['|', ('product_tmpl_id', '=', product.id), ('byproduct_ids.product_id.product_tmpl_id', '=', product.id)])

        if num_of_boms == 1:
            self.total_weight = 0
            if len(self.bom_ids[0].bom_line_ids)>1:
                for bom_line in self.bom_ids[0].bom_line_ids:
                    bom_line.product_id.calculate_weight()
                    self.total_weight = self.total_weight + (bom_line.product_id.total_weight* bom_line.product_qty)
                self.total_weight = self.total_weight/ self.bom_ids[0].product_qty
            elif len(self.bom_ids[0].bom_line_ids) == 1: 
                self.bom_ids[0].calculate_total_scrap()
                self.piece_scrap_weight_calculation()

    def piece_scrap_weight_calculation(self):
        for record in self:
            record.bom_ids[0].calculate_total_scrap()
            record.piece_scrap_weight = record.bom_ids[0].weight_scrap/ record.bom_ids[0].product_qty
            record.piece_weight= (record.bom_ids[0].bom_line_ids[0].product_id.total_weight/record.bom_ids[0].product_qty)-record.piece_scrap_weight
            record.total_weight = record.piece_weight  

    def compute_final_priece(self):
        for product in self:
            num_of_boms = self.env['mrp.bom'].sudo().search_count(['|', ('product_tmpl_id', '=', product.id), ('byproduct_ids.product_id.product_tmpl_id', '=', product.id)])

        if num_of_boms == 1:
            self.standard_price = 0
            for bom_line in self.bom_ids[0].bom_line_ids:
                bom_line.product_id.compute_final_priece()
                self.standard_price = self.standard_price + (bom_line.product_id.standard_price* bom_line.product_qty)      
