# The origins of an event take the campaign of the event (new campaign_id of
# the origin), which their sponsorships without campaign then take.
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return
    openupgrade.logged_query(
        cr,
        """
        UPDATE recurring_contract_origin o
        SET campaign_id = e.campaign_id
        FROM crm_event_compassion e
        WHERE e.id = o.event_id
            AND e.campaign_id IS NOT NULL
            AND o.campaign_id IS NULL
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE recurring_contract c
        SET campaign_id = o.campaign_id
        FROM recurring_contract_origin o
        WHERE o.id = c.origin_id
            AND o.campaign_id IS NOT NULL
            AND c.campaign_id IS NULL
        """,
    )
