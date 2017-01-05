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

import logging
import csv
import os

logger = logging.getLogger()

IMPORT_DIR = os.path.join(os.path.dirname(__file__)) + '/'


def migrate(cr, version):
    if not version:
        return

    logger.info("MIGRATION : LOADING CHILDREN GLOBAL IDS")
    with open(IMPORT_DIR + 'child_global_ids.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        # Skip header
        csvreader.next()
        for row in csvreader:
            cr.execute("""
                UPDATE compassion_child
                SET global_id = '{}'
                WHERE local_id = '{}'
            """.format(row[1], row[0]))

    logger.info("MIGRATION : LOADING SPONSOR GLOBAL IDS")
    with open(IMPORT_DIR + 'sponsor_global_ids.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        # Skip header
        csvreader.next()
        for row in csvreader:
            cr.execute("""
                UPDATE res_partner p
                SET global_id = '{}'
                WHERE ref = '{}'
                AND EXISTS(
                    SELECT category_id
                    FROM res_partner_res_partner_category_rel r
                    JOIN res_partner_category c
                    ON r.category_id = c.id
                    WHERE r.partner_id = p.id AND c.name LIKE '%Sponsor'
                )
            """.format(row[1], row[0]))

    logger.info("MIGRATION : LOADING SPONSORSHIP GLOBAL IDS")
    with open(IMPORT_DIR + 'sponsorship_ids.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        # Skip header
        csvreader.next()
        for row in csvreader:
            cr.execute("""
                SELECT id FROM compassion_child
                WHERE local_id = '{}';
            """.format(row[0]))
            child_id = cr.fetchone()
            child_id = child_id and child_id[0]
            cr.execute("""
                SELECT id FROM res_partner
                WHERE ref = '{}' AND parent_id is NULL AND has_sponsorships
                = TRUE;
            """.format(row[1]))
            sponsor_id = cr.fetchone()
            sponsor_id = sponsor_id and sponsor_id[0]
            if child_id and sponsor_id:
                cr.execute("""
                    UPDATE recurring_contract
                    SET global_id = %s
                    WHERE child_id = %s AND correspondant_id = %s
                    AND state NOT IN ('cancelled', 'terminated')
                """, (row[2], child_id, sponsor_id))

    # Update partner preferred names
    cr.execute("""
    UPDATE res_partner SET preferred_name = COALESCE(firstname, name)
    """)
