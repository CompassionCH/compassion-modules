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

from openerp.osv.orm import Model, fields
from openerp.tools import mod10r

logger = logging.getLogger(__name__)


class account_invoice(Model):

    ''' Inherit account.invoice in order to change BVR ref field type '''
    _inherit = "account.invoice"

    _columns = {
        # 'bvr_reference': fields.char("BVR REF.", size=32,)
    }
