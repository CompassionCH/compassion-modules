{
    "name": "mis_builder_spn_info",
    "summary": """
        Info on aquisition and departure to report on spn evolution
        """,
    "description": """
        In order for the report to display,
        two accounts needs to be created (in each company if multiple) of equity type.
        with the names:
        - Sponsorships
        - Child Sponsored
    """,
    "author": "Compassion Suisse",
    "website": "https://www.compassion.ch",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml  # noqa: B950
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "mis_builder",  # OCA/mis_builder
        "account",  # source
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
    ],
    # only loaded in demonstration mode
}
