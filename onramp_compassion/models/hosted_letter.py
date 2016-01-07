# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import uuid
from openerp import models, fields, api, _


class HostedLetter(models.Model):
    _name = 'sponsorship.hostedletter'

    letter_file = fields.Many2one('ir.attachment', required=True)
    uuid = fields.Char(required=True, default=str(uuid.uuid4()))
