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
from openerp import api, models, fields, _
from openerp.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)


class CommunicationConfig(models.Model):
    """ This class allows to configure if and how we will inform the
    sponsor when a given event occurs. """
    _name = 'partner.communication.config'
    _description = 'Communication Configuration'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(
        required=True, help='Rule name')
    send_mode = fields.Selection('_get_send_mode', required=True)
    send_mode_pref_field = fields.Char(
        'Partner preference field',
        help='Name of the field in res.partner in which to find the '
             'delivery preference'
    )
    print_if_not_email = fields.Boolean(
        help="Should we print the communication if the sponsor don't have "
             "an e-mail address"
    )
    email_template_id = fields.Many2one(
        'email.template', 'Email template')
    report_id = fields.Many2many(
        'ir.actions.report.xml', 'Letter template')
    from_employee_id = fields.Many2one(
        'hr.employee', 'Communication From',
        help='The sponsor will receive the communication from this employee'
    )
    email_ids = fields.One2many(
        'mail.mail', 'communication_config_id', 'Generated e-mails',
        help='Track e-mails generated from this configuration'
    )
    paper_usage_count = fields.Integer(
        help='How many times a paper was print with this configuration'
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    @api.constrains('send_mode_pref_field')
    def _validate_config(self):
        """ Test if the config is valid. """
        valid = True
        if self.send_mode_pref_field:
            valid = hasattr(self.env['res.partner'], self.send_mode_pref_field)

        if not valid:
            raise ValidationError(
                "Following field does not exist in res.partner: %s." %
                self.send_mode_pref_field
            )

    def _get_send_mode(self):
        send_modes = self.get_delivery_preferences()
        send_modes.append(
            ('partner_preference', _('Partner specific'))
        )
        return send_modes

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def get_delivery_preferences(self):
        return [
            ('none', _("Don't inform sponsor")),
            ('auto_digital', _('Send e-mail automatically')),
            ('digital', _('Prepare e-mail (sent manually)')),
            ('auto_physical', _('Print letter automatically')),
            ('physical', _('Prepare report (print manually)')),
        ]

    def get_inform_mode(self, partner):
        """ Returns how the partner should be informed for the given
        communication.
        :param partner: res.partner record
        """
        self.ensure_one()
        if self.send_mode != 'partner_preference':
            return self.send_mode
        else:
            return getattr(
                partner, self.send_mode_pref_field.name,  'none')

    def inform_sponsor(self, partner, object_id, auto_send=None,
                       email_template=None, report=None, _from=None, to=None):
        """ Sends a communication to the sponsor based on the configuration.
        :param partner: res.partner record
        :param object_id: record id generating the e-mail or report. This
                          record will be used to construct dynamic templates.
        :param auto_send: optional field for overriding communication
                          configuration (useful to prevent or force auto_send)
        :param email_template: optional e-mail template to override the
                               default set in the config
        :param report: optional report to override the default set in the
                       config
        :param _from: optional e-mail address to override the sender of the
                      communication.
        :param to: optional e-mail address to override the recipient of the
                   communication.

        :returns: Email or Report record if one was generated, False if
                  nothing was done.
        """
        self.ensure_one()
        send_mode = self.get_inform_mode(partner)
        if send_mode == 'none':
            return False

        if auto_send is None:
            auto_send = 'auto' in send_mode
        if email_template is None:
            email_template = self.email_template_id

        if 'digital' in send_mode and email_template:
            if _from is None:
                _from = self.from_employee_id.work_email or self.env[
                    'ir.config_parameter'].get_param(
                    'partner_communication.default_from_address')
            if _from and (to or partner.email):
                # Send by e-mail
                email_vals = {
                    'email_from': _from,
                    'recipient_ids': [(4, partner.id)],
                    'communication_config_id': self.id
                }
                if to:
                    # Replace partner e-mail by specified address
                    email_vals['email_to'] = to
                    del email_vals['recipient_ids']

                email = self.env['mail.compose.message'].with_context(
                    lang=partner.lang).create_emails(
                    email_template, object_id, email_vals)
                if auto_send:
                    email.send_sendgrid()
                message = email.message_id
                partner.message_post(message.body, message.subject)
                return email

        if 'physical' in send_mode or self.print_if_not_email:
            # TODO Print letter
            self.paper_usage_count += 1
            return False

        # A valid path was not found
        return False
