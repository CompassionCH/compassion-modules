##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api
import base64
import json


class ImportJsonMapping(models.TransientModel):
    _name = "import.json.mapping.wizard"
    _description = "Import GMC Mapping Wizard"

    file = fields.Binary()

    @api.multi
    def import_json_mapping(self):
        self.ensure_one()
        dec = str(base64.decodebytes(self.file), 'utf-8')
        data = json.loads(dec)
        return self.env['compassion.mapping'].create_from_json(data)
