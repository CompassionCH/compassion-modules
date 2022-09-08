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
    _name = "import.letter.config"
    _inherit = "correspondence.metadata"
    _description = "S2B Letter Import Config"

    name = fields.Char()
