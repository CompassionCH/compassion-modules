# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class EmailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    body = fields.Html(sanitize=False)

    @api.model
    def create_emails(self, template, res_ids, default_mail_values=None):
        """ Helper to generate a new e-mail given a template and objects.

        :param int template: mail.template record
        :param res_ids: ids of the resource objects
        :return: browse records of created e-mails (one per resource object)
        """
        all_mail_values = self._get_mail_values(template, res_ids)
        email_obj = self.env['mail.mail']
        emails = email_obj
        for res_id in res_ids:
            mail_values = all_mail_values[res_id]
            if default_mail_values:
                mail_values.update(default_mail_values)

            if mail_values.get('body_html'):
                mail_values['body'] = mail_values['body_html']
            emails += email_obj.create(mail_values)
        return emails

    @api.model
    def get_generated_fields(self, template, res_ids):
        """ Helper to retrieve generated html given a template and objects.

        :param int template: mail.template record
        :param res_ids: ids of the resource objects
        :return: html code generated for the e-mail (list if len(res_ids)>1)
        """
        all_mail_values = self._get_mail_values(template, res_ids)
        email_fields = list()
        for res_id in res_ids:
            email_fields.append(all_mail_values[res_id])
        if len(email_fields) == 1:
            email_fields = email_fields[0]
        return email_fields

    def _get_mail_values(self, template, res_ids):
        """ Helper to get e-mail values given a template and objects.

        :param int template: mail.template record
        :param res_ids: ids of the resource objects
        :return: list of dictionaries containing e-mail values
        """
        if not isinstance(res_ids, list):
            res_ids = [res_ids]
        wizard = self.sudo().with_context(active_ids=res_ids).create({
            'template_id': template.id,
            'composition_mode': 'mass_mail',
            'model': template.model,
            'author_id': self.env.user.partner_id.id,
        })
        # Fetch template values.
        wizard.write(
            wizard.onchange_template_id(
                template.id, 'mass_mail', False, False)['value'])
        return wizard.get_mail_values(res_ids)
