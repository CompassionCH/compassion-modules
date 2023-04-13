# -*- coding: utf-8 -*-
{
    'name': "mis_builder_spn_info",

    'summary': """
        Info on aquisition and departure to report on spn evolution
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Compassion Suisse",
    'website': "http://www.compassion.ch",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        "mis_builder",  # OCA/mis_builder
        "account",  # source
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
}
