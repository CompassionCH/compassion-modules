# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    partners = env['res.partner'].search_count(
            [('global_id', '!=', False),
             ('title.gender', '!=', False),
             ('title.name', 'not in', [
                 'Madam', 'Mister', 'Misters', 'Ladies'])])
    _logger.warning("Found %s partners to migrate gender on GMC. Don't forget "
                    "to call upsert_constituent method on those.", partners)
    # partners.upsert_constituent()
