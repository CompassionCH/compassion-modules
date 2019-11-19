##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, fields


class GlobalPartner(models.Model):
    _name = 'compassion.global.partner'
    _inherit = 'compassion.mapped.model'
    _description = 'Compassion Global Partner'

    name = fields.Char(required=True)
    country_id = fields.Many2one('res.country', 'Country')
    code = fields.Char(related='country_id.code', store=True)
