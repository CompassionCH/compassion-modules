# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields

import requests
import logging

logger = logging.getLogger(__name__)


class child_compassion(models.Model):
    _inherit = 'compassion.child'

    sponsorship_ids = fields.One2many(
        'recurring.contract', compute='_set_related_contracts',
        string="Sponsorships", readonly=True)
    unsponsored_since = fields.Date(
        compute='_set_unsponsored_since', store=True)

    @api.multi
    def _set_related_contracts(self):
        con_obj = self.env['recurring.contract']
        for child in self:
            child.sponsorship_ids = con_obj.search([
                ('child_id', '=', child.id),
                ('type', '=', 'S')])

    @api.multi
    def _set_unsponsored_since(self):
        """ Returns the date since the child is waiting for a sponsor.
        If child was never sponsored, this date comes from GMC services,
        otherwise we can infer it by looking at last sponsorship. """
        con_obj = self.env['recurring.contract']
        for child in self:
            child.unsponsored_since = False
            contract = con_obj.search(
                [('child_id', '=', child.id)], order='end_date desc', limit=1)
            if contract and child.state not in ('P', 'F', 'X'):
                child.unsponsored_since = contract.end_date
            elif not child.has_been_sponsored:
                # Retrieve the information from the webservice
                url = self.get_url(child.code, 'information')
                r = requests.get(url)
                json_data = r.json()
                if r.status_code == 200:
                    child.unsponsored_since = json_data[
                        'beginWaitTime'] or False
                else:
                    logger.error(
                        'An error occured while fetching the unsponsored '
                        ' date of child %s.' % child.code +
                        json_data['error']['message'])

    @api.multi
    def get_infos(self):
        """ Update unsponsored date. """
        self._set_unsponsored_since()
        return super(child_compassion, self).get_infos()
