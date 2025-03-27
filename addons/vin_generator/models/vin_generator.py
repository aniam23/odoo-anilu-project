# -*- coding: utf-8 -*-

from odoo import models, fields, api

position_four_table = {

    "BUMPERPULL":   "B",
    "PINTLE HITCH": "P",
    "GOOSENECK":    "G",
    "KING PIN":     "K",
}

position_five_table = {

    "DUMP TRAILER":         "D",
    "ROLL OFF_DUMP":        "R",
    "TILT DECK":            "T",
    "UTILITY TRAILER":      "U",
    "CAR HAULER":           "H",
    "FLATDECK":             "F",
    "REMOVABLE GOOSENECK":  "G",
    "CHASSIS":              "C",
    "TANKER":               "K",
    "END DUMP":             "E",
    "BELLY DUMP":           "B",
    "SAND BOX TRAILER":     "S",
    "CARGO TRAILER":        "Z",
    "STOCK TRAILER":        "A",
    "SILAGE BOX":           "M",
    "VACCUM TANK":          "P",
    "CONICAL HOOPER":       "V",
    "BARBECUE":             "Y", 
}

position_six_and_seven_table = {

    "4 FEET LONG":  ["0","4"],
    "6 FEET LONG":  ["0","6"],
    "8 FEET LONG":  ["0","8"],
    "10 FEET LONG": ["1","0"],
    "12 FEET LONG": ["1","2"],
    "14 FEET LONG": ["1","4"],
    "16 FEET LONG": ["1","6"],
    "18 FEET LONG": ["1","8"],
    "20 FEET LONG": ["2","0"],
    "22 FEET LONG": ["2","2"],
    "24 FEET LONG": ["2","4"],
    "26 FEET LONG": ["2","6"],
    "28 FEET LONG": ["2","8"],
    "30 FEET LONG": ["3","0"],
    "32 FEET LONG": ["3","2"],
    "34 FEET LONG": ["3","4"],
    "36 FEET LONG": ["3","6"],
    "38 FEET LONG": ["3","8"],
    "40 FEET LONG": ["4","0"],
    "42 FEET LONG": ["4","2"],
    "44 FEET LONG": ["4","4"],
    "45 FEET LONG": ["4","5"],
    "46 FEET LONG": ["4","6"],
    "48 FEET LONG": ["4","8"],
    "51 FEET LONG": ["5","1"],
    "53 FEET LONG": ["5","3"],    
}

position_eight_table = {

    "SINGLE AXLE":  "1",
    "2 AXLES":      "2",
    "3 AXLES":      "3",
    "4 AXLES":      "4"
}
   
position_ten_table ={

    "2021": "M",
    "2022": "N",
    "2023": "P",
    "2024": "R",
    "2025": "S",
    "2026": "T",
    "2027": "V",
    "2028": "W",
    "2029": "X",
    "2030": "Y",
    "2031": "1",
    "2032": "2",
    "2033": "3",
    "2034": "4",
    "2035": "5",
    "2036": "6",
    "2037": "7",
    "2038": "8",
    "2039": "9"
}
    
digit_convert_table = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "P": 7,
        "R": 9,
        "S": 2,
        "T": 3,
        "U": 4,
        "V": 5,
        "W": 6,
        "X": 7,
        "Y": 8,
        "Z": 9
    }
