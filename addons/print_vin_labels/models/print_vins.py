from odoo import models, fields, api
from odoo.exceptions import UserError
from io import BytesIO
from datetime import datetime 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import base64

class PrintVins(models.Model):  
    _name = 'print.vins'
    _description = 'Print VIN Labels'
    name = fields.Char(string='Name')
    sale_order = fields.Many2one('sale.order', string='Sales Orders')
    model_hs7 = fields.Many2many(comodel_name='mrp.production', string='MODEL HS7')
    gvwr = fields.Many2many(comodel_name='vin_generator.gvwr_manager', string='gvwr_related')
    gawr = fields.Many2many(comodel_name='print.gawr', string='name')
    gawr_lb = fields.Float(string='Gawr lb')
    printer_port = fields.Integer(string='Puerto de la Impresora', default=9100)
    weight_total = fields.Float(string='Peso total')
    product_name = fields.Char(string='Product_name')
    pdf_file = fields.Binary(string='PDF File', attachment=True)
    pdf_filename = fields.Char(string='PDF Filename', compute='_compute_pdf_filename')

    @api.depends('name')
    def _compute_pdf_filename(self):
        for record in self:
            record.pdf_filename = f"vin_label_{record.name or 'unknown'}.pdf"

    def get_data(self):
        # list_of_data = []
        # manufacturing_order_list = self.env['mrp.production'].search([])
        # for order in manufacturing_order_list:
        #     if hasattr(order, 'vin_dispayed') and order.vin_dispayed:
        #         product_vin = order.vin_dispayed
        #         product_name = order.product_id.display_name
        #         date = order.date_planned_start
        #         list_of_data.append({
        #             "vin": product_vin,
        #             "date": date,
        #             "product_name": product_name,
        #             "order_id": order.id,
        #         })
        # if not list_of_data:
        #     raise ValueError("No se encontraron órdenes de producción con el campo 'vin_dispayed'.")
        # return list_of_data
        return self.model_hs7.vin_dispayed

    def generate_pdf(self):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        data_list = self.get_data()
        gvwr = False
        gawr = False
        if self.model_hs7:
            if self.model_hs7.product_id.gvwr_child:
                gvwr = self.model_hs7.product_id.gvwr_child
            elif self.model_hs7.product_id.gvwr_related:
                gvwr = self.model_hs7.product_id.gvwr_related
        if self.model_hs7:
            if self.model_hs7.product_id.gawr_related:
                gawr = self.model_hs7.product_id.gawr_related

        if gvwr == False:
            raise ValueError("No se ha seleccionado un registro para 'gvwr'.")
        gvwr_lb = gvwr.weight_lb
        gvwr_kg = gvwr.weight_kg

        if gawr == False:
            raise ValueError("No se ha seleccionado un registro para 'gawr'.")
        gawr_libras = gawr.name
        gawr_lb = gawr_libras[5:9]
        gawr_kg = round(float(gawr_lb) * 0.453592, 1)

        if not self.model_hs7:
            raise UserError("No se ha seleccionado un registro en 'HS7'.")
        product = self.model_hs7.product_id
        product_name = self.model_hs7.product_id.display_name
        model_string = product_name.split(" ")[0].replace('[','').replace(']','')
        weight_lb = self.model_hs7.product_id.dry_weight
        carga_maxima_lb = weight_lb - gvwr_lb 
        weight_kg = int(round(carga_maxima_lb  * 0.453592))
        product_vin = None

        if data_list:
            product_vin = data_list        
        
        tire_rating = ""
        lbs_wheels = ""
        rin = ""
        num_rin=""
        wheel_names = []
        wheels_count = {}
        
        tire_type = product.tire_typ
        if product.bom_ids:  
            bom_lines = product.bom_ids[0].bom_line_ids  
            for bom_line in bom_lines:
                bom_product = bom_line.product_id
                 
                bom_product_name = bom_product.display_name.upper()
                if 'LLANTA' in bom_product_name:
                    if bom_product.id in wheels_count:
                        wheels_count[bom_product.id] += bom_line.product_qty
                    else:
                        wheels_count[bom_product.id] = bom_line.product_qty
                        wheel_names.append(bom_product_name)
                    if not rin:
                        for size in ['R15', 'R16', 'R17.5']:
                            if size in bom_product_name:
                                rin = size
                                break
                    full_tire_array = bom_product_name.split(" ") 
                    rin = full_tire_array[1]
                    num_rin= f"{full_tire_array[9]} {full_tire_array[10]} {full_tire_array[11]}"

        wheel_name_str = ' '.join(wheel_names) if wheel_names else "No se encontraron llantas en la lista de materiales"


        if 'SINGLE' == tire_type and 'R15' in wheel_name_str and ('10PLY' in wheel_name_str or '10PR' in wheel_name_str):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '2830 LBS'
        elif 'SINGLE' == tire_type and 'R15' in wheel_name_str and ('8PLY' in wheel_name_str or '8PR' in wheel_name_str):
            lbs_wheels = '448 KPA/65 PSI'
            tire_rating = '2150 LBS'
        elif 'SINGLE' == tire_type and 'R15' in wheel_name_str and ('6PLY' in wheel_name_str or '6PR' in wheel_name_str):
            lbs_wheels = '334 KPA/50 PSI'
            tire_rating = '1820 LBS'
        elif 'SINGLE' == tire_type and 'R16' in wheel_name_str and ('10PLY' in wheel_name_str or '10PR' in wheel_name_str):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3520 LBS'
        elif 'DUAL' == tire_type and 'R16' in wheel_name_str and ('10PLY' in wheel_name_str or '10PR' in wheel_name_str):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3080 LBS'
        elif 'SINGLE' == tire_type and 'R16' in wheel_name_str and ('14PLY' in wheel_name_str or '14PR' in wheel_name_str):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '4400 LBS'
        elif 'DUAL' == tire_type and 'R16' in wheel_name_str and ('14PLY' in wheel_name_str or '14PR' in wheel_name_str):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '3860 LBS'
        elif 'SUPER SINGLE' == tire_type and 'R17.5' in wheel_name_str and ('18PLY' in wheel_name_str or '18PR' in wheel_name_str):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '6005 LBS'
        elif 'DUAL' == tire_type and 'R17.5' in wheel_name_str and ('18PLY' in wheel_name_str or '18PR' in wheel_name_str):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '5675 LBS'


        result = rin

        c.setFont("Helvetica", 10)
        y_position = height - 20 * mm

        c.drawString(20 * mm, y_position, f"The weight of the cargo should never exceed {weight_kg} kg or {carga_maxima_lb} lbs")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"le poids du chargement ne doit jamais depasser {weight_kg} kg ou {carga_maxima_lb} lb.")
        y_position -= 10 * mm

        c.drawString(20 * mm, y_position, result)
        c.drawString(100 * mm, y_position, lbs_wheels)
        y_position -= 10 * mm

        c.drawString(20 * mm, y_position, "MANUFACTURED BY/FABRIQUE PAR: HORIZON TRAILERS MEXICO S. DE R.L. DE C.V.")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"GVWR / PNBV {gvwr_kg} KG ({gvwr_lb} LB) DATE: 26/03/2025")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"GAWR (EACH AXLE) / PNBE ( CHAQUE ESSIEU) {gawr_kg}KG({gawr_lb})LBS")
        y_position -= 5 * mm
        c.drawString(20 * mm, y_position, f"TIRE/PNEU {rin}  RIM/JANTE {num_rin} {tire_rating}")
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


    def print_vins(self): 
        pdf_data = self.generate_pdf()
        self.write({
            'pdf_file': pdf_data
        })
      
        data_list = self.get_data()
        gvwr = False
        gawr = False
        if self.model_hs7:
            if self.model_hs7.product_id.gvwr_child:
                gvwr = self.model_hs7.product_id.gvwr_child
            elif self.model_hs7.product_id.gvwr_related:
                gvwr = self.model_hs7.product_id.gvwr_related
        if self.model_hs7:
            if self.model_hs7.product_id.gawr_related:
                gawr = self.model_hs7.product_id.gawr_related

        if gvwr == False:
            raise ValueError("No se ha seleccionado un registro para 'gvwr'.")
        gvwr_lb = gvwr.weight_lb
        gvwr_kg = gvwr.weight_kg

        if gawr == False:
            raise ValueError("No se ha seleccionado un registro para 'gawr'.")
        gawr_libras = gawr.name
        gawr_lb = gawr_libras[5:9]
        gawr_kg = round(float(gawr_lb) * 0.453592, 1)

        if not self.model_hs7:
            raise UserError("No se ha seleccionado un registro en 'HS7'.")
        product = self.model_hs7.product_id
        product_name = self.model_hs7.product_id.display_name
        model_string = product_name.split(" ")[0].replace('[','').replace(']','')
        weight_lb = self.model_hs7.product_id.dry_weight
        carga_maxima_lb = weight_lb - gvwr_lb 
        weight_kg = int(round(carga_maxima_lb  * 0.453592))
        product_vin = None

        if data_list:
            product_vin = data_list        
        
        tire_rating = ""
        lbs_wheels = ""
        rin = ""
        num_rin=""
        wheel_names = []
        wheels_count = {}
        
        tire_type = product.tire_typ
        if product.bom_ids:  
            bom_lines = product.bom_ids[0].bom_line_ids  
            for bom_line in bom_lines:
                bom_product = bom_line.product_id
                 
                bom_product_name = bom_product.display_name.upper()
                if 'LLANTA' in bom_product_name:
                    if bom_product.id in wheels_count:
                        wheels_count[bom_product.id] += bom_line.product_qty
                    else:
                        wheels_count[bom_product.id] = bom_line.product_qty
                        wheel_names.append(bom_product_name)
                    if not rin:
                        for size in ['R15', 'R16', 'R17.5']:
                            if size in bom_product_name:
                                rin = size
                                break
                full_tire_array = bom_product_name.split(" ") 
                rin = full_tire_array[1]
                num_rin= f"{full_tire_array[8]} {full_tire_array[9]} {full_tire_array[10]}"

        wheel_name_str = ' '.join(wheel_names) if wheel_names else "No se encontraron llantas en la lista de materiales"


        if 'SINGLE' in wheel_name_str and 'R15' in wheel_name_str and ('10PLY' in wheel_name_str or '10PR' in wheel_name_str):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '2830 LBS'
        elif 'SINGLE' in wheel_name_str and 'R15' in wheel_name_str and ('8PLY' in wheel_name_str or '8PR' in wheel_name_str):
            lbs_wheels = '448 KPA/65 PSI'
            tire_rating = '2150 LBS'
        elif 'SINGLE' in wheel_name_str and 'R15' in wheel_name_str and ('6PLY' in wheel_name_str or '6PR' in wheel_name_str):
            lbs_wheels = '334 KPA/50 PSI'
            tire_rating = '1820 LBS'
        elif 'SINGLE' in wheel_name_str and 'R16' in wheel_name_str and ('10PLY' in wheel_name_str or '10PR' in wheel_name_str):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3520 LBS'
        elif 'DUAL' in wheel_name_str and 'R16' in wheel_name_str and ('10PLY' in wheel_name_str or '10PR' in wheel_name_str):
            lbs_wheels = '550 KPA/80 PSI'
            tire_rating = '3080 LBS'
        elif 'SINGLE' in wheel_name_str and 'R16' in wheel_name_str and ('14PLY' in wheel_name_str or '14PR' in wheel_name_str):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '4400 LBS'
        elif 'DUAL' in wheel_name_str and 'R16' in wheel_name_str and ('14PLY' in wheel_name_str or '14PR' in wheel_name_str):
            lbs_wheels = '758 KPA/110 PSI'
            tire_rating = '3860 LBS'
        elif 'SUPER SINGLE' in wheel_name_str and 'R17.5' in wheel_name_str and ('18PLY' in wheel_name_str or '18PR' in wheel_name_str):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '6005 LBS'
        elif 'DUAL' in wheel_name_str and 'R17.5' in wheel_name_str and ('18PLY' in wheel_name_str or '18PR' in wheel_name_str):
            lbs_wheels = '862 KPA/125 PSI'
            tire_rating = '5675 LBS'


        result = rin
       
        zpl_template = """
        ^XA
         ^FO650,50^ADR,20,10^FDThe weight of the cargo should never exceed {weight_kg} kg or {carga_maxima_lb} lbs^FS
         ^FO630,50^ADR,20,10^FDle poids du chargement ne doit jamais depasser {weight_kg} kg ou {carga_maxima_lb} lb.^FS
         ^FO490,5^ADR,20,10^FD      
            {result}  ^FS   
         ^FO490,210^ADR,20,10^FD  
                {lbs_wheels}  ^FS
         ^FO450,5^ADR,20,10^FD      
            {result}  ^FS   
         ^FO450,210^ADR,20,10^FD  
                {lbs_wheels}  ^FS
         ^FO400,5^ADR,20,10^FD      
            {result}  ^FS   
         ^FO400,210^ADR,20,10^FD  
                {lbs_wheels}  ^FS
         ^FO390,800^ADR,15,10^FWN^FDR^FD {product_vin} ^FS
         ^FO300,50^ADR,25,10^FDMANUFACTURED BY/FABRIQUE PAR: HORIZON TRAILERS MEXICO S. DE R.L. DE C.V.^FS
         ^FO280,50^ADR,25,10^FDGVWR / PNBV  {gvwr_kg} KG ( {gvwr_lb} LB) 
                                      DATE: 26/03/2025^FS  
         ^FO260,50^ADR,25,10^FDGAWR (EACH AXLE) / PNBE ( CHAQUE ESSIEU) {gawr_kg} KG({gawr_lb})LBS^FS
         ^FO240,50^ADR,25,10^FDTIRE/PNEU {rin}  RIM/JANTE {num_rin} {tire_rating} ^FS
         ^FO215,50^ADR,25,10^FDCOLD INFL. PRESS/PRESS. DE GONFL. A FROID {lbs_wheels}/LCP SINGLE^FS
         ^FO190,50^A0R,20,20^FDTHIS VEHICLE TO ALL APPLICABLE U.S. FEDERAL MOTOR SAFETY STANDARDS IN EFFECT ON THE DATE OF MANUFACTURE ^FS
         ^FO170,50^A0R,20,20^FDSHOWN ABOVE.THIS VEHICLE CONFORMS TO ALL APPLICABLE STANDARDS PRESCRIBED UNDER CANADA.^FS
         ^FO150,50^A0R,20,20^FDATE OF MANUFACTURE./.. CE VEHICLE EST CONFORME A TOUS LES NORMES EN VIGUEUR A LA DATE DE SA FABRICATION.^FS
         ^FO130,50^A0R,20,20^FDSUR LA SECURITÉ DES VARIÉGLES AUTOMOBILES DU CANADA EN VIGUEUR A LA DATE DE SA FABRICATION.^FS
         ^FO90,50^ADR,15,10^FDVIN.:{product_vin}^FS
         ^FO90,500^ADR,15,10^FDTYPE:TRA/REM^FS        ^FO90,800^ADR,15,10^FDMODEL:{model_string} ^FS
         ^XZ
         """
       
        zpl_code = zpl_template.format(
                result=result,
                weight_lb=weight_lb,
                carga_maxima_lb=carga_maxima_lb,
                weight_kg=weight_kg,
                lbs_wheels=lbs_wheels,
                rin=rin,
                num_rin = num_rin,
                tire_rating=tire_rating,
                product_vin=product_vin,
                gvwr_kg=gvwr_kg,
                gvwr_lb=gvwr_lb,
                gawr_kg=gawr_kg,
                gawr_lb=gawr_lb,
                model_string=model_string,
                date=datetime.now().strftime('%d/%m/%Y')
            )
      
        return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/print.vins/%s/pdf_file/%s?download=true' % (self.id, self.pdf_filename),
                    'target': 'self',
            }
            
            
              
