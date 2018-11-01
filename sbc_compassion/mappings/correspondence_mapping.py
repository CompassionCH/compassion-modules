# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
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
        'CompassConstituentId': None,
        'GlobalId': ('partner_id.global_id', 'res.partner'),
        'MandatoryReviewRequired': 'mandatory_review',
        'ObjectUrl': None,
        'PreferredName': ('partner_id.preferred_name', 'res.partner'),
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
        'Beneficiary.GlobalId': None,
        'GlobalPartner.Id': None,
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
    }

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        """
        Change mapping in order to send the translated language as original
        language to GMC. This is because we translate the letter locally
        and want to keep the original language in our system, but we transmit
        the translated language to avoid the letter going into Field Office
        Translation Queue.
        :param odoo_object: correspondence object
        :param fields_to_submit: dict of fields to submit
        :return: connect data
        """
        res = super(CorrespondenceMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        res['OriginalLanguage'] = odoo_object.translation_language_id.name
        return res

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Replace mapping for template to look for B2S templates.
        """
        if connect_name == 'Template' and not value.startswith('CH'):
            value_mapping = ('b2s_layout_id.code', 'correspondence.b2s.layout')
            # Value is FO-X-YYYY-Z and we are only interested in YYYY
            # which holds the template code (like 1S11 for layout 1)
            value = value[5:9]

        result = super(CorrespondenceMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search)

        if connect_name == 'GlobalPartnerSBCId':
            # Cast to int
            result[value_mapping] = int(value)

        return result

    def _process_odoo_data(self, odoo_data):
        # Replace child and correspondant values with sponsorship
        if 'child_id' in odoo_data and 'partner_id' in odoo_data:
            partner_id = odoo_data.pop('partner_id')
            child_id = odoo_data.pop('child_id')
            sponsorship = self.env['recurring.contract'].search([
                ('correspondent_id', '=', partner_id),
                ('child_id', '=', child_id)], limit=1)
            if not sponsorship:
                # We can have multiple partners with same global_id :(
                partner = self.env['res.partner'].browse(partner_id)
                sponsorship = self.env['recurring.contract'].search([
                    ('correspondent_id.global_id', '=', partner.global_id),
                    ('child_id', '=', child_id)], limit=1)
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
