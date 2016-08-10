# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
import csv

logger = logging.getLogger()


def migrate(cr, version):
    if not version:
        return

    logger.info("MIGRATION : LOADING CHILDREN GLOBAL IDS")
    with open('child_global_ids.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        # Skip header
        csvreader.next()
        for row in csvreader:
            cr.execute("""
                UPDATE compassion_child
                SET global_id = '{}'
                WHERE compass_id = '{}'
            """.format(row[1], row[0]))

    logger.info("MIGRATION : LOADING SPONSOR GLOBAL IDS")
    with open('sponsor_global_ids.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        # Skip header
        csvreader.next()
        for row in csvreader:
            cr.execute("""
                UPDATE res_partner
                SET global_id = '{}'
                WHERE ref = '{}'
            """.format(row[1], row[0]))
