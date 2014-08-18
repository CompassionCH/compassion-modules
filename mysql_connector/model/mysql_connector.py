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

import MySQLdb as mdb
import logging


class mysql_connector:
    """ Contains all the utility methods needed to talk with a MySQL server
    which connection settings are stored in the object mysql.config.settings. """
    
    def __init__(self, cr, uid, settings_obj):
        """ Establishes the connection to the MySQL server used by GP. 
            Args:
                - settings_obj : a reference to the 'mysql.config.settings' object
                - cr : a database cursor to the Postgres database of OpenERP.
                - uid : OpenERP user id. """
        settings = settings_obj.default_get(cr, uid, ['default_mysql_host','default_mysql_db','default_mysql_user','default_mysql_pw'])
        self._con = False
        if settings:
            try:
                self._con = mdb.connect(settings['default_mysql_host'], settings['default_mysql_user'], settings['default_mysql_pw'], settings['default_mysql_db']);
                self._cur = self._con.cursor(mdb.cursors.DictCursor)
            except mdb.Error, e:
                logging.debug("Error %d: %s" % (e.args[0],e.args[1]))
        else:
            raise Exception("No settings found")

    def __del__(self):
        """ Close the MySQL connection. """
        if self._con:
            self._con.close()
            
    def query(self, statement, args=None):
        """ Performs a MySQL query that has no return value. 
            Args:
                - statement (string) : the query to be executed.
                - args (list or dictionnary) : the arguments of the query. If args is a sequence, then %s must be used as the parameter placeholder in the query. If a mapping is used, %(key)s must be used as the placeholder. 
            Returns:
                - long integer rows affected, if any.
        """
        with self._con:
            return self._cur.execute(statement, args)
            
    def selectOne(self, statement, args=None):
        """ Performs a MySQL SELECT statement and returns one single row.
            Args:
                - statement (string) : the query to be executed.
                - args (list or dictionnary) : the arguments of the query. If args is a sequence, then %s must be used as the parameter placeholder in the query. If a mapping is used, %(key)s must be used as the placeholder. 
            Returns :
                - Dictionary containing the selected field names as keys with their values. 
                ex : {'SELECT_1':'VALUE_1', ... , 'SELECT_N':'VALUE_N'}
                - None if the query didn't return a result.
        """
        with self._con:
            self._cur.execute(statement, args)
            if self._cur.rowcount > 0:
                return self._cur.fetchone()
                
    def selectAll(self, statement, args=None):
        """ Performs a MySQL SELECT statement and returns all rows.
            Args:
                - statement (string) : the query to be executed.
                - args (list or dictionnary) : the arguments of the query. If args is a sequence, then %s must be used as the parameter placeholder in the query. If a mapping is used, %(key)s must be used as the placeholder. 
            Returns :
                - List of dictionaries containing the selected field names as keys with their values. 
                ex : [{'SELECT_1':'VALUE_1', ... , 'SELECT_N':'VALUE_N'},{'SELECT_1':'VALUE_1_2', ... , 'SELECT_N':'VALUE_N_2'}, ...]
                - Empty list if the query didn't return a result.
        """
        with self._con:
            self._cur.execute(statement, args)
            if self._cur.rowcount > 0:
                return self._cur.fetchall()
                
        return list()
        
    def is_alive(self):
        """ Test if the connection is alive. """
        try:
            self.selectOne("SELECT VERSION()")
            return True
        except Exception, e:
            return False
        