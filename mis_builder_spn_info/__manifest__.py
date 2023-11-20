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
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "mis_builder",  # OCA/mis_builder
        "account",  # source
        "sponsorship_compassion",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/res_config_settings_view.xml",
    ],
    # only loaded in demonstration mode
}
