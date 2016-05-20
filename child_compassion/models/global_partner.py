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


class GlobalPartner(models.Model):
    _name = 'compassion.global.partner'

    name = fields.Char(required=True)
    country_id = fields.Many2one('res.country', 'Country')
