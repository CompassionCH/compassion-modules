##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        INSERT INTO mobile_app_messages(partner_id)
        SELECT id FROM res_partner;
        UPDATE res_partner p
        SET app_messages = (
            SELECT id FROM mobile_app_messages
            WHERE partner_id = p.id
        );
    """)
