# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from mysql_connector.model.mysql_connector import mysql_connector

class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """
                
    def pushPassword(self, id, value):
        """ Push the password of a OpenERP user to GP. """
        return self.query("UPDATE login SET ERP_PWD = AES_ENCRYPT(%s, SHA2('gpT0ErpP455w0rd!',512)) WHERE ERP_ID = %s", (value,id))