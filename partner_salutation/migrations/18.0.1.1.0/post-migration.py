##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# Salutations offered on the public-facing forms by default. Curators adjust
# the set afterwards from the title list; this only sets the initial value.
DEFAULT_PUBLIC_TITLE_XMLIDS = [
    "base.res_partner_title_mister",
    "base.res_partner_title_madam",
]


def migrate(cr, version):
    """Set the initial value of res.partner.title.is_shown_on_public_forms.

    Runs once on the upgrade that introduces the field. Curators own the set
    from then on, and later upgrades leave their choices untouched.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    titles = env["res.partner.title"]
    for xmlid in DEFAULT_PUBLIC_TITLE_XMLIDS:
        title = env.ref(xmlid, raise_if_not_found=False)
        if title:
            titles |= title
    if titles:
        titles.is_shown_on_public_forms = True
        _logger.info(
            "Seeded is_shown_on_public_forms on default public titles: %s",
            titles.mapped("name"),
        )
