# -*- coding: utf-8 -*-45.00
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from email.utils import parseaddr
from odoo import api, fields, models, exceptions, _
from odoo.tools import config
from odoo.tools import html_sanitize

_logger = logging.getLogger(__name__)
try:
    import detectlanguage
except ImportError:
    _logger.warning("Please install detectlanguage")


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
    email_origin = fields.Char()
    language = fields.Selection('_get_lang')
    holiday_closure_id = fields.Many2one(
        'holiday.closure', 'Holiday closure', readonly=True)

    @api.depends('subject')
    @api.multi
    def _compute_name(self):
        for rd in self:
            rd.name = u'{} - {}'.format(rd.code, rd.subject)

    def _compute_color(self):
        for request in self:
            if int(request.priority) == 2:
                request.color = 2

    @api.model
    def _get_lang(self):
        langs = self.env['res.lang'].search([])
        return [(l.code, l.name) for l in langs]

    @api.multi
    def action_reply(self):
        """
        This function opens a window to compose an email, with the default
        template message loaded by default"""
        self.ensure_one()
        original_partner = self.partner_id

        if not original_partner:
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
            'lang': self.language,
        }

        if original_partner:
            alias_partner = self._get_partner_alias(
                original_partner, parseaddr(self.email_from)[1]
            )
            partner = alias_partner
            if alias_partner == original_partner:
                partner = original_partner
            self.partner_id = partner
            ctx['default_partner_ids'] = [partner.id]

            messages = self.mapped('message_ids').filtered(
                lambda m: m.body and (m.author_id == original_partner or
                                      partner in m.partner_ids))
            if messages:
                # Put quote of previous message in context for using in
                # mail compose message wizard
                message = messages.filtered(
                    lambda m: m.author_id == self.partner_id)[:1]
                if message:
                    ctx['reply_quote'] = message.get_message_quote()
                    ctx['message_id'] = message.id

            # Un-archive the email_alias so that a mail can be sent and set a
            # flag to re-archive them once the email is sent.
            if partner.contact_type == 'attached' and not partner.active:
                partner.toggle_active()
        else:
            ctx['claim_no_partner'] = True

        # Assign current user to request
        self.user_id = self.env.uid

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }

    def _get_partner_alias(self, partner, email):
        if email and partner.email != email:
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
        msg['body'] = html_sanitize(msg.get('body', ''))

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
            'subject': subject,
            'email_origin': msg.get('from'),
        }

        if 'partner_id' not in custom_values:
            match_obj = self.env['res.partner.match']
            options = {'skip_create': True}
            partner = match_obj.match_partner_to_infos({
                'email': parseaddr(msg.get('from'))[1]
            }, options)
            if partner:
                defaults['partner_id'] = partner.id
                defaults['language'] = partner.lang

        # Check here if the date of the mail is during a holiday
        mail_date = fields.Date.to_string(
            fields.Date.from_string(msg.get('date')))
        defaults['holiday_closure_id'] = self.env["holiday.closure"].search([
            ('start_date', '<=', mail_date),
            ('end_date', '>=', mail_date)
        ], limit=1).id

        defaults.pop('name', False)
        defaults.update(custom_values)

        request_id = super(CrmClaim, self).message_new(msg, defaults)
        request = self.browse(request_id)
        if not request.language:
            request.language = self.detect_lang(
                request.description).lang_id.code

        # # send automated holiday response
        try:
            if request.holiday_closure_id:
                request.send_holiday_answer()
        except Exception as e:
            _logger.error("The automatic mail failed\n{}".format(e))

        return request_id

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
        """Change the stage to "Resolve" when the employee answer
           to the supporter but not if it's an automatic answer.
        """
        result = super(CrmClaim, self).message_post(**kwargs)

        if 'mail_server_id' in kwargs and not self.env.context.get(
                'keep_stage'):
            for request in self:
                ir_data = self.env['ir.model.data']
                request.stage_id = ir_data.get_object_reference(
                    'crm_claim', 'stage_claim2')[1]

        return result

    @api.multi
    def write(self, values):
        """
        - If move request in stage 'Waiting on support' assign the request to
        the current user.
        - Push partner to associated mail messages
        """
        super(CrmClaim, self).write(values)

        if values.get('stage_id') == self.env.ref(
                'crm_request.stage_wait_support').id:
            for request in self:
                if not request.user_id:
                    request.user_id = self.env.uid

        if values.get('partner_id'):
            for request in self:
                request.message_ids.filtered(
                    lambda m: m.email_from == request.email_origin
                ).write({
                    'author_id': values['partner_id']
                })
        return True

    @api.model
    def detect_lang(self, text):
        """
        Use detectlanguage API to find the language of the given text
        :param text: text to detect
        :return: res.lang compassion record if the language is found, or False
        """
        detectlanguage.configuration.api_key = config.get(
            'detect_language_api_key')
        language_name = False
        langs = detectlanguage.languages()
        try:
            code_lang = detectlanguage.simple_detect(text)
        except (IndexError, detectlanguage.DetectLanguageError):
            # Language could not be detected
            return False
        for lang in langs:
            if lang.get("code") == code_lang:
                language_name = lang.get("name")
                break
        if not language_name:
            return False

        return self.env['res.lang.compassion'].search(
            [('name', '=ilike', language_name)], limit=1)

    @api.multi
    def send_holiday_answer(self):
        """ This will use the holiday mail template and enforce a
        mail sending to the requester. """
        template = self.env.ref("crm_request.business_closed_email_template")
        for request in self:
            template.with_context(lang=request.language).send_mail(
                request.id, force_send=True, email_values={
                    'email_to': request.email_origin}
            )


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
