# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import json
import base64
import uuid

from ..tools.onramp_connector import OnrampConnector
from ..mappings import base_mapping as mapping

from openerp import models, fields, api, _
from openerp.exceptions import Warning

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession


class SponsorshipCorrespondence(models.Model):
    _inherit = 'correspondence'

    # Letter remote access and stats
    ###################################
    uuid = fields.Char(required=True, default=lambda self: self._get_uuid())
    read_url = fields.Char(compute='_get_read_url')
    last_read = fields.Datetime()
    read_count = fields.Integer(default=0)

    def _get_uuid(self):
        return str(uuid.uuid4())

    @api.multi
    def _get_read_url(self):
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url')
        for letter in self:
            letter.read_url = "{}/b2s_image?id={}".format(
                base_url, letter.uuid)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit. """
        letter = super(SponsorshipCorrespondence, self).create(vals)
        if not self.env.context.get('no_comm_kit'):
            action_id = self.env.ref('onramp_compassion.create_commkit').id
            self.env['gmc.message.pool'].create({
                'action_id': action_id,
                'object_id': letter.id
            })
        return letter

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def process_commkit_notifications(self, commkit_updates, headers,
                                      eta=None):
        """ Create jobs which will process all incoming CommKit Notification
        messages. """
        session = ConnectorSession.from_env(self.env)
        action_id = self.env.ref('onramp_compassion.update_commkit').id
        for update_data in commkit_updates:
            # Create a GMC message to keep track of the updates
            gmc_message = self.env['gmc.message.pool'].create({
                'action_id': action_id,
                'content': json.dumps(update_data),
                'headers': json.dumps(dict(headers.items()))})
            job_uuid = update_commkit_job.delay(
                session, self._name, update_data, gmc_message.id, eta=eta)
            gmc_message.request_id = job_uuid

        return True

    def convert_for_connect(self):
        """
        Method called when Create CommKit message is processed.
        (TODO) Upload the image to Persistence and convert correspondence data
        to GMC format.

        TODO : Remove this method and use mapping directly in message center.
        """
        self.ensure_one()
        letter = self.with_context(lang='en_US')
        if not letter.original_letter_url:
            onramp = OnrampConnector()
            letter.original_letter_url = onramp.send_letter_image(
                letter.letter_image.datas, letter.letter_format)
        letter_mapping = mapping.new_onramp_mapping(self._name, self.env)
        return letter_mapping.get_connect_data(letter)

    def get_connect_data(self, data):
        """ Enrich correspondence data with GMC data after CommKit Submission.
        """
        self.ensure_one()
        letter_mapping = mapping.new_onramp_mapping(self._name, self.env)
        return self.write(letter_mapping.get_vals_from_connect(data))

    def process_letter(self):
        """ Method called when new B2S letter is Published. """
        self.download_attach_letter_image('original_letter_url')
        for letter in self:
            if letter.original_language_id not in \
                    letter.correspondant_id.spoken_lang_ids:
                letter.compose_letter_image()

    @api.multi
    def download_attach_letter_image(self, context=None,
                                     type='final_letter_url'):
        """ Download letter image from US service and attach to letter. """
        for letter in self:
            # Download and store letter
            letter_url = getattr(letter, type)
            image_data = None
            if letter_url:
                image_data = OnrampConnector().get_letter_image(
                    letter_url, 'pdf', dpi=300)
            if image_data is None:
                raise Warning(
                    _('Image does not exist'),
                    _("Image requested was not found remotely."))
            name = letter.child_id.code + '_' + letter.kit_identifier + '.pdf'
            letter.letter_image = self.env['ir.attachment'].create({
                "name": name,
                "db_datas": image_data,
                'res_model': self._name,
                'res_id': letter.id,
            })

    @api.multi
    def attach_original(self):
        self.download_attach_letter_image(type='original_letter_url')

    def get_image(self, user=None):
        """ Method for retrieving the image and updating the read status of
        the letter.
        """
        self.ensure_one()
        self.write({
            'last_read': fields.Datetime.now(),
            'read_count': self.read_count + 1,
        })
        data = base64.b64decode(self.letter_image.datas)
        message = _("The sponsor requested the child letter image.")
        if user is not None:
            message = _("User requested the child letter image.")
        self.message_post(message, _("Letter downloaded"))
        return data

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    @api.model
    def _commkit_update(self, data, message_id=None):
        """ Given the message data, update or create a
        SponsorshipCorrespondence object. """
        letter_mapping = mapping.new_onramp_mapping(self._name, self.env)
        commkit_vals = letter_mapping.get_vals_from_connect(data)

        published_state = 'Published to Global Partner'
        is_published = commkit_vals.get('state') == published_state

        # Write/update commkit
        kit_identifier = commkit_vals.get('kit_identifier')
        commkit = self.search([('kit_identifier', '=', kit_identifier)])
        if commkit:
            # Avoid to publish twice a same letter
            is_published = is_published and commkit.state != published_state
            commkit.write(commkit_vals)
        else:
            commkit = self.with_context(no_comm_kit=True).create(commkit_vals)

        if is_published:
            commkit.process_letter()

        if message_id is not None:
            gmc_message = self.env['gmc.message.pool'].browse(message_id)
            gmc_message.write({
                'object_id': commkit.id,
                'state': 'success',
                'process_date': fields.Datetime.now()})
        return gmc_message

    @api.model
    def _needaction_domain_get(self):
        domain = [('direction', '=', 'Beneficiary To Supporter'),
                  ('state', '=', 'Published to Global Partner'),
                  ('last_read', '=', False)]
        return domain

##############################################################################
#                            CONNECTOR METHODS                               #
##############################################################################


def related_action_message(session, job):
    message_id = job.args[2]
    action = {
        'name': _("Message"),
        'type': 'ir.actions.act_window',
        'res_model': 'gmc.message.pool',
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': message_id,
    }
    return action


@job(default_channel='root.commkit_update')
@related_action(action=related_action_message)
def update_commkit_job(session, model_name, data, message_id):
    """Job for processing an update commkit message."""
    session.env[model_name]._commkit_update(
        data, message_id)
