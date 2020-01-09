# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'

    interaction_resume_ids = fields.One2many(
        'interaction.resume', 'partner_id', 'Interaction resume')

    # Do not clutter the mail thread with emails that can be seen in
    # interaction resume
    message_ids = fields.One2many(
        'mail.message', 'res_id', string='Messages', domain=lambda self: [
            ('model', '=', self._name),
            ('subtype_id', 'in', [self.env.ref('mail.mt_note').id])
        ], auto_join=True)

    @api.multi
    def _compute_comm_count(self):
        # Only count pending communications
        for partner in self:
            partner.communication_count = self.env[
                'partner.communication.job'].search_count([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ('pending', 'call')),
                ])

    @api.multi
    def open_events(self):
        event_ids = self.env['crm.event.compassion'].search(
            [('partner_id', 'child_of', self.ids)]).ids

        return {
            'name': _('Events'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.event.compassion',
            'target': 'current',
            'domain': [('id', 'in', event_ids)],
        }

    @api.multi
    def create_odoo_user(self):
        portal = self.env['portal.wizard'].create({})
        portal.onchange_portal_id()
        users_portal = portal.mapped('user_ids')
        users_portal.write({'in_portal': True})
        res = portal.action_apply()

        return res

    @api.multi
    def _compute_opportunity_count(self):
        super(Partner, self)._compute_opportunity_count()
        for partner in self:
            operator = 'child_of' if partner.is_company else '='
            partner.opportunity_count += self.env['crm.lead'].search_count(
                [('partner_id', operator, partner.id),
                 ('type', '=', 'opportunity'), ('active', '=', False)])

    def open_interaction(self):
        """
        Populates data for interaction resume and open the view
        :return: action opening the view
        """
        self.ensure_one()
        self.env['interaction.resume'].populate_resume(self.id)
        partners_with_same_email_ids = self.env['res.partner'].search([
            ('email', '=', self.email)
        ]).mapped("id")
        return {
            'name': _('Interaction resume'),
            'type': 'ir.actions.act_window',
            'res_model': 'interaction.resume',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('partner_id', 'in', partners_with_same_email_ids)],
            'target': 'current',
        }

    @api.multi
    def log_call(self):
        """ Prepare crm.phonecall creation. """
        self.ensure_one()
        action_ctx = self.env.context.copy()
        action_ctx.update({
            'default_state': 'done',
            'default_partner_id': self.id,
            'default_partner_mobile': self.mobile,
            'default_partner_phone': self.phone,
        })
        domain = [('partner_id', '=', self.id)]

        return {
            'name': _('Log your call'),
            'domain': domain,
            'res_model': 'crm.phonecall',
            'view_mode': 'form,tree,calendar',
            'type': 'ir.actions.act_window',
            'nodestroy': False,  # close the pop-up wizard after action
            'target': 'new',
            'context': action_ctx,
        }
