# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


# Warning: This migration can take a long time!
@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return
    cr = env.cr

    cr.execute("ALTER TABLE partner_communication_attachment "
               "ADD COLUMN IF NOT EXISTS report_id INTEGER")

    cr.execute("SELECT id FROM partner_communication_attachment")
    communication_ids = cr.dictfetchall()

    for communication_id in communication_ids:
        communication_object = env['partner.communication.attachment'].search([
            ('id', '=', communication_id['id'])
        ])

        report_name = communication_object.report_name
        communication_object.report_id = \
            env['report']._get_report_from_name(report_name).id
