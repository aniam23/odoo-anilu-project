from odoo import models, fields, api

class log_reference(models.Model):
    _name = 'fnce_xml_upld.log_reference'
    _table = 'fnce_xml_upld_log_reference'
    _description = 'Helps on maneging logs of reference payments and invoices'
    name = fields.Char(string="Name",readonly=True)
    date = fields.Datetime(string="Creation Date",readonly=True)
    invoiceRef = fields.Many2one(comodel_name='account.move',
                                  string='Invoice Reference'
                                  )
    
    attachmentRef = fields.Many2one(comodel_name='ir.attachment',
                                     string='Attachment Reference',
                                     )
    
    paymentRef = fields.Many2many(comodel_name='account.payment',
                                  string='Payment Reference',
                                  )
    
    paymentRelation = fields.Many2many(comodel_name='account.payment.register',
                                  string='Registered Payment Reference',
                                  )
    @api.model_create_multi
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('fnce_xml_upld.log_reference') or 'New'
        res = super().create(vals)
        return res
    @api.ondelete(at_uninstall=False)
    def delete_related_fields(self):
        for record in self:
            relatedDoc = record.env['ir.attachment'].browse(record.attachmentRef.id)
            relatedDoc.unlink()
        
        

    
    
 