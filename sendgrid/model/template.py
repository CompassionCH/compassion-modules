# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api
from openerp.tools.config import config

import json
import sendgrid
from ..tools import sendgrid_templates



class Template(models.Model):
    """ Reference to a template available on the SendGrid user account. """
    _name = 'sendgrid.template'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char()
    remote_id = fields.Char()

    @api.one
    def update(self):
        # TODO: remove duplication
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise exceptions.Warning(
                'ConfigError',
                _('Missing sendgrid_api_key in conf file'))

        client = sendgrid.SendGridAPIClient(api_key)
        template_client = sendgrid_templates.Templates(client)
        status, msg = template_client.get()
        result = json.loads(msg)

        # TODO: handle error if dict does not have expected structure?
        for template in result["templates"]:
            id = template["id"]
            name = template["name"]
            record = self.search([('remote_id', '=', id)])
            if record:
                record.name = name
            else:
                self.create({
                    "remote_id": id,
                    "name": name,
                })
