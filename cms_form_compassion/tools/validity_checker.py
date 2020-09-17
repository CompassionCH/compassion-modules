##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta, datetime


def is_expired(obj):
    """
    This function is used by confirmation endpoints to check if they have
    expired.
    """
    expire = obj.sudo().create_date + timedelta(days=1)
    return expire < datetime.now()
