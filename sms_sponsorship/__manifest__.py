##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
# pylint: disable=C8101
{
    'name': 'Compassion SMS Sponsorships',
    'version': '11.0.1.0.2',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'crm_compassion',  # compassion-modules
        'cms_form_compassion',  # compassion-modules
        'link_tracker',  # source/addons
        'website_no_index',  # Compassion's fork of OCA/website
        'base_phone',  # OCA/connector_telephony
        'stock',  # source/addons
        'payment_ogone'  # source/addons
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'data/sms_crons.xml',
        'data/utm_medium.xml',
        'data/transaction_server_actions.xml',
        'views/event_compassion_view.xml',
        'views/hold_view.xml',
        'views/sms_child_request_view.xml',
        'views/notification_settings_view.xml',
        'templates/assets.xml',
        'templates/sms_registration_confirmation_template.xml',
    ],
    'installable': True,
    'auto_install': False,
}
