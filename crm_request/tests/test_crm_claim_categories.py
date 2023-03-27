##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.exceptions import ValidationError
from odoo.tests import SingleTransactionCase


class TestCrmClaimCategories(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_category_creation_unique_keywords(self):
        keywords = ["test", "test2", "test3"]
        new_category = self.env["crm.claim.category"].create(
            {"name": "TestCategory", "keywords": keywords}
        )
        self.assertEqual(new_category.name, "TestCategory")
        self.assertEqual(len(new_category.keywords.split(",")), 3)

        keywords2 = ["test4", "test5", "test6"]
        new_category_2 = self.env["crm.claim.category"].create(
            {"name": "TestCategory2", "keywords": keywords2}
        )
        self.assertEqual(new_category_2.name, "TestCategory2")
        self.assertEqual(len(new_category_2.keywords.split(",")), 3)

        with self.assertRaises(ValidationError) as e:
            self.env["crm.claim.category"].create(
                {"name": "TestCategory3", "keywords": keywords2}
            )
        self.assertIn(
            "One keyword must be unique over all types"
            " and not be included in another keyword",
            str(e.exception),
        )
