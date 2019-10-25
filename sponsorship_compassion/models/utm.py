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


class UtmMedium(models.Model):
    _inherit = 'utm.medium'

    type = fields.Selection([
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
    ], default='manual')
