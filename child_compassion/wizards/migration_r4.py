# -*- encoding: utf-8 -*-
#
#    Copyright (C)  Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    The licence is in the file __openerp__.py
#

import logging
from openerp import models, api


logger = logging.getLogger(__name__)


class MigrationR4(models.TransientModel):
    """ Perform migrations after upgrading the module
    """
    _name = 'migration.r4'

    @api.model
    def perform_migration(self):
        # Only execute migration for 8.0.1.4.1 -> 8.0.3.0
        child_compassion_module = self.env['ir.module.module'].search([
            ('name', '=', 'child_compassion')
        ])
        if child_compassion_module.latest_version == '8.0.1.4.1':
            self._perform_migration()
        return True

    def _perform_migration(self):
        """
        Finds available children and try to put them on hold
        """
        logger.info("MIGRATION : Putting hold on available children")
        hold = self.env['compassion.hold'].create({
                'name': 'Fake hold',
                'type': 'Consignment Hold'
        })
        available_children = self.env['compassion.child'].search([(
            'state', 'in', ['N', 'D', 'I']
        )])
        available_children.write({'hold_id': hold.id})
        # for child in available_children:
        # TODO Implement when holds are implemented
        # TODO Are children automatically put on hold for us?
        # logger.info("nothing to do for this child.")
