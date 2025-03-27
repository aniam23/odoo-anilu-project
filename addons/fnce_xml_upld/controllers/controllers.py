# -*- coding: utf-8 -*-
from odoo import http

class FnceXmlUpld(http.Controller):
    @http.route('/fnce_xml_upld/fnce_xml_upld/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/fnce_xml_upld/fnce_xml_upld/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('fnce_xml_upld.listing', {
            'root': '/fnce_xml_upld/fnce_xml_upld',
            'objects': http.request.env['fnce_xml_upld.fnce_xml_upld'].search([]),
        })

    @http.route('/fnce_xml_upld/fnce_xml_upld/objects/<model("fnce_xml_upld.fnce_xml_upld"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('fnce_xml_upld.object', {
            'object': obj
        })