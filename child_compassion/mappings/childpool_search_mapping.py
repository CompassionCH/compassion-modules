# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ChilpoolSearchMapping(OnrampMapping):
    """
    Childpool mapping for searching available children from GMC.
    """
    ODOO_MODEL = 'compassion.childpool.search'
    MAPPING_NAME = "profile_search"

    CONNECT_MAPPING = {
        'gender': 'gender',
        'countries': ('field_office_ids.country_code',
                      'compassion.field.office'),
        'minAge': 'min_age',
        'maxAge': 'max_age',
        'birthMonth': 'birthday_month',
        'birthDay': 'birthday_day',
        'birthYear': 'birthday_year',
        'name': 'child_name',
        'churchPartners': ('fcp_ids.fcp_id', 'compassion.project'),
        'churchPartnerName': 'fcp_name',
        'hivAffectedArea': 'hiv_affected_area',
        'isOrphan': 'is_orphan',
        'hasSpecialNeeds': 'has_special_needs',
        'minDaysWaiting': 'min_days_waiting',
        'skip': 'skip',
        'take': 'take',
    }

    FIELDS_TO_SUBMIT = {k: None for k in CONNECT_MAPPING.iterkeys()}

    def __init__(self, env):
        super(ChilpoolSearchMapping, self).__init__(env)
        self.FIELDS_TO_SUBMIT['gender'] = lambda g: g and g[0]

    def _process_connect_data(self, connect_data):
        """ Don't send fields not set. """
        temp_data = connect_data.copy()
        for key, value in temp_data.iteritems():
            if not value:
                del connect_data[key]


class AdvancedSearchMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.childpool.search'
    MAPPING_NAME = "advanced_search"

    CONNECT_MAPPING = {
        # Search params
        'NumberOfBeneficiaries': 'take',
        'Start': 'skip',
        'Filter': ('search_filter_ids', 'compassion.query.filter'),
        # Search fields
        'Age': 'min_age',
        'BeneficiaryLocalId': 'local_id',
        'BeneficiaryName': 'child_name',
        'BeneficiaryAMState': 'state_selected',
        'BirthDay': 'birthday_day',
        'BirthMonth': 'birthday_month',
        'BirthYear': 'birthday_year',
        'ChronicIllnesses': 'chronic_illness',
        'FieldOffice': 'field_office_ids',
        'Gender': 'gender',
        'HoldingGlobalPartner': 'holding_gp_ids',
        'FCPID': 'fcp_ids',
        'FCPName': 'fcp_name',
        'IsHIVAffectedArea': 'hiv_affected_area',
        'IsOrphan': 'is_orphan',
        'IsSpecialNeeds': 'has_special_needs',
        'NaturalFatherAlive': 'father_alive',
        'NaturalMotherAlive': 'mother_alive',
        'PhysicalDisabilities': 'physical_disability',
        'PlannedCompletionDate': 'completion_date_after',
        'WaitTime': 'min_days_waiting',
        # Constants not used
        'SortBy': None,
        'SortType': None,
    }

    FIELDS_TO_SUBMIT = {
        'NumberOfBeneficiaries': None,
        'Start': None,
        'Filter': None,
        'SortBy': None,
        'SortType': None,
    }

    CONSTANTS = {
        'SortBy': 'PriorityScore',
        'SortType': None
    }

    def _process_connect_data(self, connect_data):
        """ Put data in outgoing wrapper. """
        data = connect_data.copy()
        connect_data.clear()
        connect_data['BeneficiarySearchRequestList'] = data


class ChilpoolSearchMixMapping(OnrampMapping):
    """
    Childpool mapping for searching mix of available children from GMC.
    """
    ODOO_MODEL = 'compassion.childpool.search'
    MAPPING_NAME = "rich_mix"

    CONNECT_MAPPING = {
        'numberOfBeneficiaries': 'take',
    }

    FIELDS_TO_SUBMIT = {'numberOfBeneficiaries': None}
