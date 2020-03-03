from openupgradelib import openupgrade


def migrate(cr, version):
    # Move date formats that were in child_switzerland
    openupgrade.rename_xmlids(cr, [
        ('child_switzerland.date_short_en', 'advanced_translation.date_short_en'),
        ('child_switzerland.date_month_en', 'advanced_translation.date_month_en'),
        ('child_switzerland.date_full_en', 'advanced_translation.date_full_en'),
    ])
