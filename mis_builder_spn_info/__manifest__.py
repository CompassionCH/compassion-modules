# pylint: disable=C8101
{
    "name": "mis_builder_spn_info",
    "summary": """
        Adds a product field used in Nordic MIS reports.
        This can be removed if the reports are adapted.
        """,
    "author": "Compassion CH",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "category": "Uncategorized",
    "version": "18.0.1.0.1",
    "license": "AGPL-3",
    "depends": [
        "mis_builder",  # OCA/mis_builder
        "mis_builder_budget",  # OCA/mis_builder
        "account",  # source
        "sponsorship_compassion",
    ],
    "data": [],
    "installable": True,
}
