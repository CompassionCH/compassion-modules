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

from openerp import models, api


class EmailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def create_emails(self, template, res_ids, default_mail_values=None):
        """ Helper to generate a new e-mail given a template and objects.

        :param int template: email.template record
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
            emails += email_obj.create(mail_values)
        return emails

    @api.model
    def get_generated_html(self, template, res_ids):
        """ Helper to generate a new e-mail given a template and objects.

        :param int template: email.template record
        :param res_ids: ids of the resource objects
        :return: html code generated for the e-mail (list if len(res_ids)>1)
        """
        all_mail_values = self._get_mail_values(template, res_ids)
        email_bodies = list()
        for res_id in res_ids:
            email_bodies.append(all_mail_values[res_id]['body_html'])
        if len(email_bodies) == 1:
            email_bodies = email_bodies[0]
        return email_bodies

    @api.model
    def get_generated_subject(self, template, res_ids):
        """ Helper to get the generated subject of an e-mail template.

        :param int template: email.template record
        :param res_ids: ids of the resource objects
        :return: html code generated for the e-mail (list if len(res_ids)>1)
        """
        all_mail_values = self._get_mail_values(template, res_ids)
        email_bodies = list()
        for res_id in res_ids:
            email_bodies.append(all_mail_values[res_id]['subject'])
        if len(email_bodies) == 1:
            email_bodies = email_bodies[0]
        return email_bodies

    def _get_mail_values(self, template, res_ids):
        """ Helper to get e-mail values given a template and objects.

        :param int template: email.template record
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
            'notification': True,
            'auto_delete': True,
        })
        # Fetch template values.
        wizard.write(
            wizard.onchange_template_id(
                template.id, 'mass_mail', False, False)['value'])
        return self.get_mail_values(wizard, res_ids)

    @api.multi
    def send_mail(self):
        """ Return to e-mails generated. """
        super(EmailComposeMessage, self).send_mail()
        mail_ids = self.env['mail.mail'].search([
            ('res_id', 'in', self.env.context.get('active_ids', [])),
            ('model', '=', self.env.context.get('active_model'))
        ])
        if mail_ids:
            return {
                'name': 'E-mails',
                'view_mode': 'form,tree',
                'view_type': 'form',
                'domain': [('id', 'in', mail_ids.ids)],
                'res_model': 'mail.mail',
                'res_id': mail_ids.ids[0],
                'type': 'ir.actions.act_window',
            }
        return True
