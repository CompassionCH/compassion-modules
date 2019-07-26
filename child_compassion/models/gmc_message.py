##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from odoo import models, fields

logger = logging.getLogger(__name__)


class GmcMessage(models.Model):
    """ Add child in messages. """
    _inherit = 'gmc.message'

    child_id = fields.Many2one('compassion.child', 'Child')
