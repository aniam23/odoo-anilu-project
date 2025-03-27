# -*- coding: utf-8 -*-
{
    'name': "VIN Generator",

    'summary': """
        VIN Generator""",

    'description': """
        Calculates vin for trailer based in desription and selected options
    """,

    'author': "Javier Gonzalez Pena",
    'website': "http://www.horizontrailers.com",
    'sequence': 2,

    'version': '2.0',

    'depends': ['base','product','mrp', 'account', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/shipping_weight_view.xml',
        'views/vin_generator_templates.xml',
        'views/vin_generator_view.xml',
        'views/gvwr_manager_view.xml',
        'views/production_order_vin.xml',
        'views/invoice_title_generator.xml',
        'report/vin_generator_title_report_templates.xml',
        'report/vin_generator_title_report.xml',
        'views/product_gvwr_view.xml',
        'views/product_product_gvwr.xml',
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    
}