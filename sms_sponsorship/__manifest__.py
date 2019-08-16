# -*- coding: utf-8 -*-
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
    'version': '10.0.1.0.1',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['crm_compassion', 'cms_form_compassion', 'link_tracker',
                'website_no_index'],
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
    'installable': False,
    'auto_install': False,
}
