from odoo import models, fields, api
class MainViews(models.Model):
    _name = 'main.view'
    _description = 'main view of pending shipments'
    _order = 'create_date desc'
    