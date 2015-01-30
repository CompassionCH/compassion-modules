# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from mysql_connector.model.mysql_connector import mysql_connector
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """

    # Mapping for child transfers to exit_reason_code in GP
    transfer_mapping = {
        'AU': '15',
        'CA': '16',
        'DE': '17',
        'ES': '38',
        'FR': '18',
        'GB': '20',
        'IT': '19',
        'KR': '37',
        'NL': '35',
        'NZ': '40',
        'US': '21',
    }

    def upsert_child(self, uid, child):
        """Push or update child in GP after converting all relevant
        information in the destination structure."""
        vals = dict()
        return self.upsert("Enfants", vals)
        
    def upsert_case_study(self, uid, case_study):
        """Push or update Case Study in GP."""
        vals = dict()
        return self.upsert("Fichiersenfants", vals)

    def set_child_sponsor_state(self, child):
        update_string = "UPDATE Enfants SET %s WHERE code='%s'"
        update_fields = "situation='{}'".format(child.state)
        if child.sponsor_id:
            update_fields += ", codega='{}'".format(child.sponsor_id.ref)

        if child.state == 'F':
            # If the child is sponsored, mark the sponsorship as terminated in
            # GP and set the child exit reason in tables Poles and Enfant
            end_reason = child.gp_exit_reason or \
                self.transfer_mapping[child.transfer_country_id.code]
            update_fields += ", id_motif_fin={}".format(end_reason)
            # We don't put a child transfer in ending reason of a sponsorship
            if not child.transfer_country_id:
                pole_sql = "UPDATE Poles SET TYPEP = IF(TYPEP = 'C', " \
                           "'A', 'F'), id_motif_fin={}, datefin=curdate() " \
                           "WHERE codespe='{}' AND TYPEP NOT IN " \
                           "('F','A')".format(end_reason, child.code)
                logger.info(pole_sql)
                self.query(pole_sql)

        if child.state == 'P':
            # Remove delegation and end_reason, if any was set
            update_fields += ", datedelegue=NULL, codedelegue=''" \
                             ", id_motif_fin=NULL"

        sql_query = update_string % (update_fields, child.code)
        logger.info(sql_query)
        return self.query(sql_query)
        
    