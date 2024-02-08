{
    "name": "mis_builder_spn_info",
    "summary": """
        Info on aquisition and departure to report on spn evolution
        """,
    "author": "Compassion Switzerland",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "category": "Uncategorized",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
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
