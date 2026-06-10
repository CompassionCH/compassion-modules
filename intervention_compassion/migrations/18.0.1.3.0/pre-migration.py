from openupgradelib import openupgrade


def migrate(cr, version):
    cr.execute(
        """
    SELECT id
        FROM gmc_action_connect
            WHERE connect_schema='http://schemas.ci.org/ci/messaging/availability/2025/06/InterventionReservationConvertedToHoldNotification'
                """
    )
    res_id = cr.fetchone()
    if res_id:
        openupgrade.add_xmlid(
            cr,
            "intervention_compassion",
            "intervetion_to_hold_connect",
            "gmc.action.connect",
            res_id[0],
        )
    cr.execute(
        """
        SELECT id
        FROM gmc_action_connect
        WHERE connect_schema =
              'http://schemas.ci.org/ci/messaging/availability/2025/02/ReservationExpiredNotification'
        """
    )
    res_id = cr.fetchone()
    if res_id:
        openupgrade.add_xmlid(
            cr,
            "intervention_compassion",
            "expiration_reservation_connect",
            "gmc.action.connect",
            res_id[0],
        )
    # Remove duplicate mappings
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM compassion_mapping
        WHERE model_id = (
            SELECT id FROM ir_model WHERE model = 'compassion.global.intervention')
    """,
    )
