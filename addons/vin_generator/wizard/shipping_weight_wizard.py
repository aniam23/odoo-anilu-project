from odoo import models,fields,api

class shipping_weight_wizard(models.TransientModel):
    _name = 'shipping.weight.wizard'
    _description = 'Wizard aid to get weight from user input'

    mo_date = fields.Text()
    product_vin = fields.Text()
    product_body_type = fields.Text()

    weight = fields.Integer()

    invoice = fields.Many2one(
        comodel_name='account.move',
    )
    sale_order = fields.Many2one(
        comodel_name='sale.order'
    )

    def transform_to_lbs(self, kg):
        lb = int(float(kg) * 2.205)
        shipping_text = str(kg)+"KG ("+str(lb)+"LB)"
        return shipping_text
    
    def format_date(self, dateToFormat):
        auxArrayOfStrings = dateToFormat.split()
        auxArrayOfStrings = auxArrayOfStrings[0].split("-")
        return {
            "date": str(auxArrayOfStrings[2])+"/"+str(auxArrayOfStrings[1])+"/"+str(auxArrayOfStrings[0]),
            "year": str(auxArrayOfStrings[0])
        }
    
    def format_body_type(self,bodyTypeString):
        if "_" in bodyTypeString:
            return "ROLL OFF DUMP"
        else:
            return bodyTypeString
        
    def format_gvwr(self, product):
        lb = product.gvwr_related.weight_lb
        kg = product.gvwr_related.weight_kg
        name = product.display_name
        return {
            "gvwr": str(kg)+" KG ("+str(lb)+" LBS)",
            "model": name
        }
    def get_data(self):

        list_of_data = []
        mo_orders = []

        manufacturing_order_list = self.env['mrp.production'].search([])
        weight_text = self.transform_to_lbs(self.weight)
        for order in manufacturing_order_list:
            if order.origin != False and order.origin == self.sale_order.name:
                mo_orders.append(order)

        for mo_order in mo_orders:
            mo_date = mo_order.date_planned_start
            product_vin = mo_order.vin_dispayed
            product_body_type = mo_order.vin_relation.trailer_type

            dateAndYear = self.format_date(str(mo_date))
            bodyType = self.format_body_type(product_body_type)
            productInfo = self.format_gvwr(mo_order.product_id)
            invoice_name = self.invoice.display_name

            list_of_data.append({
                "date": dateAndYear["date"],
                "vin":product_vin,
                "body_type": bodyType,
                "gvwr": productInfo["gvwr"],
                "invoice_number": invoice_name,
                "year": dateAndYear["year"],
                "shipping_weight": weight_text,
                "model_name": productInfo["model"],
                "last_data": False
            })
        
        list_of_data[len(list_of_data)-1]["last_data"] = True
        return list_of_data

    def set_data(self):
        fullData = self.get_data()
        return self.env.ref('vin_generator.title_print').report_action(self,data={
            'id':self.id,
            'full_data': fullData
            })



