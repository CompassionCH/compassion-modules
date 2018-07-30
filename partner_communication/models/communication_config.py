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
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)


class OmrConfig(models.AbstractModel):
    _name = 'partner.communication.orm.config.abstract'

    omr_enable_marks = fields.Boolean(
        string='Enable OMR',
        help='If set to True, the OMR marks are displayed in the '
             'communication.'
    )
    omr_should_close_envelope = fields.Boolean(
        string='OMR should close the envelope',
        help='If set to True, the OMR mark for closing the envelope is added '
             'to the communication.'
    )
    omr_add_attachment_tray_1 = fields.Boolean(
        string='Attachment from tray 1',
        help='If set to True, the OMR mark for adding an '
             'attachment from back 1 is added to the communication.'
    )
    omr_add_attachment_tray_2 = fields.Boolean(
        string='Attachment from tray 2',
        help='If set to True, the OMR mark for adding an '
             'attachment from tray 2 is added to the communication.'
    )


class CommunicationDefaults(models.AbstractModel):
    """ Abstract class to share config settings between communication config
    and communication job. """
    _name = 'partner.communication.defaults'

    user_id = fields.Many2one(
        'res.users', 'From', domain=[('share', '=', False)])
    need_call = fields.Boolean(
        help='Indicates we should have a personal contact with the partner'
    )
    print_if_not_email = fields.Boolean(
        help="Should we print the communication if the sponsor don't have "
             "an e-mail address"
    )
    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Letter template',
        domain=[('model', '=', 'partner.communication.job')]
    )


class CommunicationOmrConfig(models.Model):
    _name = 'partner.communication.omr.config'
    _inherit = 'partner.communication.orm.config.abstract'

    config_id = fields.Many2one('partner.communication.config')
    lang_id = fields.Many2one('res.lang')


class CommunicationConfig(models.Model):
    """ This class allows to configure if and how we will inform the
    sponsor when a given event occurs. """
    _name = 'partner.communication.config'
    _inherit = 'partner.communication.defaults'
    _inherits = {'utm.source': 'source_id'}
    _rec_name = "source_id"
    _description = 'Communication Configuration'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    source_id = fields.Many2one(
        'utm.source', 'UTM Source', required=True, ondelete='restrict'
    )
    model_id = fields.Many2one(
        'ir.model', 'Applies to', required=True,
        help="The kind of document with this communication can be used")
    model = fields.Char(related='model_id.model', store=True, readonly=True)
    send_mode = fields.Selection('_get_send_mode', required=True)
    send_mode_pref_field = fields.Char(
        'Partner preference field',
        help='Name of the field in res.partner in which to find the '
             'delivery preference'
    )
    email_template_id = fields.Many2one(
        'mail.template', 'Email template',
        domain=[('model', '=', 'partner.communication.job')]
    )
    attachments_function = fields.Char(
        help='Define a function in the communication_job model that will '
        'return all the attachment information for the communication in a '
        'dict of following format: {attach_name: [report_name, b64_data]}'
        'where attach_name is the name of the file generated,'
        'report_name is the name of the report used for printing,'
        'b64_data is the binary of the attachment'
    )
    omr_config_ids = fields.One2many(
        comodel_name='partner.communication.omr.config',
        inverse_name='config_id',
    )
    active = fields.Boolean(default=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.constrains('send_mode_pref_field')
    def _validate_config(self):
        """ Test if the config is valid. """
        for config in self.filtered('send_mode_pref_field'):
            valid = hasattr(self.env['res.partner'],
                            config.send_mode_pref_field)
            if not valid:
                raise ValidationError(
                    _("Following field does not exist in res.partner: %s.") %
                    config.send_mode_pref_field
                )

    @api.constrains('email_template_id', 'report_id')
    def _validate_attached_reports(self):
        for config in self:
            if config.email_template_id and config.email_template_id.model \
                    != 'partner.communication.job':
                raise ValidationError(
                    _("Attached e-mail templates should be linked to "
                      "partner.communication.job objects!")
                )
            if config.report_id and config.report_id.model != \
                    'partner.communication.job':
                raise ValidationError(
                    _("Attached report templates should be linked to "
                      "partner.communication.job objects!")
                )

    @api.constrains('attachments_function')
    def _validate_attachment_function(self):
        job_obj = self.env['partner.communication.job']
        for config in self.filtered('attachments_function'):
            if not hasattr(job_obj, config.attachments_function):
                raise ValidationError(
                    _("partner.communication.job has no function called ") +
                    config.attachments_function
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
            ('both', _('Send e-mail + prepare report (print manually)')),
        ]

    def get_inform_mode(self, partner):
        """ Returns how the partner should be informed for the given
        communication (digital, physical or False).
        It makes the product of the communication preference and the partner
        preference :

        comm_pref   partner_pref    result
        ----------------------------------
        digital     physical        physical if "print if no e-mail" else none
        physical    digital         physical if not "email only"

        auto        manual          manual
        manual      auto            manual

        :param partner: res.partner record
        :returns: send_mode (physical/digital/False), auto_mode (True/False)
        """
        self.ensure_one()
        # First key is the comm send_mode, second key is the partner send_mode
        # value is the send_mode that should be selected.
        send_priority = {
            'physical': {
                'none': 'none',
                'physical': 'physical',
                'digital': 'physical' if not partner.email_only else 'none',
                'both': 'physical',
            },
            'digital': {
                'none': 'none',
                'physical': 'physical' if self.print_if_not_email else 'none',
                'digital': 'digital',
                'both': 'both' if self.print_if_not_email else 'digital',
            },
            'both': {
                'none': 'none',
                'physical': 'physical',
                'digital': 'both' if not partner.email_only else 'digital',
                'both': 'both',
            }
        }

        if self.send_mode != 'partner_preference':
            partner_mode = getattr(
                partner, self.send_mode_pref_field or
                'global_communication_delivery_preference',
                partner.global_communication_delivery_preference)
            if self.send_mode == partner_mode:
                send_mode = self.send_mode
                auto_mode = 'auto' in send_mode or send_mode == 'both'
            else:
                auto_mode = (
                    'auto' in self.send_mode and 'auto' in partner_mode or
                    self.send_mode == 'both' and 'auto' in partner_mode or
                    'auto' in self.send_mode and partner_mode == 'both'
                )
                comm_mode = self.send_mode.replace('auto_', '')
                partner_mode = partner_mode.replace('auto_', '')
                send_mode = send_priority[comm_mode][partner_mode]

        else:
            send_mode = getattr(
                partner, self.send_mode_pref_field,  'none')
            auto_mode = 'auto' in send_mode or send_mode == 'both'

        send_mode = send_mode.replace('auto_', '')
        if send_mode == 'none':
            send_mode = False

        # missing email
        if send_mode in ['digital', 'both'] and not partner.email:
            removed_digital = True
            if (self.print_if_not_email or send_mode == 'both') and not \
                    partner.email_only:
                send_mode = 'physical'
                auto_mode = False
            else:
                send_mode = False

        # missing address
        if send_mode in ['physical', 'both'] and \
                not (partner.zip or partner.city):
            if send_mode == 'both' and not removed_digital:
                send_mode = 'digital'
            else:
                send_mode = False

        return send_mode, auto_mode
