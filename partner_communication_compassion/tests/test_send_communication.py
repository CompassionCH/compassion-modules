##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

MODULE = "partner_communication_compassion."


# post_install: runs without -u on a copy of production (no data change)
@tagged("post_install", "-at_install")
class TestSendCommunication(TransactionCase):
    """send_communication picks the communication of each partner from that
    partner's own letters, whatever else is in the batch (T3477)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Built here, no demo data: the tests also run on a copy of production
        partner = cls.env["res.partner"].create({"name": "T3477 payer"})
        group = cls.env["recurring.contract.group"].create(
            {
                "partner_id": partner.id,
                "advance_billing_months": 1,
                "recurring_value": 1,
                "recurring_unit": "month",
            }
        )
        cls.sponsorship = cls.env["recurring.contract"].create(
            {
                "reference": "T3477-test",
                "type": "S",
                "partner_id": partner.id,
                "correspondent_id": partner.id,
                "group_id": group.id,
            }
        )

    def _create_b2s_letter(self, name, vals=None):
        partner = self.env["res.partner"].create({"name": name})
        return self.env["correspondence"].create(
            {
                "sponsorship_id": self.sponsorship.id,
                "partner_id": partner.id,
                "direction": "Beneficiary To Supporter",
                **(vals or {}),
            }
        )

    def test_first_letter_of_one_partner_does_not_change_the_others(self):
        new_sponsor = self.env.ref("sbc_compassion.correspondence_type_new_sponsor")
        first_letter = self._create_b2s_letter(
            "Sponsor A", {"communication_type_ids": [(6, 0, new_sponsor.ids)]}
        )
        moment_letter = self._create_b2s_letter(
            "Sponsor B", {"is_compassion_moment": True}
        )
        new_letter = self._create_b2s_letter("Sponsor C")

        configs = {}

        def generate_communication(letters, config):
            for letter in letters:
                configs[letter] = config
            return True

        letters = first_letter | moment_letter | new_letter
        # force_send: the test sponsorship stays in draft
        with patch.object(
            type(letters), "_generate_communication", generate_communication
        ):
            letters.with_context(force_send=True).send_communication()

        def config(xmlid):
            return self.env.ref(MODULE + xmlid)

        self.assertEqual(
            configs[first_letter], config("config_onboarding_first_letter")
        )
        self.assertEqual(configs[moment_letter], config("child_letter_moment_config"))
        self.assertEqual(configs[new_letter], config("child_letter_config"))
