from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Pre-migration script for 14.0.1.4.0.
    Sets country_id to NULL in res_partner and payment_transaction
    for countries with NULL code, to avoid foreign key issues.
    """
    cr = env.cr
    cr.execute(
        """
        UPDATE res_partner
        SET country_id = NULL
        WHERE country_id IN (
            SELECT id FROM res_country WHERE code IS NULL
        );
    """
    )
    cr.execute(
        """
        UPDATE payment_transaction
        SET partner_country_id = 44  -- Switzerland (CH)
        WHERE partner_country_id IN (
            SELECT id FROM res_country WHERE code IS NULL
        );
    """
    )
    cr.execute(
        """
        DELETE FROM res_country
        WHERE code IS NULL;
    """
    )
    cr.execute(
        "delete from res_lang_compassion where name = 'English' and code_iso IS NULL;"
    )
    # Add new Field Offices
    new_office_codes = ["KH", "MW", "MM", "ZM"]
    cr.execute(
        "SELECT field_office_id, id FROM compassion_field_office "
        "WHERE field_office_id IN %s",
        (tuple(new_office_codes),),
    )
    for row in cr.fetchall():
        openupgrade.add_xmlid(
            cr,
            "child_compassion",
            f"field_office_{row[0].lower()}",
            "compassion.field.office",
            row[1],
        )
