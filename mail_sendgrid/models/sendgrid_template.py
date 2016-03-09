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

import json
import sendgrid
import re

from openerp import models, fields, api, exceptions, _
from openerp.tools.config import config

from ..tools import sendgrid_templates


class SendgridTemplate(models.Model):
    """ Reference to a template available on the SendGrid user account. """
    _name = 'sendgrid.template'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char()
    remote_id = fields.Char(readonly=True)
    html_content = fields.Html(readonly=True)
    plain_content = fields.Text(readonly=True)
    detected_keywords = fields.Char(compute='_compute_keywords')

    def _compute_keywords(self):
        for template in self:
            if template.html_content:
                keywords = template.get_keywords()
                self.detected_keywords = ';'.join(keywords)

    @api.one
    def update(self):
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
            status, msg = template_client.get(id)
            template_versions = json.loads(msg)['versions']
            template_vals = template_versions[0]
            for version in template_versions:
                if version['active']:
                    template_vals = version
            vals = {
                "remote_id": id,
                "name": template["name"],
                "html_content": template_vals["html_content"],
                "plain_content": template_vals["plain_content"],
            }
            record = self.search([('remote_id', '=', id)])
            if record:
                record.write(vals)
            else:
                self.create(vals)

    def get_keywords(self):
        """ Search in the Sendgrid template for keywords included with the
        following syntax: {keyword_name} and returns the list of keywords.
        keyword_name shouldn't be longer than 20 characters.
        You can replace the substitution prefix and suffix by adding values
        in the system parameters
            - mail_sendgrid.substitution_prefix
            - mail_sendgrid.substitution_suffix
        """
        self.ensure_one()
        params = self.env['ir.config_parameter']
        prefix = params.search([
            ('key', '=', 'mail_sendgrid.substitution_prefix')
        ]).value or '{'
        suffix = params.search([
            ('key', '=', 'mail_sendgrid.substitution_suffix')
        ]) or '}'
        pattern = prefix + '.{0,20}' + suffix
        return list(set(re.findall(pattern, self.html_content)))
