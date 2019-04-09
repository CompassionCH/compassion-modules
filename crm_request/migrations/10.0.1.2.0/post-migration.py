# -*- coding: utf-8 -*-
#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>


def migrate(cr, version):
    if not version:
        return

    # Remove all alias that was created by
    cr.execute(""" UPDATE crm_claim SET email_origin = email_from; """)
    cr.execute(""" DELETE FROM res_partner WHERE type = 'email_alias'
        and email = 'xivo@xivo2016.sokl.ch'; """)
