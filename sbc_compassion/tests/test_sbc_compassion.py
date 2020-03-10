##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import logging
import os
from os import path

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

logger = logging.getLogger(__name__)

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data/"


class TestSbcCompassion(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()

        self.t_child = self.create_child("TT123456789")
        self.t_partner = self.env.ref("base.res_partner_address_31")
        t_group = self.create_group({"partner_id": self.t_partner.id})
        self.t_sponsorship = self.create_contract(
            {
                "partner_id": self.t_partner.id,
                "group_id": t_group.id,
                "child_id": self.t_child.id,
            },
            [{"amount": 50.0}],
        )

        self.list_files_path = [path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)]

        self.t_partner.write({"global_id": "12345678", "ref": "1231234"})

        self.validate_sponsorship(self.t_sponsorship)
        self.t_sponsorship.force_activation()

    def test_base(self):
        self.assertEqual(self.t_sponsorship.child_id.local_id, "TT123456789")
        self.assertEqual(self.t_sponsorship.partner_id.global_id, "12345678")
        self.assertEqual(self.t_sponsorship.state, "active")

    def test_import_pdf(self):
        """
            This test import the pdf include in the folder /data and verify the
            data's integrity.
        """
        list_data = []

        #  tuple with
        for file_path in self.list_files_path:
            with open(file_path, "rb") as f:
                list_data.append(
                    (
                        0,
                        False,
                        {
                            "name": f.name.split("/")[-1],
                            "datas": base64.b64encode(f.read()),
                        },
                    )
                )

        import_letter = (
            self.env["import.letters.history"]
                .with_context(async_mode=False)
                .create({"data": list_data})
        )

        import_letter.button_import()
        self.assertEqual(len(import_letter.import_line_ids), 6)

        # Check the import line
        for line in import_letter.import_line_ids:
            if line.file_name.startswith("Dove"):
                self.assertEqual(line.template_id.name, "Dove")
                self.assertEqual(line.partner_id.name, "Edward Foster")
                self.assertEqual(line.child_id.display_name, "TT123456789")
            if line.file_name.startswith("Postman"):
                self.assertEqual(line.template_id.name, "Postman")
