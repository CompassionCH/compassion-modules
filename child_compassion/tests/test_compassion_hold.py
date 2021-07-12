##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import mock
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo.tests import TransactionCase

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)


class TestHold(TransactionCase):

    @mock.patch(mock_update_hold)
    def test_no_date_change_after_expiration(self, update_hold):
        """
        Assert changing the expiration date of an already expired hold
        will throw an error
        """

        update_hold.return_value = True

        test_hold = self.env["compassion.hold"].create({
            "expiration_date": datetime.now() - relativedelta(day=1)
        })

        self.assertRaises(UserError, test_hold.write, {"expiration_date": datetime.now()})
