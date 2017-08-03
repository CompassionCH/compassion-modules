# -*- coding: utf-8 -*-
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
import simplejson
import os
import sys

from odoo.netsvc import DBFormatter

ONRAMP_LOGGER = logging.getLogger('ONRAMP')

_logger_init = False


def init_logger():
    """ Add a new logger especially designed to log messages received and
    sent by the ramp.
    """
    global _logger_init
    if _logger_init:
        return
    _logger_init = True

    format = '%(asctime)s %(pid)s %(levelname)s %(dbname)s %(name)s: ' \
        '%(message)s'
    logf = 'log/odoo/onramp.log'
    handler = False
    try:
        # We check we have the right location for the log files
        dirname = os.path.dirname(logf)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=logf, when='D', interval=1, backupCount=30)
        formatter = DBFormatter(format)
        handler.setFormatter(formatter)

    except Exception:
        sys.stderr.write(
            "ERROR: couldn't create the logfile directory. "
            "Won't log ONRAMP to files.\n")
        return

    ONRAMP_LOGGER.setLevel(logging.INFO)
    ONRAMP_LOGGER.addHandler(handler)


init_logger()


def log_message(type, url, headers=None, message=None, session=None):
    if headers is None:
        headers = dict()
    if message is None:
        message = '{empty}'
    if session is not None:
        complete_headers = headers.copy()
        complete_headers.update(session.headers)
    else:
        complete_headers = headers
    ONRAMP_LOGGER.info(
        "[%s] %s %s %s",
        type,
        url,
        [(k, v) for k, v in complete_headers.iteritems()],
        simplejson.dumps(message))
