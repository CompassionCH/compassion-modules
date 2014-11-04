# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from mysql_connector.model.mysql_connector import mysql_connector


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """

    def pushPassword(self, id, value):
        """ Push the password of a OpenERP user to GP. """
        return self.query("UPDATE login SET ERP_PWD = AES_ENCRYPT(%s, "
                          "SHA2('gpT0ErpP455w0rd!',512)) WHERE ERP_ID = %s",
                          (value, id))
