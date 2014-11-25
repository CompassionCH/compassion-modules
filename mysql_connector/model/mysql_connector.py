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

import MySQLdb as mdb
import logging
from openerp.tools.config import config


class mysql_connector:
    """ Contains all the utility methods needed to talk with a MySQL server
    which connection settings are stored in the object mysql.config.settings.
    """

    def __init__(self, cr, uid):
        """ Establishes the connection to the MySQL server used by GP.
            Args:
                - cr : a database cursor to the Postgres database of OpenERP.
                - uid : OpenERP user id. """
        mysql_host = config.get('mysql_host')
        mysql_user = config.get('mysql_user')
        mysql_pw = config.get('mysql_pw')
        mysql_db = config.get('mysql_db')
        self._con = False
        try:
            self._con = mdb.connect(mysql_host, mysql_user, mysql_pw,
                                    mysql_db)
            self._cur = self._con.cursor(mdb.cursors.DictCursor)
        except mdb.Error, e:
            logging.debug("Error %d: %s" % (e.args[0], e.args[1]))

    def __del__(self):
        """ Close the MySQL connection. """
        if self._con:
            self._con.close()

    def query(self, statement, args=None):
        """ Performs a MySQL query that has no return value.
        Args:
            - statement (string) : the query to be executed.
            - args (list or dict) : the arguments of the query. If args is a
                                    sequence, then %s must be used as the
                                    parameter placeholder in the query. If a
                                    mapping is used, %(key)s must be
                                    used as the placeholder.
        Returns:
            - long integer rows affected, if any, True otherwise.
        """
        with self._con:
            res = self._cur.execute(statement, args)
            if res == 0:
                res = True
            return res

    def selectOne(self, statement, args=None):
        """ Performs a MySQL SELECT statement and returns one single row.
        Args:
            - statement (string) : the query to be executed.
            - args (list or dict) : the arguments of the query. If args is a
                                    sequence, then %s must be used as the
                                    parameter placeholder in the query. If a
                                    mapping is used, %(key)s must be
                                    used as the placeholder.
        Returns :
            - Dictionary containing the selected field names as keys
              with their values.
              ex : {'SELECT_1':'VALUE_1', ... , 'SELECT_N':'VALUE_N'}
            - Empty dict if the query didn't return a result.
        """
        with self._con:
            self._cur.execute(statement, args)
            return self._cur.fetchone() or dict()

    def selectAll(self, statement, args=None):
        """ Performs a MySQL SELECT statement and returns all rows.
         Args:
            - statement (string) : the query to be executed.
            - args (list or dict) : the arguments of the query. If args is a
                                    sequence, then %s must be used as the
                                    parameter placeholder in the query. If a
                                    mapping is used, %(key)s must be
                                    used as the placeholder.
        Returns :
            - List of dictionaries containing the selected field names as keys
              with their values.
              ex : [{'SELECT_1':'VALUE_1', ... , 'SELECT_N':'VALUE_N'},
                    {'SELECT_1':'VALUE_1_2', ... , 'SELECT_N':'VALUE_N_2'},
                    ...]
            - Empty list if the query didn't return a result.
        """
        with self._con:
            self._cur.execute(statement, args)
            return self._cur.fetchall() or list()

    def is_alive(self):
        """ Test if the connection is alive. """
        try:
            self.selectOne("SELECT VERSION()")
            return True
        except Exception:
            return False
