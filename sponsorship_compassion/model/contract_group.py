# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import time

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import mod10r
from openerp import netsvc

import pdb

class contract_group(orm.Model):
    ''' Add BVR on groups and add BVR ref and analytics_id
    in invoices '''
    _inherit = 'recurring.contract.group'
    