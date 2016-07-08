# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from math import ceil
from openerp import models, fields, api, _
from openerp.exceptions import Warning

from openerp.addons.message_center_compassion.tools.onramp_connector import \
    OnrampConnector

from openerp.addons.message_center_compassion.mappings import base_mapping


class GlobalChildSearch(models.TransientModel):
    """
    Class used for searching children in the global childpool.
    """
    _name = 'compassion.childpool.search'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # Search parameters
    gender = fields.Selection([
        ('Male', 'Male'),
        ('Female', 'Female')
    ])
    field_office_ids = fields.Many2many(
        'compassion.field.office', 'childpool_field_office_search_rel',
        string='Field Offices')
    min_age = fields.Integer(size=2)
    max_age = fields.Integer(size=2)
    birthday_month = fields.Integer(size=2)
    birthday_day = fields.Integer(size=2)
    birthday_year = fields.Integer(size=4)
    child_name = fields.Char()
    icp_ids = fields.Many2many(
        'compassion.project', 'childpool_project_search_rel',
        string='Projects')
    icp_name = fields.Char()
    hiv_affected_area = fields.Boolean()
    is_orphan = fields.Boolean()
    has_siblings = fields.Boolean()
    has_special_needs = fields.Boolean()
    min_days_waiting = fields.Integer(size=4)
    source_code = fields.Char()

    # Pagination
    skip = fields.Integer(size=4)
    take = fields.Integer(default=80, size=4)

    # Returned children
    nb_found = fields.Integer('Number of matching children', readonly=True)
    nb_selected = fields.Integer(
        'Selected children', compute='_compute_nb_children')
    global_child_ids = fields.Many2many(
        'compassion.global.child', 'childpool_children_rel',
        string='Available Children', readonly=True,
    )
    nb_male = fields.Integer('Boys', compute='_compute_nb_children')
    nb_female = fields.Integer('Girls', compute='_compute_nb_children')

    hold_expiration_date = fields.Datetime()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_nb_children(self):
        for search in self:
            search.nb_selected = len(search.global_child_ids)
            search.nb_male = len(search.global_child_ids.filtered(
                lambda child: child.gender == 'M'))
            search.nb_female = len(search.global_child_ids.filtered(
                lambda child: child.gender == 'F'))

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def do_search(self):
        self.ensure_one()
        # Remove previous search results
        self.global_child_ids.unlink()
        self._call_search_service(
            'profile_search', 'beneficiaries/availabilitysearch',
            'BeneficiarySearchResponseList')
        return True

    @api.multi
    def add_search(self):
        self.ensure_one()
        self.skip += self.nb_selected
        self._call_search_service(
            'profile_search', 'beneficiaries/availabilitysearch',
            'BeneficiarySearchResponseList')
        if self.nb_found == 0:
            raise Warning(_('No children found.'))
        return True

    @api.multi
    def rich_mix(self):
        self.ensure_one()
        # Remove previous search results
        self.global_child_ids.unlink()
        self._call_search_service(
            'rich_mix', 'beneficiaries/richmix',
            'BeneficiaryRichMixResponseList')
        return True

    @api.multi
    def make_a_hold(self):
        """ Create hold and send to Connect """
        holds = self.env['compassion.hold']
        messages = self.env['gmc.message.pool']
        for child in self.global_child_ids:
            # Save children form global children to compassion children
            child_vals = {
                'global_id': child.global_id,
                'local_id': child.local_id,
                'project_id': child.project_id.id,
                'field_office_id': child.field_office_id,
                'name': child.name,
                'firstname': child.firstname,
                'lastname': child.lastname,
                'preferred_name': child.preferred_name,
                'gender': child.gender,
                'birthdate': child.birthdate,
                'age': child.age,
                'is_orphan': child.is_orphan,
                'beneficiary_state ': child.beneficiary_state,
                'sponsorship_status': child.sponsorship_status,
                'unsponsored_since': child.unsponsored_since,
            }
            child_comp = self.env['compassion.child'].create(child_vals)

            # Create Holds for children to reserve
            hold_vals = {
                'name': "",
                'child_id': child_comp.id,
                'type': 'Consignment Hold',
                'expiration_date': self.hold_expiration_date,
                'primary_owner': 'Rose-Marie Reber',
                'secondary_owner': 'Carole Rochat',
                'no_money_yield_rate': '1.1',
                'yield_rate': '1.1',
                'channel': '',
                'source_code': '',
            }
            hold = holds.create(hold_vals)
            holds += hold

            # create messages to send to Connect
            action_id = self.env.ref('child_compassion.create_hold').id

            messages += messages.create({
                'action_id': action_id,
                'object_id': hold.id
            })
        messages.with_context(async_mode=False).process_messages()

        # update compassion children with hold_id received
        for hold in holds:
            child_to_update = hold.child_id
            if hold.hold_id:
                child_vals = {
                    'hold_id': hold.id,
                    'active': True,
                    'state': 'N',
                }
                child_to_update.write(child_vals)
            else:
                # delete child if no hold_id received
                child_to_update.unlink()
                hold.unlink()

    @api.multi
    def country_mix(self):
        """
        Tries to find an even number of children for each country.
        :return:
        """
        country_codes = self.env['compassion.field.office'].search([]).mapped(
            'field_office_id')
        children = {code: self.env['compassion.global.child'] for code in
                    country_codes}
        max_per_country = ceil(float(self.take) / len(country_codes))
        found_children = self.env['compassion.global.child']
        all_children = self.env['compassion.global.child']
        nb_found = 0
        tries = 0
        while nb_found < self.take:
            all_children += self.global_child_ids
            self.take_more()
            for child in self.global_child_ids - all_children:
                child_country = child.local_id[0:2]
                country_pool = children.get(child_country)
                if country_pool is not None and len(country_pool) < \
                        max_per_country:
                    children[child_country] = country_pool + child
                    found_children += child
                    nb_found += 1
                if nb_found == self.take:
                    break
            self.skip += self.take
            tries += 1
            if tries > 5:
                raise Warning(
                    _("Cannot find enough availalbe children in all "
                      "countries. Try with less"))

        # Delete leftover children
        (self.global_child_ids - found_children).unlink()
        return True

    @api.multi
    def filter(self):
        self.ensure_one()
        matching = self.global_child_ids.filtered(
            lambda child: self._does_match(child))
        (self.global_child_ids - matching).unlink()
        # Specify filter is applied
        self.nb_found = len(self.global_child_ids)
        return True

    @api.multi
    def take_more(self):
        self.ensure_one()
        # Use rich mix
        self._call_search_service(
            'rich_mix', 'beneficiaries/richmix',
            'BeneficiaryRichMixResponseList')
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _call_search_service(self, mapping_name, service_name, result_name):
        """
        Calls the given search service for the global childpool
        :param mapping_name: Name of the action mapping to use the correct
                             mapping.
        :param service_name: URL endpoint of the search service to call
        :param result_name: Name of the wrapping tag for the answer
        :return:
        """
        mapping = base_mapping.new_onramp_mapping(
            self._name, self.env, mapping_name)
        params = mapping.get_connect_data(self)
        onramp = OnrampConnector()
        result = onramp.send_message(service_name, 'GET', None, params)
        if result['code'] == 200:
            self.nb_found = result['content'].get('NumberOfBeneficiaries', 0)
            mapping = base_mapping.new_onramp_mapping(
                'compassion.global.child', self.env)
            for child_data in result['content'][result_name]:
                child_vals = mapping.get_vals_from_connect(child_data)
                child_vals['search_view_id'] = self.id
                self.global_child_ids += self.env[
                    'compassion.global.child'].create(child_vals)
        else:
            raise Warning(result.get('content', result)['Error'])

    def _does_match(self, child):
        """ Returns if the selected criterias correspond to the given child.
        """
        if self.field_office_ids and child.project_id.field_office_id not in \
                self.field_office_ids:
            return False
        if self.icp_ids and child.project_id not in self.icp_ids:
            return False
        if self.icp_name and self.icp_name not in child.project_id.name:
            return False
        if self.child_name and self.child_name not in child.name:
            return False
        if self.gender and child.gender != self.gender[0]:
            return False
        if self.hiv_affected_area and not child.is_area_hiv_affected:
            return False
        if self.is_orphan and not child.is_orphan:
            return False
        if self.has_special_needs and not child.is_special_needs:
            return False
        if self.min_age and child.age < self.min_age:
            return False
        if self.max_age and child.age > self.max_age:
            return False
        if self.min_days_waiting and child.waiting_days < \
                self.min_days_waiting:
            return False
        birthdate = fields.Date.from_string(child.birthdate)
        if self.birthday_month and self.birthday_month != birthdate.month:
            return False
        if self.birthday_day and self.birthday_day != birthdate.day:
            return False
        if self.birthday_year and self.birthday_year != birthdate.year:
            return False

        return True
