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
from openerp import models, fields


class MailMessage(models.Model):
    """ Add relation to communication configuration to track generated
    e-mails.
    """
    _inherit = 'mail.mail'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    communication_config_id = fields.Many2one('partner.communication.config')
