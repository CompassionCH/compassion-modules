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

from openerp import models, api
from openerp.exceptions import Warning

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession


class SponsorshipCorrespondence(models.Model):
    _inherit = 'sponsorship.correspondence'

    @api.model
    def process_commkit_notifications(self, commkit_updates, eta=None):
        """ Create jobs which will process all incoming CommKit Notification
        messages. """
        session = ConnectorSession.from_env(self.env)
        for update_data in commkit_updates:
            update_commkit_job.delay(
                session, self._name, update_data, eta=eta)

    @api.model
    def _commkit_update(self, vals):
        """ Given the message data in vals, update or create a
        SponsorshipCorrespondence object. """
        commkit_vals = {
            'state': vals['Status'],
            'rework_reason': vals['SDL_ReasonForRework'],
            'rework_comments': vals['SDL_ReworkComments'],
            'letter_url': vals['FinalLetterURL']
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
        return commkit


@job(default_channel='root.commkit_update')
def update_commkit_job(session, model_name, data):
    """Job for processing an update commkit message."""
    session.env['sponsorship.correspondence']._commkit_update(data)
