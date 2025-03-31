# -*- coding: utf-8 -*-
{
    'name': "Logistics Document Packages",

    'summary': """
        logistics_document_packages""",

    'description': """
       logistics module for document export process or orders sales
    """,

    'author': "Anilu Amado Aguero",
    'website': "http://www.horizontrailers.com",
    'sequence': 3,
    'category': 'All',
    'version': '1.0',

    'depends': ['sale','vin_generator'],
    'data': [
        'security/ir.model.access.csv',
        'views/main_view.xml',
        'views/model_hs7.xml',
        'views/freight_view.xml',
        'views/num_wheel_view.xml',
        'views/weights_view.xml',
        'views/send_view.xml',
        'views/sales_view.xml',
        'views/doc_views.xml',
        'report/packing_action.xml',
        'report/packing_template.xml',
        'report/HS7_template.xml',
        'report/HS7_action.xml',
        'report/factura_action.xml',
        'report/factura_template.xml',
        'report/all_mso_action.xml',
        'report/all_mso_template.xml',
        'report/decla_action.xml',
        'report/decla_template.xml',
        'report/mso_action.xml',
        'report/mso_template.xml',
        'report/packing_fact_action.xml',
        'report/packing_fac_template.xml',
     
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    
}