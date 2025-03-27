from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    is_trailer = fields.Boolean(string='Is Trailer')
    tongue_type = fields.Selection(
        selection=[
            ("BUMPERPULL", "BUMPERPULL"),
            ("GOOSENECK", "GOOSENECK"),
            ("PINTLE HITCH", "PINTLE HITCH")
        ],
        string="Tongue Type",
        default="BUMPERPULL"
    )
    length = fields.Selection(
        selection=[
            ("4 FEET LONG", "4 FEET LONG"),
            ("6 FEET LONG", "6 FEET LONG"),
            ("8 FEET LONG", "8 FEET LONG"),
            ("10 FEET LONG", "10 FEET LONG"),
            ("12 FEET LONG", "12 FEET LONG"),
            ("14 FEET LONG", "14 FEET LONG"),
            ("16 FEET LONG", "16 FEET LONG"),
            ("18 FEET LONG", "18 FEET LONG"),
            ("20 FEET LONG", "20 FEET LONG"),
            ("22 FEET LONG", "22 FEET LONG"),
            ("24 FEET LONG", "24 FEET LONG"),
            ("26 FEET LONG", "26 FEET LONG"),
            ("28 FEET LONG", "28 FEET LONG"),
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
        string="Length",
        default="16 FEET LONG"
    )
    gawr_related = fields.Many2one('vin_generator.vin_generator', string='GAWR')
    axles = fields.Selection(
        selection=[
            ("SINGLE AXLE", "SINGLE AXLE"),
            ("2 AXLES", "2 AXLES"),
            ("3 AXLES", "3 AXLES"),
            ("4 AXLES", "4 AXLES")
        ],
        string="Number Of Axles",
        default="SINGLE AXLE"
    )
    trailer_type = fields.Selection(
        selection=[
            ('DUMP TRAILER', 'DUMP TRAILER'),
            ('ROLL OFF_DUMP', 'ROLL OFF_DUMP'),
            ('TILT DECK', 'TILT DECK'),
            ('UTILITY TRAILER', 'UTILITY TRAILER'),
            ('CAR HAULER', 'CAR HAULER'),
            ('FLATDECK', 'FLATDECK'),
            ('REMOVABLE GOOSENECK', 'REMOVABLE GOOSENECK'),
            ('CHASSIS', 'CHASSIS'),
            ('TANKER', 'TANKER'),
            ('END DUMP', 'END DUMP')
        ],
        string="Trailer Type"
    )
    model_year = fields.Selection(
        selection=lambda self: self.year_selection(),
        string="Year",
        default="2021"
    )

   
    dry_weight = fields.Integer(
        string="DRY WEIGHT",
        help="Peso del remolque sin carga (en kg o lbs)",
        digits=(10, 2) 
    )

    @api.model
    def year_selection(self):
        year = 2021
        year_list = []
        while year != 2040:
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

class ProductProduct(models.Model):
    _inherit = 'product.product'

    gvwr_child = fields.Many2one('vin_generator.gvwr_manager', string='GAWR Child')

    @api.model_create_multi
    def create(self, vals_list):
        products = super(ProductProduct, self).create(vals_list)
        for product in products:
            product.gvwr_child = product.product_tmpl_id.gawr_related
        return products