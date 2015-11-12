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
from base_mapping import OnrampMapping


class CorrespondenceMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship Correspondence.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'sponsorship.correspondence'

    BENEFICIARY_MAPPING = {
        'Age': None,
        'CompassId': ('child_id.unique_id', 'compassion.child'),
        'Gender': None,
        'GlobalId': None,
        'LocalId': ('child_id.code', 'compassion.child'),
        'Name': None,
        'ObjectUrl': None
    }

    FIELD_OFFICE_MAPPING = {
        'Name': None
    }

    GLOBAL_PARTNER_MAPPING = {
        'Id': None,
        'OptInForLanguageTranslation': None
    }

    ICP_MAPPING = {
        'Id': None,
        'ObjectUrl': None
    }

    PAGES_MAPPING = {
        'EnglishTranslatedText': None,
        'FinalPageURL': None,
        'OriginalPageURL': None,
        'OriginalText': None,
        'TranslatedText': None
    }

    SUPPORTER_MAPPING = {
        'CompassConstituentId': None,   # Todo Where to find this ?
        'CommunicationDeliveryPreference': None,  # Todo Where to find this ?
        'GlobalId': ('correspondant_id.ref', 'res.partner'),
        'MandatoryReviewRequired': 'mandatory_review',
        'ObjectUrl': None,
        'PreferredName': ('correspondant_id.name', 'res.partner'),
        'Gender': None
    }

    CONNECT_MAPPING = {
        'Beneficiary': BENEFICIARY_MAPPING,
        'Field Office': FIELD_OFFICE_MAPPING,
        'FontSize': None,
        'Font': None,
        'GlobalPartner': GLOBAL_PARTNER_MAPPING,
        'Pages': PAGES_MAPPING,
        'Direction': 'direction',
        'PrintType': None,
        'RelationshipType': 'relationship',
        'SBCGlobalStatus': 'state',
        'Status': 'state',
        'SBCTypes': ('communication_type_ids.name',
                     'sponsorship.correspondence.type'),
        'CompassionSBCId': 'kit_identifier',
        'FinalLetterURL': 'final_letter_url',
        'GlobalPartnerSBCId': 'id',
        'IsFinalLetter': None,
        'IsFinalLetterArchived': None,
        'IsOriginalLetterArchived': None,
        'IsOriginalLetterMailed': None,
        'ItemNotScannedEligible': None,
        'ItemNotScannedNotEligible': None,
        'NumberOfPages': None,
        'OriginalLanguage': ('original_language_id.name',
                             'res.lang.compassion'),
        'OriginalLetterURL': 'original_letter_url',
        'TransactionId': None,
        'IsMarkedForRework': None,
        'ResasonForRework': None,
        'ReworkComments': None,
        'Template': ('template_id.layout',
                     'sponsorship.correspondence.template'),
        'TranslatedBy': None,
        'TranslationLanguage': ('destination_language_id.name',
                                'res.lang.compassion'),
        'Supporter': SUPPORTER_MAPPING
    }

    FIELDS_TO_SUBMIT = {
        'Beneficiary.LocalId': None,
        'Beneficiary.CompassId': None,
        'GlobalPartner.Id': None,
        'Supporter.CompassConstituentId': None,
        'Supporter.GlobalId': None,
        'Direction': None,
        'Pages': None,
        'RelationshipType': None,
        'SBCGlobalStatus': None,
        'GlobalPartnerSBCId': str,
        'OriginalLanguage': None,
        'OriginalLetterURL': None,
        'Template': None,
        'SourceSystem': None,
        'NumberOfPages': None,
    }

    CONSTANTS = {
        'SourceSystem': 'Odoo',
        'GlobalPartner.Id': 'CH',
        'Supporter.CompassConstituentId': '7-3655245',  # TODO: Remove and
                                                        # fetch properly
        'Pages': [],     # TODO : See how to send info about pages
        'NumberOfPages': 1,     # TODO
    }

    def _process_odoo_data(self, odoo_data):
        # Replace child and correspondant values with sponsorship
        if 'child_id' in odoo_data and 'correspondant_id' in odoo_data:
            sponsorship = self.env['recurring.contract'].search([
                ('correspondant_id', '=', odoo_data['correspondant_id']),
                ('child_id', '=', odoo_data['child_id'])], limit=1)
            del odoo_data['child_id']
            del odoo_data['correspondant_id']
            if sponsorship:
                odoo_data['sponsorship_id'] = sponsorship.id
