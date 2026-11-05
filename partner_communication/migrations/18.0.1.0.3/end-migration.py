import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """
    The reports of our communications have no javascript, so wkhtmltopdf has
    nothing to wait for: a print delay of 0 makes each of them about 2 seconds
    faster. This is an end-migration so that all the modules are loaded, and it
    takes the reports from what the communications use, whatever module defines
    them (they may also have been added directly in the database), so that it
    works for any of our instances (Switzerland, Nordic, ...).
    """
    # Our code prints the reports of the communications by name: a report that
    # was duplicated from the UI (same report name) can be the one that is used,
    # so all the reports sharing the name of a report of the communications are
    # updated. Only the ones that still have the default value (-1) change, to
    # keep a value that someone would have set by hand.
    env.cr.execute(
        """
        UPDATE ir_act_report_xml
        SET print_delay = 0
        WHERE print_delay < 0 AND report_name IN (
            SELECT report_name FROM ir_act_report_xml WHERE id IN (
                SELECT report_id FROM partner_communication_config
                WHERE report_id IS NOT NULL
                UNION
                SELECT report_id FROM partner_communication_attachment
                WHERE report_id IS NOT NULL
            ) OR model IN (
                'partner.communication.job',
                'correspondence',
                'compassion.child',
                'recurring.contract',
                'crm.claim',
                'compassion.field.office'
            )
        )
        """
    )
    _logger.info(
        "Print delay set to 0 for %s reports of the communications", env.cr.rowcount
    )
