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
        if not isinstance(res_ids, list):
            res_ids = [res_ids]
        wizard = self.sudo().with_context(active_ids=res_ids).create({
            'template_id': template.id,
            'composition_mode': 'mass_mail',
            'model': template.model,
            'author_id': 111,   # Sent with user Emanuel Cino
        })
        # Fetch template values.
        wizard.write(
            wizard.onchange_template_id(
                template.id, 'mass_mail', False, False)['value'])
        all_mail_values = self.get_mail_values(wizard, res_ids)
        email_obj = self.env['mail.mail']
        emails = email_obj
        for res_id in res_ids:
            mail_values = all_mail_values[res_id]
            if default_mail_values:
                mail_values.update(default_mail_values)
            emails += email_obj.create(mail_values)
        return emails
