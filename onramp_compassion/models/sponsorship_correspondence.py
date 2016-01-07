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

import base64
import json
import urllib2

from ..tools.onramp_connector import OnrampConnector
from ..mappings import base_mapping as mapping

from openerp import models, fields, api, _

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession


class SponsorshipCorrespondence(models.Model):
    _inherit = 'sponsorship.correspondence'

    hosted_letter_id = fields.Many2one('sponsorship.hostedletter',
                                       default=lambda self: self._retrieve_letter())

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit. """
        letter = super(SponsorshipCorrespondence, self).create(vals)
        if not self.env.context.get('from_onramp'):
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

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def _commkit_update(self, data, message_id=None):
        """ Given the message data, update or create a
        SponsorshipCorrespondence object. """
        letter_mapping = mapping.new_onramp_mapping(self._name, self.env)
        commkit_vals = letter_mapping.get_vals_from_connect(data)

        # Download and store letter
        letter_url = commkit_vals['original_letter_url']
        response = urllib2.urlopen(letter_url)
        letter_file = response.read()
        attachment = self.env['ir.attachment'].create({
            "name": letter_url,
            "db_datas": base64.b64encode(letter_file),
        })
        hosted_letter = self.env['sponsorship.hostedletter'].create({
            'letter_file': attachment.id,
        })
        commkit_vals['hosted_letter_id'] = hosted_letter.id

        kit_identifier = commkit_vals.get('kit_identifier')
        commkit = self.search([('kit_identifier', '=', kit_identifier)])
        if commkit:
            commkit.write(commkit_vals)
        else:
            commkit = self.with_context(from_onramp=True).create(commkit_vals)

        if message_id is not None:
            gmc_message = self.env['gmc.message.pool'].browse(message_id)
            gmc_message.write({
                'object_id': commkit.id,
                'state': 'success',
                'process_date': fields.Datetime.now()})
        return gmc_message


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
