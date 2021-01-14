# -*- coding: utf-8 -*-
{
    'name': "res_country_statistics",

    'summary': """
        Add some statistical indicator retrieve from the world bank""",

    'description': """
        the following indicator will be retrive from the world bank
        
    """,

    'author': "Compassion Suisse",
    'website': "http://www.compassion.cch",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}