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
        """
        Finds available children and try to put them on hold
        """
        logger.info("MIGRATION : Putting hold on available children")
        child_obj = self.env['compassion.child']
        hold = self.env['compassion.hold'].create({
                'name': 'Fake hold',
                'type': 'Consignment Hold'
        })
        self.env.cr.execute(
            'select id from compassion_child where to_migrate_r4 = true')
        child_ids = [r[0] for r in self.env.cr.fetchall()]
        available_children = child_obj.browse(child_ids)
        available_children.write({
            'hold_id': hold.id,
            'to_migrate_r4': False
        })
        # for child in available_children:
            # TODO Implement when holds are implemented
            # TODO Are children automatically put on hold for us?
            # TODO Should we also update information of children?
            # logger.info("nothing to do for this child.")

        return True
