# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Find revisions and put subject in them
    rev_obj = env['partner.communication.revision']
    revisions = rev_obj.search([])
    remove_html_pattern = re.compile(r'<.*?>')
    for revision in revisions:
        raw_subject = revision.config_id.email_template_id.with_context(
            lang=revision.lang).subject
        if not raw_subject:
            continue
        html_subject = revision.with_context(
            unstore_keywords=True)._simplify_text(raw_subject)
        revision.subject = remove_html_pattern.sub("", html_subject)
