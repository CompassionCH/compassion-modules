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


class ImportConfig(models.Model):
    """ This class defines all metadata of a correspondence"""

    _name = 'import.letter.config'
    _inherit = 'correspondence.metadata'

    name = fields.Char()
    is_encourager = fields.Boolean('Encourager')

    def get_fields(self):
        res = super().get_fields()
        res.append('is_encourager')
        return res
