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
from openerp import models, fields


class HostedLetter(models.Model):
    _name = 'sponsorship.hostedletter'

    letter_file = fields.Many2one('ir.attachment', required=True)
    uuid = fields.Char(required=True, default=lambda self: self._get_uuid())
    read_url = fields.Char(compute='_get_read_url')
    last_read = fields.Datetime()
    read_count = fields.Integer()

    def _get_read_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        self.read_url = "{}/b2s_image?id={}".format(base_url, self.uuid)

    def _get_uuid(self):
        return str(uuid.uuid4())
