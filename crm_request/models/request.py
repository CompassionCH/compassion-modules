# -*- coding: utf-8 -*-45.00
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from email.utils import parseaddr
from odoo import api, fields, models, exceptions, _


class CrmClaim(models.Model):
    _inherit = "crm.claim"
    _description = "Request"

    date = fields.Datetime(string='Date', readonly=True, index=False)
    name = fields.Char(compute='_compute_name', store=True)
    subject = fields.Char(required=True)
    alias_id = fields.Many2one(
        'mail.alias', 'Alias',
        help="The destination email address that the contacts used.")
    code = fields.Char(string='Number')
    claim_type = fields.Many2one(string='Type')
    user_id = fields.Many2one(string='Assign to')
    stage_id = fields.Many2one(group_expand='_read_group_stage_ids')
    ref = fields.Char(related='partner_id.ref')
    color = fields.Integer('Color index', compute='_compute_color')

    @api.depends('subject')
    @api.multi
    def _compute_name(self):
        for rd in self:
            rd.name = u'{} - {}'.format(rd.code, rd.subject)

    def _compute_color(self):
        for request in self:
            if int(request.priority) == 2:
                request.color = 2

    @api.multi
    def action_reply(self):
        """
        This function opens a window to compose an email, with the default
        template message loaded by default"""
        self.ensure_one()

        if not self.partner_id:
            raise exceptions.UserError(_(
                "You can only reply if you set the partner."
            ))
        template_id = self.claim_type.template_id.id
        ctx = {
            'default_model': 'crm.claim',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }

        if self.partner_id:
            partner = self._get_partner_alias(
                self.partner_id, parseaddr(self.email_from)[1]
            )
            ctx['default_partner_ids'] = [partner.id]

            # Un-archive the email_alias so that a mail can be sent and set a
            # flag to re-archive them once the email is sent.
            if partner.contact_type == 'attached' and not partner.active:
                ctx['unarchived_partners'] = [partner.id]
        else:
            ctx['claim_no_partner'] = True

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }

    def _get_partner_alias(self, partner, email):
        if partner.email != email:
            for partner_alias in partner.other_contact_ids:
                if partner_alias.email == email:
                    return partner_alias
            # No match is found
            raise exceptions.Warning(
                _('No partner aliases match: %s !') % email
            )
        else:
            return partner

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Unlink the email_from field from the partner"""
        if self.partner_id:
            self.partner_phone = self.partner_id.phone

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([('active', '=', True)], order=order)
        return stages.browse(stage_ids)

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    @api.model
    def message_new(self, msg, custom_values=None):
        """ Use the html of the mail's body instead of html converted in text
        """
        if custom_values is None:
            custom_values = {}

        alias_char = parseaddr(msg.get('to'))[1].split('@')[0]
        alias = self.env['mail.alias'].search(
            [['alias_name', '=', alias_char]])

        # Find the corresponding type
        subject = msg.get('subject')
        type_ids = self.env['crm.claim.type'].search(
            [('keywords', '!=', False)])
        type_id = False
        for record in type_ids:
            if any(word in subject for word in record.get_keys()):
                type_id = record.id
                break

        defaults = {
            'date': msg.get('date'),  # Get the time of the sending of the mail
            'alias_id': alias.id,
            'claim_type': type_id,
            'subject': subject
        }

        if 'partner_id' not in custom_values:
            match_obj = self.env['res.partner.match']
            options = {'skip_create': True}
            partner = match_obj.match_partner_to_infos({
                'email': parseaddr(msg.get('from'))[1]
            }, options)
            if partner:
                defaults['partner_id'] = partner.id

        defaults.pop('name', False)

        defaults.update(custom_values)
        return super(CrmClaim, self).message_new(msg, defaults)

    @api.multi
    def message_update(self, msg_dict, update_vals=None):
        """Change the stage to "Waiting on support" when the customer write a
           new mail on the thread
        """
        result = super(CrmClaim, self).message_update(msg_dict, update_vals)
        for request in self:
            request.stage_id = self.env[
                'ir.model.data'].get_object_reference(
                'crm_request', 'stage_wait_support')[1]
        return result

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, **kwargs):
        """Change the stage to "Waiting on customer" when the employee answer
           to the supporter
        """
        result = super(CrmClaim, self).message_post(**kwargs)

        if 'mail_server_id' in kwargs:
            for request in self:
                ir_data = self.env['ir.model.data']
                request.stage_id = ir_data.get_object_reference(
                    'crm_request', 'stage_wait_customer')[1]
                request.user_id = self.env.user

        return result

    @api.multi
    def write(self, values):
        """
        - If move request in stage 'In Progress' assign the request to the
          current user.
        - Push partner to associated mail messages
        """
        if values.get('stage_id') == self.env.ref('crm_claim.stage_claim5').id:
            values['user_id'] = self.env.uid
        super(CrmClaim, self).write(values)
        if values.get('partner_id'):
            for request in self:
                request.message_ids.filtered(
                    lambda m: m.email_from == request.email_from
                ).write({
                    'author_id': values['partner_id']
                })
        return True


class AssignRequestWizard(models.TransientModel):
    _name = 'assign.request.wizard'
    user_id = fields.Many2one('res.users', 'Assign to',
                              default=lambda self: self.env.user,)
    intern_note = fields.Text('Internal note')

    @api.multi
    def assign_to(self):
        self.ensure_one()
        model = self.env.context.get('active_model')
        model_id = self.env.context.get('active_id')
        request = self.env[model].browse(model_id)
        request.user_id = self.user_id
        if self.intern_note:
            request.message_post(subject='Message for ' + self.user_id.name,
                                 body=self.intern_note)
