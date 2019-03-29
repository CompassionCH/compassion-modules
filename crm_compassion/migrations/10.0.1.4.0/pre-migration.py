# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Remove the paper message in message thread
    try:
        cr.execute("""
                    DELETE FROM mail_message
                    WHERE id = ANY (
                                    SELECT mm.id
                                    FROM  mail_message as mm
                                    INNER JOIN partner_communication_job as pcj
                                    ON pcj.partner_id = mm.res_id
                                    AND pcj.subject = mm.subject
                                    WHERE mm.model LIKE 'res.partner'
                                    AND subtype_id = 43
                                )
                """)
    except:
        cr.rollback()
