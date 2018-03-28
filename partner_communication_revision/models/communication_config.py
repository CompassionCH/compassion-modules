# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class CommunicationConfig(models.Model):
    _inherit = 'partner.communication.config'

    revision_number = fields.Float(default=1.0, readonly=True)
    revision_date = fields.Date(default=fields.Date.today(), readonly=True)
    revision_ids = fields.One2many(
        'partner.communication.revision', 'config_id', 'Revisions'
    )
