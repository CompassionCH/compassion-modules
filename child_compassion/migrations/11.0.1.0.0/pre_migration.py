# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Remove bad space in xml_ids of household duties
    openupgrade.rename_xmlids(cr, [
        ('child_compassion.household_duty _animal',
         'child_compassion.household_duty_animal'),
        ('child_compassion.household_duty _market',
         'child_compassion.household_duty_market'),
        ('child_compassion.household_duty _water',
         'child_compassion.household_duty_water'),
        ('child_compassion.household_duty _childcare',
         'child_compassion.household_duty_childcare'),
        ('child_compassion.household_duty _cleaning',
         'child_compassion.household_duty_cleaning'),
        ('child_compassion.household_duty _gardening',
         'child_compassion.household_duty_cleaning'),
        ('child_compassion.household_duty _firewood',
         'child_compassion.household_duty_firewood'),
        ('child_compassion.household_duty _kitchen',
         'child_compassion.household_duty_kitchen'),
        ('child_compassion.household_duty _makingbed',
         'child_compassion.household_duty_makingbed'),
        ('child_compassion.household_duty _errands',
         'child_compassion.household_duty_errands'),
        ('child_compassion.household_duty _sewing',
         'child_compassion.household_duty_sewing'),
        ('child_compassion.household_duty _teaching',
         'child_compassion.household_duty_teaching'),
        ('child_compassion.household_duty _clothes',
         'child_compassion.household_duty_clothes'),
    ])
