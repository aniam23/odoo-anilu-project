# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SeqCdcInv(models.Model):
    _name = 'sequence.fab'

    name = fields.Char('nombre')
    seq = fields.Integer('consecutivo')

    def get_seq_mm(self, nam):
        bus = self.env['sequence.fab'].search([('name', '=', nam)])
        if bus:
            current = bus.seq
            bus.write({'seq': bus.seq + 1})
            return current
        else:
            secu = self.env['sequence.fab'].create({
                'name': nam,
                'seq': 2,
            })
            return 1

