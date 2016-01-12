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

from openerp import models, fields, _


class TemplateList(models.Model):
    _name = 'sponsorship.templatelist'

    lang = fields.Char()
    template_id = fields.Many2one('sendgrid.template')
