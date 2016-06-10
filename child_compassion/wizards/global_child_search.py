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

from openerp import models, fields, api
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
    min_age = fields.Integer()
    max_age = fields.Integer()
    birthday_month = fields.Integer()
    birthday_day = fields.Integer()
    birthday_year = fields.Integer()
    child_name = fields.Char()
    icp_ids = fields.Many2many(
        'compassion.project', 'childpool_project_search_rel',
        string='Projects')
    icp_name = fields.Char()
    hiv_affected_area = fields.Boolean()
    is_orphan = fields.Boolean()
    has_siblings = fields.Boolean()
    has_special_needs = fields.Boolean()
    min_days_waiting = fields.Integer()
    source_code = fields.Char()

    # Pagination
    skip = fields.Integer()
    take = fields.Integer(default=80)

    # Returned children
    nb_found = fields.Integer('Number of matching children', readonly=True)
    global_child_ids = fields.Many2many(
        'compassion.global.child', 'childpool_children_rel',
        string='Available Children', readonly=True,
    )

    @api.multi
    def do_search(self):
        self.ensure_one()
        # Remove previous search results
        self.global_child_ids = False

        mapping = base_mapping.new_onramp_mapping(self._name, self.env,
                                                  "profile_search")
        params = mapping.get_connect_data(self)
        onramp = OnrampConnector()
        result = onramp.send_message(
            'beneficiaries/availabilitysearch', 'GET', None, params)
        if result['code'] == 200:
            self.nb_found = result['content']['NumberOfBeneficiaries']
            self._map_and_create_json_oject(result['content']
                                            ['BeneficiarySearchResponseList'])
        else:
            raise Warning(
                result.get('content', result)['Error'])

        return True

    @api.multi
    def rich_mix(self):
        self.ensure_one()
        # Remove previous search results
        self.global_child_ids = False

        mapping = base_mapping.new_onramp_mapping(self._name, self.env,
                                                  "rich_mix")
        params = mapping.get_connect_data(self)
        onramp = OnrampConnector()
        result = onramp.send_message(
            'beneficiaries/richmix', 'GET', None, params)
        if result['code'] == 200:
            self._map_and_create_json_oject(result['content']
                                            ['BeneficiaryRichMixResponseList'])
        else:
            raise Warning(
                result.get('content', result)['Error'])

        return True

    def _map_and_create_json_oject(self, children):
        mapping = base_mapping.new_onramp_mapping(
            'compassion.global.child', self.env)
        for child_data in children:
            child_vals = mapping.get_vals_from_connect(child_data)
            self.global_child_ids += self.env[
                'compassion.global.child'].create(child_vals)
