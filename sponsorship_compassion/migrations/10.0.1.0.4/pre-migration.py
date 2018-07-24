# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Move fields in another module
    openupgrade.update_module_moved_fields(
        cr, 'account.invoice', ['invoice_type'], 'sponsorship_switzerland',
        'sponsorship_compassion')
    openupgrade.update_module_moved_fields(
        cr, 'res.partner',
        ['is_church', 'church_id', 'church_member_count', 'member_ids'],
        'partner_compassion', 'sponsorship_compassion')
    openupgrade.rename_xmlids(
        cr,
        [('partner_compassion.res_partner_category_church',
          'sponsorship_compassion.res_partner_category_church')])
