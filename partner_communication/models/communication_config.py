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
    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Letter template')

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
        communication (digital, physical or False).
        :param partner: res.partner record
        :returns: send_mode (auto/digital/False), auto_mode (True/False)
        """
        self.ensure_one()
        if self.send_mode != 'partner_preference':
            send_mode = self.send_mode
        else:
            send_mode = getattr(
                partner, self.send_mode_pref_field,  False)

        auto_mode = 'auto' in send_mode
        send_mode = send_mode.replace('auto_', '')
        if send_mode == 'none':
            send_mode = False
        if send_mode == 'digital' and not partner.email:
            if self.print_if_not_email:
                send_mode = 'physical'
            else:
                send_mode = False
        return send_mode, auto_mode
