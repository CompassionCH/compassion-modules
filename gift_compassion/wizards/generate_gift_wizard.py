##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models

logger = logging.getLogger(__name__)


class GenerateGiftWizard(models.TransientModel):
    """This wizard generates a Gift Invoice for a given contract."""

    _inherit = "generate.gift.wizard"

    def generate_invoice(self, due_date=None):
        """
        Only generate invoice if no_birthday_invoice parameter is not set.
        Otherwise generate only the gift.
        :param gift_wizard: a generate_gift_wizard record
        :param contract:  the sponsorship
        :return: None
        """
        for contract_id in self.contract_ids:
            if contract_id.no_birthday_invoice:

                gift_obj = self.env["sponsorship.gift"]
                birthday_gift_type = self.env.ref(
                "sponsorship_compassion.gift_type_birthday"
            )
            gift_vals = {"sponsorship_gift_type_id": birthday_gift_type.id}
                gift_date = self.compute_date_birthday_invoice(
                    contract_id.child_id.birthdate
                )
                # Search that a gift is not already pending
                existing_gifts = gift_obj.search(
                    [
                        ("sponsorship_id", "=", contract_id.id),
                        ("gift_date", ">=", gift_date.replace(day=1, month=1)),
                        ("gift_date", "<=", gift_date.replace(day=31, month=12)),
                        ("gift_type_id", "=", birthday_gift_type.id
                        ),
                    ]
                )
                if not existing_gifts:
                    # Create a gift record
                    gift_vals["sponsorship_id"] = contract_id.id
                    gift_vals["date_partner_paid"] = gift_date
                    gift_vals["gift_date"] = gift_date
                    gift_vals["amount"] = contract_id.birthday_invoice
                    gift_obj.create(gift_vals)
                self.contract_ids-=contract_id
        super().generate_invoice(due_date)

    def compute_date_birthday_invoice(self, child_birthdate, payment_date=None):
        """Set date of invoice two months before child's birthdate"""
        if payment_date is None:
            payment_date = datetime.today()
        inv_date = payment_date.date()
        birthdate = child_birthdate
        new_date = inv_date
        if birthdate.month >= inv_date.month + 2:
            new_date = inv_date.replace(day=28, month=birthdate.month - 2)
        elif birthdate.month + 3 < inv_date.month:
            new_date = birthdate.replace(
                day=28, year=inv_date.year + 1
            ) + relativedelta(months=-2)
            new_date = max(new_date, inv_date)
        return new_date
