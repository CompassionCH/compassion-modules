# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ChilpoolSearchMapping(OnrampMapping):
    """
    Childpool mapping for searching available children from GMC.
    """
    ODOO_MODEL = 'compassion.childpool.search'
    ACTION = "profile_search"

    CONNECT_MAPPING = {
        'gender': 'gender',
        'countries': ('field_office_ids.field_office_id',
                      'compassion.field.office'),
        'minAge': 'min_age',
        'maxAge': 'max_age',
        'birthMonth': 'birthday_month',
        'birthDay': 'birthday_day',
        'birthYear': 'birthday_year',
        'name': 'child_name',
        'churchPartners': ('icp_ids.icp_id', 'compassion.project'),
        'churchPartnerName': 'icp_name',
        'hivAffectedArea': 'hiv_affected_area',
        'isOrphan': 'is_orphan',
        'hasSiblings': 'has_siblings',
        'hasSpecialNeeds': 'has_special_needs',
        'minDaysWaiting': 'min_days_waiting',
        'sourceCode': 'source_code',
        'skip': 'skip',
        'take': 'take',
    }

    FIELDS_TO_SUBMIT = {k: None for k in CONNECT_MAPPING.iterkeys()}

    def _process_connect_data(self, connect_data):
        """ Don't send fields not set. """
        temp_data = connect_data.copy()
        for key, value in temp_data.iteritems():
            if not value:
                del connect_data[key]


class ChilpoolSearchMixMapping(OnrampMapping):
    """
    Childpool mapping for searching mix of available children from GMC.
    """
    ODOO_MODEL = 'compassion.childpool.search'
    ACTION = "rich_mix"

    CONNECT_MAPPING = {
        'numberOfBeneficiaries': 'take',
    }

    FIELDS_TO_SUBMIT = {'numberOfBeneficiaries': None}
