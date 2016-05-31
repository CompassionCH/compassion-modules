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
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class CorrespondenceMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship Correspondence.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'correspondence'

    BENEFICIARY_MAPPING = {
        'Age': None,
        'CompassId': ('child_id.compass_id', 'compassion.child'),
        'Gender': None,
        'GlobalId': ('child_id.global_id', 'compassion.child'),
        'LocalId': ('child_id.local_id', 'compassion.child'),
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

    SUPPORTER_MAPPING = {
        'CompassConstituentId': ('correspondant_id.ref', 'res.partner'),
        'CommunicationDeliveryPreference': None,  # Todo Where to find this ?
        'GlobalId': None,
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
        'Pages': ('page_ids', 'correspondence.page'),
        'Direction': 'direction',
        'PrintType': None,
        'RelationshipType': 'relationship',
        'SBCGlobalStatus': 'state',
        'Status': 'state',
        'SBCTypes': ('communication_type_ids.name',
                     'correspondence.type'),
        'CompassionSBCId': 'kit_identifier',
        'FinalLetterURL': 'final_letter_url',
        'GlobalPartnerSBCId': 'id',
        'IsFinalLetter': None,
        'IsFinalLetterArchived': None,
        'IsOriginalLetterArchived': None,
        'IsOriginalLetterMailed': None,
        'ItemNotScannedEligible': None,
        'ItemNotScannedNotEligible': None,
        'NumberOfPages': 'nbr_pages',
        'OriginalLanguage': ('original_language_id.name',
                             'res.lang.compassion'),
        'OriginalLetterURL': 'original_letter_url',
        'TransactionId': None,
        'MarkedForRework': 'marked_for_rework',
        'ReasonForRework': 'rework_reason',
        'ReworkComments': 'rework_comments',
        'Template': ('template_id.layout',
                     'correspondence.template'),
        'TranslatedBy': 'translator',
        'TranslationLanguage': ('translation_language_id.name',
                                'res.lang.compassion'),
        'Supporter': SUPPORTER_MAPPING
    }

    FIELDS_TO_SUBMIT = {
        'Beneficiary.LocalId': None,
        'GlobalPartner.Id': None,
        'Supporter.CompassConstituentId': lambda id: '65-' + id,
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
    }

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Remove 65- suffix from partner reference and look only
            for non-company partners.
            Replace mapping for template to look for B2S templates.
        """
        if connect_name == 'CompassConstituentId':
            value = value[3:]
            relation_search = [('is_company', '=', False)]
        if connect_name == 'Template' and not value.startswith('CH'):
            value_mapping = ('b2s_layout_id.code', 'correspondence.b2s.layout')
            # Value is FO-X-YYYY-Z and we are only interested in YYYY
            # which holds the template code (like 1S11 for layout 1)
            value = value[5:9]
        return super(CorrespondenceMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)

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
        # Replace dict by a tuple for the ORM update/create
        if 'page_ids' in odoo_data:
            pages = list()
            for page in odoo_data['page_ids']:
                page_url = page.get('original_page_url')
                if not page_url:
                    # We don't need to save pages not accessible
                    continue
                page_id = self.env['correspondence.page'].search(
                    [('original_page_url', '=', page_url)], limit=1).id
                # if page_url already exist update it
                if page_id:
                    orm_tuple = (1, page_id, page)
                # else create a new one
                else:
                    orm_tuple = (0, 0, page)
                pages.append(orm_tuple)
            odoo_data['page_ids'] = pages or False
