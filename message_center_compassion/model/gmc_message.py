# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv.orm import Model, fields
from openerp.osv import fields, osv
import requests
import pdb


SERVER_URL = 'https://test.services.compassion.ch:443/rest/openerp/'


class gmc_message_pool(Model):
    """ Pool of messages exchanged between Compassion CH and GMC. """
    _name = 'gmc.message.pool'

    _columns = {
        'date': fields.date(_('Message Date'), required=True, readonly=True),
        'action_id': fields.many2one('gmc.action',_('GMC Message'),
                                  ondelete="restrict", required=True,
                                  readonly=True),
        'send_date': fields.date(_('Date Sent to GMC'), readonly=True),
        'state': fields.selection(
            [('pending', _('Pending')),
             ('sent', _('Sent'))],
            _('State'), readonly=True
        ),
        'object_id': fields.integer(_('Referrenced Object Id')),
        'incoming_key': fields.char(_('Object Reference'), size=9,
                                    help=_("In case of incoming message, \
                                            contains the reference of the \
                                            child or the project that will \
                                            be created/modified.")),
    }
gmc_message_pool()


class gmc_action(Model):
    """ Represents all messages that can be sent/received via
    the OffRamp message system developed by Compass."""
    _name = 'gmc.action'
    _columns = {
        'direction': fields.selection(
            (('in',_('Incoming Message')),
             ('out',_('Outgoing Message')),
            ),
            _('Message Direction'), required=True
        ),
        'name': fields.char(_('GMC Message'), size=20, required=True),
        'model': fields.char('OSV Model', size=30),
        'type': fields.selection(
            [('create','Create'),
             ('update', 'Update'),
             ('allocate', 'Allocate'),
             ('deallocate', 'Deallocate'),
             ('depart', 'Depart Child'),
             ],
            _('Message Type'), required=True
        ),
    }
gmc_action()