# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Correct SUB - parent relations
    broken_subs = env['recurring.contract'].search([
        ('parent_id', '!=', False),
        ('child_id', '!=', False),
        ('parent_id.sub_sponsorship_id', '=', False)
    ])
    for sub in broken_subs:
        sub.parent_id.sub_sponsorship_id = sub
    broken_subs = env['recurring.contract'].search([
        ('sub_sponsorship_id', '!=', False),
        ('child_id', '!=', False),
        ('sub_sponsorship_id.parent_id', '=', False)
    ])
    for sub in broken_subs:
        sub.sub_sponsorship_id.parent_id = sub

    # Remove subs that are invalid
    invalid_subs = env['recurring.contract'].search([
        ('parent_id', '!=', False),
        '|',
        '&', ('child_id', '=', False), ('state', '!=', 'draft'),
        ('parent_id.state', 'not in', ('terminated', 'cancelled'))
    ])
    invalid_subs.with_context(allow_removing_sub=True).write({
        'parent_id': False})

    # Set sponsorship_line_id
    new_sponsorships = env['recurring.contract'].search([
        ('child_id', '!=', False),
        ('activation_date', '!=', False),
        ('parent_id', '=', False),
    ], order='activation_date asc')
    line_id = 1
    for sponsorship in new_sponsorships:
        sponsorship.sponsorship_line_id = line_id
        sub_sponsorship = sponsorship.sub_sponsorship_id
        while sub_sponsorship:
            sub_sponsorship.sponsorship_line_id = line_id
            sub_sponsorship = sub_sponsorship.sub_sponsorship_id
        line_id += 1

    # Find missed sponsorships (with parent not in sponsorship line)
    new_sponsorships = env['recurring.contract'].search([
        ('child_id', '!=', False),
        ('activation_date', '!=', False),
        ('parent_id.sponsorship_line_id', '=', False)
    ], order='activation_date asc')
    for sponsorship in new_sponsorships:
        sponsorship.sponsorship_line_id = line_id
        sub_sponsorship = sponsorship.sub_sponsorship_id
        while sub_sponsorship:
            sub_sponsorship.sponsorship_line_id = line_id
            sub_sponsorship = sub_sponsorship.sub_sponsorship_id
        line_id += 1
