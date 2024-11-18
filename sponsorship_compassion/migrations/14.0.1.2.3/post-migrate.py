import logging

from openupgradelib.openupgrade import migrate

_logger = logging.getLogger(__name__)


@migrate()
def migrate(env, version):
    env["recurring.contract"].fix_inconsistent_SWP_contracts()
