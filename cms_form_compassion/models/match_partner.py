# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _


class MatchPartner(models.AbstractModel):
    """
    Allows the matching of a partner from some given information.
    Can be extended or inherited to change the behaviour for some particular
    case.
    """
    _name = 'res.partner.match'

    @api.model
    def match_partner_to_infos(self, infos):
        """
        Find the partner that match the given info or create one if none exists
        :param infos: A dict containing the information available to find the
            partner.
            The keys should match the fields of res.partner. There is one
            exception, the partner_id key (be careful with it).
        :return: The matched partner.
        """

        new_partner = False
        partner_obj = self.env['res.partner'].sudo()
        partner = False

        partner_id = infos.get('partner_id')
        if partner_id:
            partner = partner_obj.browse(partner_id)

        if not partner or len(partner) > 1:
            partner = partner_obj.search([
                ('email', '=ilike', infos['email']),
                '|', ('active', '=', True), ('active', '=', False),
            ])

        if not partner or len(partner) > 1:
            partner = partner_obj.search([
                ('lastname', 'ilike', infos['lastname']),
                ('firstname', 'ilike', infos['firstname']),
                ('zip', '=', infos['zip']),
                '|', ('active', '=', True), ('active', '=', False),
            ])

        if not partner or len(partner) > 1:
            # no match found or not sure which one -> creating a new one.
            partner = self.match_create(partner_obj, infos)
            new_partner = True

        partner = self.match_after_match(partner, new_partner, infos)

        return partner

    @api.model
    def match_after_match(self, partner, new_partner, infos):
        """Once a match is found or created, this method allows to change it"""
        if not new_partner:
            self.match_update(partner, infos)
        return partner

    @api.model
    def match_process_create_infos(self, infos):
        """
        From the info given by the user, select the one that should be used
        for the creation of the partner.
        """
        valid = self._match_get_valid_create_fields()
        create_infos = {}
        for key, value in infos.iteritems():
            if key in valid:
                create_infos[key] = value

        # Mark the partner to be validated
        create_infos['state'] = 'pending'

        return create_infos

    @api.model
    def match_create(self, partner_obj, infos):
        """Create a new partner from a selection of the given infos."""
        create_infos = self.match_process_create_infos(infos)
        infos.setdefault('lang', self.env.lang)
        return partner_obj.create(create_infos)

    @api.model
    def _match_get_valid_create_fields(self):
        """Return the fields which can be used at creation."""
        return ['firstname', 'lastname', 'email', 'phone', 'street', 'city',
                'zip', 'country_id', 'state_id', 'title', 'lang', 'birthdate',
                'church_unlinked', 'function', 'spoken_lang_ids']

    @api.model
    def match_process_update_infos(self, infos):
        """
        From the info given by the user, select the one that should be used
        for the update of the partner.
        """
        valid = self._match_get_valid_update_fields()
        update_infos = {}
        for key, value in infos.iteritems():
            if key in valid:
                update_infos[key] = value
        return update_infos

    @api.model
    def match_update(self, partner, infos):
        """Update the matched partner with a selection of the given infos."""
        update_infos = self.match_process_update_infos(infos)
        partner.write(update_infos)

    @api.model
    def _match_get_valid_update_fields(self):
        """Return the fields which can be used at update."""
        return ['email', 'phone', 'street', 'city', 'zip', 'country_id',
                'state_id', 'church_unlinked', 'function', 'spoken_lang_ids']
