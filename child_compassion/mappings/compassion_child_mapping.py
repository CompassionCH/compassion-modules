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


class GenericChildMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.generic.child'

    CONNECT_MAPPING = {
        # Fields used in Search Message (for global child)
        'Beneficiary_GlobalID': 'global_id',
        'Beneficiary_LocalID': 'local_id',
        'FieldOffice_Name': ('project_id.field_office_id.name',
                             'compassion.field.office'),
        'CorrespondentScore': 'correspondent_score',
        'IsSpecialNeeds': 'is_special_needs',
        'SourceCode': 'source_code',
        'PriorityScore': 'priority_score',
        'FullBodyImageURL': 'image_url',

        # Fields for DetailedInformation message (for compassion.child)
        'GlobalId': 'global_id',
        'LocalBeneficiaryId': 'local_id',

        # Fields shared for both child types
        'Age': 'age',
        'BirthDate': 'birthdate',
        'Country': ('project_id.field_office_id.country_id.code',
                    'res.country'),
        'ICP_ID': ('project_id.icp_id', 'compassion.project'),
        'FieldOffice_Name': ('project_id.field_office_id.name',
                             'compassion.field.office'),
        'FirstName': 'firstname',
        'LastName': 'lastname',
        'PreferredName': 'preferred_name',
        'FullName': 'name',
        'Gender': 'gender',
        'IsHivAffectedArea': 'is_area_hiv_affected',
        'IsOrphan': 'is_orphan',
        'WaitingSinceDate': 'unsponsored_since',
        'BeneficiaryState': 'beneficiary_state',
        'HoldingGlobalPartner': ('holding_global_partner_id.name',
                                 'compassion.global.partner'),
        'HoldExpirationDate': 'hold_expiration_date',
    }

    def _process_odoo_data(self, odoo_data):
        # Take first letter of gender
        gender = odoo_data.get('gender')
        if gender:
            odoo_data['gender'] = gender[0]


class GlobalChildMapping(GenericChildMapping):
    """ Mapping for Global Child object. """

    ODOO_MODEL = 'compassion.global.child'


class CompassionChildMapping(GenericChildMapping):
    """
    ====> TODO : Add all fields for the message GetDetailedInformation
    """
    ODOO_MODEL = 'compassion.child'

    # TODO
    FIELDS_TO_SUBMIT = {}
