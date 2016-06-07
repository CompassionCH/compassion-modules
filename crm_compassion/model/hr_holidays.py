# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


class HrHolidays(models.Model):
    _inherit = "hr.holidays"

    @api.multi
    def holidays_validate(self):
        """
        Put all_day in holidays spanning in multiple days.
        Put user requesting holidays as attendee instead of connected user.
        """
        super(HrHolidays, self).holidays_validate()
        for holidays in self:
            if holidays.meeting_id and holidays.date_from and holidays.date_to:
                partner_id = holidays.employee_id.address_home_id.id
                holidays.meeting_id.write({
                    'allday':
                        holidays.date_from[0:10] != holidays.date_to[0:10],
                    'partner_ids': [(6, 0, [partner_id])] if partner_id else
                        False,
                    'start': holidays.date_from,
                    'stop': holidays.date_to,
                })
        return True
