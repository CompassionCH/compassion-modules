# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date


class res_partner(models.Model):
    """ UPSERT constituents. """
    _inherit = 'res.partner'

    @api.multi
    def write(self, vals):
        if vals.get('firstname') or vals.get('lastname') or \
                vals.get('name'):
            self._upsert_constituent()
        return super(res_partner, self).write(vals)

    @api.multi
    def write_from_gp(self, vals):
        """ GP always send firstname and lastname. We check if they changed.
        """
        new_firstname = vals.get('firstname')
        new_lastname = vals.get('lastname')
        to_update = self.mapped(
            lambda p: (new_firstname and p.firstname != new_firstname) or
            (new_lastname and p.lastname != new_lastname))
        to_update._upsert_constituent()
        return super(res_partner, self).write(vals)

    def _upsert_constituent(self):
        """If partner has active contracts, UPSERT Constituent in GMC."""
        for partner in self:
            contract_count = self.env['recurring.contract'].search_count([
                ('correspondant_id', '=', partner.id),
                ('state', 'not in', ('terminated', 'cancelled'))])
            if contract_count:
                # UpsertConstituent Message
                action_id = self.env['gmc.action'].search(
                    [('name', '=', 'UpsertConstituent')], limit=1).id
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner.id,
                    'partner_id': partner.id,
                    'date': date.today().strftime(DF),
                }
                message_obj = self.env['gmc.message.pool']
                # Delete pending upsert messages if any exist
                messages = message_obj.search([
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'new'),
                    ('action_id', '=', action_id)])
                if messages:
                    messages.unlink()
                message_obj.create(message_vals)
