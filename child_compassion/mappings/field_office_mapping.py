# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class FieldOfficeMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.field.office'

    CONNECT_MAPPING = {
        "BeneficiaryHighRisk_Name": ('high_risk_ids.name', 'fo.high.risk'),
        "ActiveDate": 'date_start',
        "AlternateAddressCountry": 'country',
        "Country": ('country_id.name', 'res.country'),
        "CountryInformationContent": 'country_information',
        "Currency": 'currency',
        "FieldOfficeDirector": 'country_director',
        "FieldOffice_ID": 'field_office_id',
        "IssueResolutionEmailAddress": 'issue_email',
        "LanguagesTranslated": ('translated_language_ids.name',
                                'res.lang.compassion'),
        "FieldOffice_Name": 'name',
        "NumberOfFieldOfficeStaff": 'staff_number',
        "Phone": 'phone_number',
        "PrimaryAddressCity": 'city',
        "PrimaryAddressCountryDivision": 'province',
        "PrimaryAddressPostalCode": 'zip_code',
        "PrimaryAddressStreet": 'street',
        "PrimaryLanguage": ('primary_language_id.name',
                            'res.lang.compassion'),
        "RegionName": 'region',
        "SocialMedia": 'social_media_site',
        "SpokenLanguage": ('spoken_language_ids.name',
                           'res.lang.compassion'),
        "Website": 'website',

        # Not used in Odoo
        "AlternateAddressCity": None,
        "AlternateAddressCountryDivision": None,
        "AlternateAddressPostalCode": None,
        "AlternateAddressStreet": None,
        "Fax": None,
        "SourceKitName": None
    }

    FIELDS_TO_SUBMIT = {
        'gpid': None,
    }

    def __init__(self, env):
        super(FieldOfficeMapping, self).__init__(env)
        self.CONSTANTS = {'gpid': env.user.country_id.code}
