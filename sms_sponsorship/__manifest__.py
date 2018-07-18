# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

{
    'name': 'Compassion SMS Sponsorships',
    'version': '10.0.0.1.0',
    'category': 'Other',
    'author': 'Compassion CH, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['crm_compassion', 'cms_form', 'sponsorship_compassion'],
    'data': [
        'templates/sms_registration_form.xml',
        'templates/assets.xml'
    ],
    'installable': True,
    'auto_install': False,
}
