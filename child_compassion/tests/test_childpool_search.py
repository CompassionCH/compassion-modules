##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from ..wizards.global_child_search import ChildpoolNoResultsError


class TestChildpoolAdvancedSearch(TransactionCase):
    def _age_filters(self, wizard):
        return wizard.search_filter_ids.filtered(lambda f: f.field_id.name == "min_age")

    def test_no_results_error_is_a_user_error(self):
        """The sponsor portal imports this class and relies on the subclassing."""
        self.assertTrue(issubclass(ChildpoolNoResultsError, UserError))

    def test_min_age_zero_keeps_age_filter(self):
        """A minimum age of 0 is a valid bound and must be sent to Connect."""
        wizard = self.env["compassion.childpool.search"].create(
            {"min_age": 0, "max_age": 18}
        )
        wizard.compute_advanced_search()
        age_filters = self._age_filters(wizard)
        self.assertEqual(len(age_filters), 1)
        self.assertEqual(age_filters.value, "0;18")

    def test_no_age_given_sends_no_age_filter(self):
        """Without any age bound the query must not contain an age filter."""
        wizard = self.env["compassion.childpool.search"].create({})
        wizard.compute_advanced_search()
        self.assertFalse(self._age_filters(wizard))

    def test_field_office_filter_sends_field_office_code(self):
        """Connect matches the FieldOffice filter on the field office code."""
        office = self.env["compassion.field.office"].create(
            {
                "field_office_id": "T1",
                "name": "Test Field Office",
                "country_id": self.env.ref("base.mx").id,
            }
        )
        wizard = self.env["compassion.childpool.search"].create(
            {"field_office_ids": [(6, 0, office.ids)]}
        )
        wizard.compute_advanced_search()
        fo_filters = wizard.search_filter_ids.filtered(
            lambda f: f.field_id.name == "field_office_ids"
        )
        self.assertEqual(fo_filters.value, "T1")
