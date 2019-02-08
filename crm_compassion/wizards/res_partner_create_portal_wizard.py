# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models, fields, _


class ResPartnerCreatePortalWizard(models.TransientModel):
    """ creation of a portal user wizard will send a email
        with the identifier if the user used the checkbox """
    _name = 'res.partner.create.portal.wizard'
    _description = 'take a partner and make it a odoo user'

    send_communication = fields.Boolean(
        _('do you want to send a mail with '
          'the login link to the user ?'), default=True)

    config_id = fields.Many2one(
        'partner.communication.config', _('choose a communication config'),
        domain="[('model', '=', 'res.users')]"
    )

    @api.multi
    def button_create_portal_user(self):
        portal = self.env['portal.wizard'].create({})
        portal.onchange_portal_id()
        users_portal = portal.mapped('user_ids')
        users_portal.write({'in_portal': True})
        no_mail = users_portal.filtered(lambda u: not u.email)
        for user in no_mail:
            partner = user.partner_id
            user.email = partner.firstname[0].lower() + \
                partner.lastname.lower() + '@cs.local'

        # define if needed to create a communication
        bool_uid_communication = (self.send_communication and self.config_id)

        ctx = {
            'create_uid_communication': bool_uid_communication,
            'config_id_id': self.config_id.id
        }
        portal.with_context(ctx).action_apply()
        no_mail.mapped('partner_id').write({'email': False})

        action = None
        if bool_uid_communication:
            # get same communication create in portal.action_apply()
            same_job_search = [
                ('partner_id', '=', users_portal.partner_id.id),
                ('config_id', '=', ctx['config_id_id']),
                ('config_id', '!=',
                 self.env.ref(
                     'partner_communication.default_communication'
                 ).id),
                ('state', 'in', ('call', 'pending'))]
            communication = self.env['partner.communication.job']\
                .search(same_job_search)

            action = {
                'name': communication.subject,
                'type': 'ir.actions.act_window',
                'res_model': 'partner.communication.job',
                'res_id': communication.id,
                'view_mode': 'form',
                'target': 'new'
            }
        return action

    @api.multi
    def button_cancel(self):
        return None
