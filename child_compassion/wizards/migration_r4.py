# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import os
import csv
import logging
from openerp import models, api


logger = logging.getLogger(__name__)

IMPORT_DIR = os.path.join(os.path.dirname(__file__)) + '/../data/'


class MigrationR4(models.TransientModel):
    """ Perform migrations after upgrading the module
    """
    _name = 'migration.r4'

    @api.model
    def perform_migration(self):
        # Only execute migration for 8.0.1 -> 8.0.3.0
        child_compassion_module = self.env['ir.module.module'].search([
            ('name', '=', 'child_compassion')
        ])
        if child_compassion_module.latest_version == '8.0.1':
            self._perform_migration()
        return True

    def _perform_migration(self):
        """
        Finds available children and try to put them on hold
        """
        logger.info("MIGRATION : Putting hold on available children")
        hold_vals = {
            'type': 'Consignment Hold',
            'expiration_date': '2017-03-19 13:00:00',
            'state': 'active',
            'source_code': 'R4 freeze hold',
        }
        child_obj = self.env['compassion.child']
        hold_obj = self.env['compassion.hold']
        logger.info(IMPORT_DIR + 'ch_children_hold.csv')
        with open(IMPORT_DIR + 'ch_children_hold.csv', 'rb') as csvfile:
            csvreader = csv.reader(csvfile)
            # Skip header
            csvreader.next()
            for row in csvreader:
                child = child_obj.search([('code', '=', row[0])])
                if child:
                    hold_vals.update({
                        'child_id': child.id,
                        'hold_id': row[1],
                        'comments': child.delegated_comment
                    })
                    hold_vals['child_id'] = child.id
                    hold_vals['hold_id'] = row[1]
                    child.hold_id = hold_obj.create(hold_vals)
