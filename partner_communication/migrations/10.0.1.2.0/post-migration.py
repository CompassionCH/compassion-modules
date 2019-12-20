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

    attachments = env['partner.communication.attachment'].search([
        ('report_name', '!=', False),
        ('communication_id', '!=', False)
    ])

    for attachment in attachments:
        report_id =\
            env['report']._get_report_from_name(attachment.report_name).id
        attachment.report_id = report_id
        attachment.attachment_id.report_id = report_id
