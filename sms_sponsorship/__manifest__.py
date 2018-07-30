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
    'version': '10.0.0.4.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['crm_compassion', 'cms_form', 'link_tracker'],
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'data/sms_event_hold_cron.xml',
        'data/utm_medium.xml',
        'views/event_compassion_view.xml',
        'views/hold_view.xml',
        'views/sms_child_request_view.xml',
        'views/notification_settings_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
