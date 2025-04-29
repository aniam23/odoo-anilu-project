# -*- coding: utf-8 -*-
{
    'name': "mm_horizon",

    'summary': """
        Modulo personalizado para horizon trailers""",

    'description': """
        Modulo personalizado para horizon trailers
    """,

    'author': "Mit-Mut",
    'website': "https://www.mit-mut.com/",
    'license': 'OPL-1',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/inherit_product_tmp.xml',
        'views/inherit_purchase_order.xml',
        'views/report_purchase.xml',
        'views/report_template.xml',
        'views/report_order_template.xml',
        #'views/templates.xml',
    ],
}
