from odoo import models, fields, api
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import base64
from datetime import datetime

class ManualPrint(models.Model):
    _name= 'print.manual'
    _description = 'Impresión manual de datos de remolques'
    name = fields.Char(string='Name')
    model_trailer = fields.Char(string="MODELO REMOLQUE")
    wheel = fields.Char(string="LLANTA")
    dry_weight = fields.Float(string="PESO TOTAL (LBS)")
    pdf_filename = fields.Char(string='PDF Filename')
    vin_registry= fields.Many2one('vin_generator.vin_generator', string='vin')
    gvwr= fields.Many2one('vin_generator.gvwr_manager', string='gvwr')
    gawr= fields.Many2one('print.gawr', string='gawr')
    pdf_file = fields.Binary(string='PDF File', attachment=True)

    @api.model_create_multi
    def create(self,vals):
        print(vals)
        vals[0]['name'] = self.env['ir.sequence'].sudo().next_by_code('manual.print.reference') or 'New'
        self._compute_pdf_filename()
        res = super(ManualPrint,self).create(vals)
        return res
    
  
    def _compute_pdf_filename(self):
        for record in self:
            record.pdf_filename = f"vin_label_{record.name or 'unknown'}.pdf"

    def generate_manual_pdf(self):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
       
        product_vin = self.vin_registry.vin if self.vin_registry else ""
        model_string = self.model_trailer or ""
        weight_lb = self.dry_weight or 0
        weight_kg = int(round(weight_lb * 0.453592))
        rin = self.wheel or "MANUAL_WHEEL"
        
        lbs_wheels = ""
        tire_rating = ""
        gvwr_kg = self.gvwr.weight_kg if self.gvwr else 0
        gvwr_lb = self.gvwr.weight_lb if self.gvwr else 0
        num_rin = ""
        gawr_libras = self.gawr.name
        gawr_lb = gawr_libras[5:9]
        gawr_kg = round(float(gawr_lb) * 0.453592, 1)
        wheel_input = (self.wheel or "").upper()
        rin = ""
        
        if wheel_input:
            full_tire_array = wheel_input.split(" ") 
            rin = full_tire_array[1] if len(full_tire_array) > 1 else ""
            if len(full_tire_array) > 10:
                num_rin = f"{full_tire_array[8]} {full_tire_array[9]} {full_tire_array[10]}"

        if 'SINGLE' in wheel_input and 'R15' in wheel_input and ('10PLY' in wheel_input or '10PR' in wheel_input):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '2830 LBS'
        elif 'SINGLE' in wheel_input and 'R15' in wheel_input and ('8PLY' in wheel_input or '8PR' in wheel_input):
            lbs_wheels = '448 KPA/65 PSI'
            tire_rating = '2150 LBS'
        elif 'SINGLE' in wheel_input and 'R15' in wheel_input and ('6PLY' in wheel_input or '6PR' in wheel_input):
            lbs_wheels = '334 KPA/50 PSI'
            tire_rating = '1820 LBS'
        elif 'SINGLE' in wheel_input and 'R16' in wheel_input and ('10PLY' in wheel_input or '10PR' in wheel_input):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3520 LBS'
        elif 'DUAL' in wheel_input and 'R16' in wheel_input and ('10PLY' in wheel_input or '10PR' in wheel_input):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3080 LBS'
        elif 'SINGLE' in wheel_input and 'R16' in wheel_input and ('14PLY' in wheel_input or '14PR' in wheel_input):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '4400 LBS'
        elif 'DUAL' in wheel_input and 'R16' in wheel_input and ('14PLY' in wheel_input or '14PR' in wheel_input):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '3860 LBS'
        elif 'SUPER SINGLE' in wheel_input and 'R17.5' in wheel_input and ('18PLY' in wheel_input or '18PR' in wheel_input):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '6005 LBS'
        elif 'DUAL' in wheel_input and 'R17.5' in wheel_input and ('18PLY' in wheel_input or '18PR' in wheel_input):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '5675 LBS'

        c.setFont("Helvetica", 10)
        y_position = height - 20 * mm
        c.drawString(20 * mm, y_position, f"The weight of the cargo should never exceed {weight_kg} kg or {weight_lb} lbs")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"le poids du chargement ne doit jamais depasser {weight_kg} kg ou {weight_lb} lb.")
        y_position -= 10 * mm

        c.drawString(20 * mm, y_position, rin)
        c.drawString(100 * mm, y_position, lbs_wheels)
        y_position -= 10 * mm

        c.drawString(20 * mm, y_position, "MANUFACTURED BY/FABRIQUE PAR: HORIZON TRAILERS MEXICO S. DE R.L. DE C.V.")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"GVWR / PNBV {gvwr_kg} KG ({gvwr_lb} LB) ")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"GAWR (EACH AXLE) / PNBE ( CHAQUE ESSIEU) {gawr_kg} KG ({gawr_lb} LB)")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"TIRE/PNEU {rin} RIM/JANTE {num_rin} {tire_rating}")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"COLD INFL. PRESS/PRESS. DE GONFL. A FROID {lbs_wheels}/LCP SINGLE")
        y_position -= 10 * mm

        c.drawString(20 * mm, y_position, "THIS VEHICLE TO ALL APPLICABLE U.S. FEDERAL MOTOR SAFETY STANDARDS")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, "IN EFFECT ON THE DATE OF MANUFACTURE SHOWN ABOVE.")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, "THIS VEHICLE CONFORMS TO ALL APPLICABLE STANDARDS PRESCRIBED UNDER CANADA.")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, "CE VEHICLE EST CONFORME A TOUS LES NORMES EN VIGUEUR A LA DATE DE SA FABRICATION.")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, "SUR LA SECURITÉ DES VARIÉGLES AUTOMOBILES DU CANADA EN VIGUEUR A LA DATE DE SA FABRICATION.")
        y_position -= 10 * mm

        c.drawString(20 * mm, y_position, f"VIN: {product_vin}")
        c.drawString(100 * mm, y_position, "TYPE: TRA/REM")
        c.drawString(180 * mm, y_position, f"MODEL: {model_string}")

        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()

        return base64.b64encode(pdf_data)

    def print_manual_vins(self):
        pdf_data = self.generate_manual_pdf()
        self.write({
            'pdf_file': pdf_data
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/print.manual/{self.id}/pdf_file/{self.pdf_filename}?download=true',
            'target': 'self',
        }
    



