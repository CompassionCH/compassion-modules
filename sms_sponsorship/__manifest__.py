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
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': ['crm_compassion', 'cms_form', 'base_phone'],
    'data': [
        'data/sms_hold_release.xml'
    ],
    'installable': True,
    'auto_install': False,
}
