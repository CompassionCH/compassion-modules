# -*- coding: utf-8 -*-

#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>


from odoo import models, fields


class RequestType(models.Model):
    _inherit = 'crm.claim.type'

    template_id = fields.Many2one('mail.template',
                                  'Template',
                                  domain="[('model_id', '=', 'crm.claim')]")
