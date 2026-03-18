import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Recompute the lifecycle state & date of an FCP project
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Fetch all projects:
    projects = env["compassion.project"].search([])

    # Invalidate cache
    projects.invalidate_cache(["last_lifecycle_id", "status", "suspension"])

    projects._compute_last_lifecycle()
    projects._compute_suspension()

    _logger.info("Successfully recomputed lifecycle states for %s FCPs.", len(projects))