list_of_multipliers = [ 8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

class vin_builder():
    vin = ["3","H","7","","","","","","","","R","","","","","",""]

    def get_count(self, count):
        return '{:06d}'.format(int(count))

    def use_comparation_rules(self,number):
        fraction = number - int(number)
        fraction = round(fraction,3)
        if fraction == 0:
            return 0
        elif fraction <= .091:
            return 1
        elif fraction <= .182:
            return 2
        elif fraction <= .273:
            return 3
        elif fraction <= .364:
            return 4
        elif fraction <= .455:
            return 5
        elif fraction <= .545:
            return 6
        elif fraction <= .634:
            return 7
        elif fraction <= .727:
            return 8
        elif fraction <= .818:
            return 9
        else:
            return "X"

    def calculateNinthDigit(self):
        array_of_numbers = []
        for digit in self.vin:
            if not digit.isnumeric() and digit != '':
               array_of_numbers.append(digit_convert_table.get(digit))
            elif digit == '':
                array_of_numbers.append(0)
            else:
                array_of_numbers.append(int(digit))
        
        count = 0
        sum_of_digits = 0.0
        for digit in array_of_numbers:
            sum_of_digits += digit * list_of_multipliers[count]
            count += 1
        
        return self.use_comparation_rules(sum_of_digits/11)


    def createVin(self, posFour, 
                  posFive, 
                  posSixSven, 
                  posEight, 
                  posTen,
                  count):
        
        self.vin[3] = position_four_table.get(posFour)
        self.vin[4] = position_five_table.get(posFive)
        posSixSev = position_six_and_seven_table.get(posSixSven)
        self.vin[5] = posSixSev[0]
        self.vin[6] = posSixSev[1]
        self.vin[7] = position_eight_table.get(posEight)

        self.vin[9] = position_ten_table.get(posTen)

        sixDigCount = self.get_count(count)

        self.vin[11] = sixDigCount[0]
        self.vin[12] = sixDigCount[1]
        self.vin[13] = sixDigCount[2]
        self.vin[14] = sixDigCount[3]
        self.vin[15] = sixDigCount[4]
        self.vin[16] = sixDigCount[5]

        self.vin[8] = str(self.calculateNinthDigit())

    def get_vin(self):
        return ''.join(self.vin)

class vin_generator(models.Model):
    _name = 'vin_generator.vin_generator'
    _table= 'vin_generator_relation'
    _description = 'Generates vins from trailer specs.'
    
    name = fields.Char(string="Name",readonly=True)
    tongue_type = fields.Selection(
        selection=[
            ('BUMPERPULL','BUMPERPULL'),
            ('PINTLE HITCH','PINTLE HITCH'),
            ('GOOSENECK','GOOSENECK'),
            ('KING PIN','KING PIN')
        ],
        string="Tongue Type"
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
    trailer_length = fields.Selection(
        selection=[
            ("4 FEET LONG","4 FEET LONG"),
            ("6 FEET LONG","6 FEET LONG"),
            ("10 FEET LONG","10 FEET LONG"),
            ("12 FEET LONG","12 FEET LONG"),
            ("14 FEET LONG","14 FEET LONG"),
            ("16 FEET LONG","16 FEET LONG"),
            ("18 FEET LONG","18 FEET LONG"),
            ("20 FEET LONG","20 FEET LONG"),
            ("22 FEET LONG","22 FEET LONG"),
            ("24 FEET LONG","24 FEET LONG"),
            ("26 FEET LONG","26 FEET LONG"),
            ("28 FEET LONG","28 FEET LONG"),
            ("30 FEET LONG","30 FEET LONG"),
            ("32 FEET LONG","32 FEET LONG"),
            ("34 FEET LONG","34 FEET LONG"),
            ("36 FEET LONG","36 FEET LONG"),
            ("38 FEET LONG","38 FEET LONG"),
            ("40 FEET LONG","40 FEET LONG"),
            ("42 FEET LONG","42 FEET LONG"),
            ("44 FEET LONG","44 FEET LONG"),
            ("45 FEET LONG","45 FEET LONG"),
            ("46 FEET LONG","46 FEET LONG"),
            ("48 FEET LONG","48 FEET LONG"),
            ("51 FEET LONG","51 FEET LONG"),
            ("53 FEET LONG","53 FEET LONG")
        ],
        string="Trailer Length"
    )
    number_of_axles = fields.Selection(
        selection=[
            ("SINGLE AXLE","SINGLE AXLE"),
            ("2 AXLES","2 AXLES"),
            ("3 AXLES","3 AXLES"),   
            ("4 AXLES","4 AXLES") 
        ],
        string= "Number Of Axles"
    )
    year_of_trailer = fields.Selection(
        selection=[
            ("2021","2021"),
            ("2022","2022"),
            ("2023","2023"),
            ("2024","2024"),
            ("2025","2025"),
            ("2026","2026"),
            ("2027","2027"),
            ("2028","2028"),
            ("2029","2029"),
            ("2030","2030"),
            ("2031","2031"),
            ("2032","2032"),
            ("2033","2033"),
            ("2034","2034"),
            ("2035","2035"),
            ("2036","2036"),
            ("2037","2037"),
            ("2038","2038"),
            ("2039","2039")
        ],
        string= "Year Of Trailer"
    )
    vin = fields.Text()

    vin_count = fields.Integer()

    production_order_relation = fields.One2many(
        'mrp.production', 'vin_relation'
    )

    @api.model_create_multi
    def create(self,vals):
        print(vals)
        vals[0]['name'] = self.env['ir.sequence'].sudo().next_by_code('vin.reference') or 'New'
        res = super(vin_generator,self).create(vals)
        return res
    
    def generate_vin(self):
        tongue = dict(self._fields['tongue_type'].selection).get(self.tongue_type)
        trailerTyp = dict(self._fields['trailer_type'].selection).get(self.trailer_type)
        trailerLen = dict(self._fields['trailer_length'].selection).get(self.trailer_length)
        numAxles = dict(self._fields['number_of_axles'].selection).get(self.number_of_axles)
        year = dict(self._fields['year_of_trailer'].selection).get(self.year_of_trailer)
        vinManager = vin_builder()
        count =  self.env['ir.sequence'].sudo().next_by_code('vin.count') or 'New'
        self.vin_count = count
        vinManager.createVin(tongue,trailerTyp,trailerLen,numAxles,year,count)
        vin = vinManager.get_vin()
        self.vin = vin


     