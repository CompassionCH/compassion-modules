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
    'version': '10.0.0.2.0',
    'category': 'Other',
    'author': 'Compassion CH, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['crm_compassion', 'cms_form', 'sponsorship_compassion'],
    'data': [
        'templates/sms_registration_form.xml',
        'templates/assets.xml',
        'security/ir.model.access.csv',
        'data/sms_hold_release.xml',
        'views/event_compassion_view.xml',
        'views/hold_view.xml',
        'views/sms_child_request_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
