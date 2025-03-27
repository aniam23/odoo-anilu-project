# -*- coding: utf-8 -*-

from odoo import models, fields, api
body_type_relation = {
    "HZ5"       : "DUMP TRAILER",
    "HZ6"       : "DUMP TRAILER",
    "EZ7"       : "DUMP TRAILER",
    "LZ7"       : "DUMP TRAILER",
    "HZ7"       : "DUMP TRAILER",
    "HZX"       : "DUMP TRAILER",
    "HZH"       : "DUMP TRAILER",
    "RDZ"       : "ROLL OFF_DUMP",
    "HRD"       : "ROLL OFF_DUMP",
    "HDZ"       : "ROLL OFF_DUMP",
    "ETZ"       : "TILT DECK",
    "HET"       : "TILT DECK",
    "EHZ"       : "UTILITY TRAILER",
    "HEH"       : "UTILITY TRAILER",
    "EWZ"       : "UTILITY TRAILER",
    "FTZ"       : "FLATDECK",
    "FHZ"       : "FLATDECK",
    "FHZSS"     : "FLATDECK",
    "FYZ"       : "FLATDECK",
    "FYZSS"     : "FLATDECK",
    "HYZ"       : "FLATDECK",

    "EDZ"       : "ROLL OFF_DUMP",
    "HCZ"       : "ROLL OFF_DUMP",
    "ROZ"       : "ROLL OFF_DUMP",
    "UTZ"       : "UTILITY TRAILER",
    "HHZ"       : "FLATDECK",
    "FFT"       : "FLATDECK",
    "FFH"       : "FLATDECK"
}
body_type_list = [
    "HZ5",
    "HZ6",
    "EZ7",
    "LZ7",
    "HZ7",
    "HZX",
    "HZH",
    "RDZ",
    "HRD",
    "HDZ",
    "ETZ",
    "HET",
    "EHZ",
    "HEH",
    "EWZ",
    "FTZ",
    "FHZ",
    "FHZSS",
    "FYZ",
    "FYZSS",
    "HYZ",

    "EDZ",
    "HCZ",
    "ROZ",  
    "UTZ",
    "HHZ",
    "FFT",
    "FFH"
]
tongue_type_relation = {
    "BP" : "BUMPERPULL",
    "GN" : "GOOSENECK",
    "PH" : "PINTLE HITCH"
}
tongue_type_list = [
    "BP",
    "GN",
    "PH"
]
length_type_relation = {
    "4" : "4 FEET LONG",
    "6" : "6 FEET LONG",
    "8" : "8 FEET LONG",
    "10" : "10 FEET LONG",
    "12" : "12 FEET LONG",
    "14" : "14 FEET LONG",
    "16" : "16 FEET LONG",
    "18" : "18 FEET LONG",
    "20" : "20 FEET LONG",
    "22" : "22 FEET LONG",
    "24" : "24 FEET LONG",
    "26" : "26 FEET LONG",
    "28" : "28 FETT LONG",
    "30" : "30 FEET LONG",
    "32" : "32 FEET LONG",
    "34" : "34 FEET LONG",
    "36" : "36 FEET LONG",
    "38" : "38 FEET LONG",
    "40" : "40 FEET LONG",
    "42" : "42 FEET LONG",
    "44" : "44 FEET LONG",
    "45" : "45 FEET LONG",
    "46" : "46 FEET LONG",
    "48" : "48 FEET LONG",
    "51" : "51 FEET LONG",
    "53" : "53 FEET LONG"
}
length_type_list = [
    "4",
    "6",
    "8",
    "10",
    "12",
    "14",
    "16",
    "18",
    "20",
    "22",
    "24",
    "26",
    "28",
    "30",
    "32",
    "34",
    "36",
    "38",
    "40",
    "42",
    "44",
    "45",
    "46",
    "48",
    "51",
    "53"
]


class production_vin(models.Model):
    _inherit = 'mrp.production',

    vin_dispayed = fields.Text(string="Vin", compute="calculate_vin", store=True)
    vin_relation = fields.Many2one(
        'vin_generator.vin_generator', 'production_order_relation'
    )
    show_vin = fields.Boolean()


    def get_if_product_is_trailer(self,production_order):
        product = self.env['product.template'].search([('name', '=' ,production_order.product_id.name)],limit=1)
        return product.is_trailer
    
    @api.depends('state')
    def calculate_vin(self):
        for record in self:
            is_trailer = self.get_if_product_is_trailer(record)
            record.show_vin = is_trailer
            if not is_trailer:
                return
            if record.state == "confirmed" and is_trailer and record.vin_dispayed == False:
                list_of_properties = record.get_info_from_product(record.product_id.name)
                newVin = self.env['vin_generator.vin_generator'].create({
                    "tongue_type" : list_of_properties[0],
                    "trailer_type" : list_of_properties[1],
                    "trailer_length" : list_of_properties[2],
                    "number_of_axles" : list_of_properties[3],
                    "year_of_trailer" : list_of_properties[4]
                })
                newVin.generate_vin()
                record.vin_relation = newVin
                record.vin_dispayed = newVin.vin

 
    def get_info_from_product(self,name):
        body_type = self.product_id.trailer_type
        
        year = self.product_id.model_year

        axle = self.product_id.axles

        tongue_type = self.product_id.tongue_type

        length = self.product_id.length

        list_of_properties = [
            tongue_type,
            body_type,
            length,
            axle,
            year
        ]
        return list_of_properties
