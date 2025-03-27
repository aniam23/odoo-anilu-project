# -*- coding: utf-8 -*-

from odoo import models,fields,api
class product_gvwr(models.Model):
    _inherit = 'product.template'
    
    is_trailer = fields.Boolean(string='Is Trailer')
    tongue_type = fields.Selection(
        selection=[
            ("BUMPERPULL","BUMPERPULL"),
            ("GOOSENECK","GOOSENECK"),
            ("PINTLE HITCH","PINTLE HITCH")
        ],
        string="Tongue Type",
        default="BUMPERPULL"
    )
    length = fields.Selection(
        selection=[
            ("4 FEET LONG" ,"4 FEET LONG"),
            ("6 FEET LONG" ,"6 FEET LONG"),
            ("8 FEET LONG" ,"8 FEET LONG"),
            ("10 FEET LONG", "10 FEET LONG"),
            ("12 FEET LONG", "12 FEET LONG"),
            ("14 FEET LONG", "14 FEET LONG"),
            ("16 FEET LONG", "16 FEET LONG"),
            ("18 FEET LONG", "18 FEET LONG"),
            ("20 FEET LONG", "20 FEET LONG"),
            ("22 FEET LONG", "22 FEET LONG"),
            ("24 FEET LONG", "24 FEET LONG"),
            ("26 FEET LONG", "26 FEET LONG"),
            ("28 FEET LONG", "28 FETT LONG"),
            ("30 FEET LONG", "30 FEET LONG"),
            ("32 FEET LONG", "32 FEET LONG"),
            ("34 FEET LONG", "34 FEET LONG"),
            ("36 FEET LONG", "36 FEET LONG"),
            ("38 FEET LONG", "38 FEET LONG"),
            ("40 FEET LONG", "40 FEET LONG"),
            ("42 FEET LONG", "42 FEET LONG"),
            ("44 FEET LONG", "44 FEET LONG"),
            ("45 FEET LONG", "45 FEET LONG"),
            ("46 FEET LONG", "46 FEET LONG"),
            ("48 FEET LONG", "48 FEET LONG"),
            ("51 FEET LONG", "51 FEET LONG"),
            ("53 FEET LONG", "53 FEET LONG")
        ],
        string= "Length",
        default= "16 FEET LONG"
    )
    
    gvwr_related = fields.Many2one(
        'vin_generator.gvwr_manager', 'GVWR',
    )

    axles = fields.Selection(
        selection=[
            ("SINGLE AXLE","SINGLE AXLE"),
            ("2 AXLES","2 AXLES"),
            ("3 AXLES","3 AXLES"),   
            ("4 AXLES","4 AXLES") 
        ],
        string= "Number Of Axles",
        default= "SINGLE AXLE"
    )
    trailer_type = fields.Selection(
        selection=[
            ('DUMP TRAILER','DUMP TRAILER'),
            ('ROLL OFF_DUMP','ROLL OFF_DUMP'),
            ('TILT DECK','TILT DECK'),
            ('UTILITY TRAILER','UTILITY TRAILER'),
            ('CAR HAULER','CAR HAULER'),
            ('FLATDECK','FLATDECK'),
            ('REMOVABLE GOOSENECK','REMOVABLE GOOSENECK'),
            ('CHASSIS','CHASSIS'),
            ('TANKER','TANKER'),
            ('END DUMP','END DUMP')
        ],
        string="Trailer Type"
    )
    @api.model
    def year_selection(self): 
        year = 2021 # replace 2000 with your a start year
        year_list = []
        while year != 2040: # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    model_year = fields.Selection(
        year_selection,
        string="Year",
        default="2021"
    )

class product_child_gvwr(models.Model):
    _inherit = 'product.product'

    gvwr_child = fields.Many2one(
        'vin_generator.gvwr_manager', 'GVWR Child'
    )

    @api.model_create_multi
    def create(self, vals):
        result = super(product_child_gvwr, self).create(vals)
        result.gvwr_child = result.product_tmpl_id.gvwr_related
        return result