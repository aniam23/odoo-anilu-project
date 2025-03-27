# -*- coding: utf-8 -*-
{
    'name': "Finance Xml Upload",

    'summary': """
        XML uploader""",

    'description': """
        Module in charge of uploading xml files and create draft invoices and bills
    """,
    'author': "Javier Gonzalez Pena",
    'website': "http://www.horizontrailers.com",
    'sequence': 1,
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '3.0',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','account','web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/log_views.xml',
        'report/fnce_xml_upld_log_reference_templates.xml',
        'report/fnce_xml_upld_log_reference_report.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}