# -*- coding: utf-8 -*-
{
    'name': "Weight Calculation",

    'summary': """
        Weight""",

    'description': """
        Calculates Weight for trailer based in BOM'S
    """,

    'author': "Obed David Cano Mendez",
    'website': "http://www.horizontrailers.com",
    'sequence': 3,

    'version': '1.0',

    'depends': ['base','product','mrp',],

    'data': [
        'views/calculate_weight_product_product.xml',
        'views/calculate_weight_product_template.xml',
        'views/calculate_percentage.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}