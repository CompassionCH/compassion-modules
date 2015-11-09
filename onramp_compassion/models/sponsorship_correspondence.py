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

from openerp import models, fields, api, _
from openerp.exceptions import Warning

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession


class SponsorshipCorrespondence(models.Model):
    _inherit = 'sponsorship.correspondence'

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
        to GMC format. """
        self.ensure_one()
        letter = self.with_context(lang='en_US')
        return {
            'Beneficiary': {
                'LocalId': letter.child_code,
                'CompassId': letter.child_id.unique_id,
            },
            'GlobalPartner': {
                'Id': 'CH'
            },
            'Direction': letter.direction,
            'Pages': [],
            'RelationshipType': letter.relationship,
            'SBCGlobalStatus': letter.state,
            'GlobalPartnerSBCId': letter.id,
            'OriginalLanguage': letter.original_language_id.name,
            'OriginalLetterURL': letter.original_letter_url,
            'SourceSystem': 'Odoo',
            'Template': 'KR-A-1S21-1',   # TODO see template naming schemes
            'Supporter': {
                'CompassConstituentId': letter.correspondant_id.ref,
                'GlobalId': letter.correspondant_id.ref
            }
        }

    def get_connect_data(self, data):
        """ Enrich correspondence data with GMC data after CommKit Submission.
        """
        self.ensure_one()
        self.write({
            'kit_id': int(data.get('CompassionSBCId', self.kit_id)),
            'state': data.get('Status', self.state)
        })

    @api.model
    def _commkit_update(self, vals, message_id=None):
        """ Given the message data in vals, update or create a
        SponsorshipCorrespondence object. """
        commkit_vals = {
            'state': vals['Status'],
            'rework_reason': vals['SDL_ReasonForRework'],
            'rework_comments': vals['SDL_ReworkComments'],
            'final_letter_url': vals['FinalLetterURL']
        }
        kit_id = int(vals.get('CompassionSBCId', -1))
        commkit = self.search([('kit_id', '=', kit_id)])
        if commkit:
            commkit.write(commkit_vals)
        else:
            # Find sponsorship based on partner and child information
            child_code = vals['Beneficiary_LocalId']
            partner_code = vals['Supporter_CompassConstituentId'][2:]
            sponsorship = self.env['recurring.contract'].search([
                ('partner_codega', '=', partner_code),
                ('child_code', '=', child_code)], limit=1)
            if not sponsorship:
                raise Warning(
                    'Not found',
                    'No sponsorship found for %s - %s' % (partner_code,
                                                          child_code))
            comm_types = self.env['sponsorship.correspondence.type'].search(
                [('name', 'in', vals['Type'])]).ids or False
            commkit_vals.update({
                'sponsorship_id': sponsorship.id,
                'kit_id': int(vals['CompassionSBCId']),
                'direction': vals['Direction'],
                'communication_type_ids': [(6, 0, comm_types)],
                'relationship': vals['RelationshipType'],
            })
            commkit = self.create(commkit_vals)

        if message_id is not None:
            gmc_message = self.env['gmc.message.pool'].browse(message_id)
            gmc_message.write({
                'object_id': commkit.id,
                'state': 'success',
                'process_date': fields.Datetime.now()})
        return gmc_message


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
