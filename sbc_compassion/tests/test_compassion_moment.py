##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests import TransactionCase, tagged


# post_install: runs without -u on a copy of production (no data change)
@tagged("post_install", "-at_install")
class TestCompassionMoment(TransactionCase):
    """A B2S letter is a Compassion Moment when its GMC template is a 1S10 one.

    GMC puts the country before the template code and a version after it, and
    sends two families of 1S10 templates (C and G): every one of them is a
    Compassion Moment (T3477). The names below are real ones received from GMC.
    """

    def _is_compassion_moment(self, template_name):
        data = self.env["correspondence"].json_to_data({"Template": template_name})
        return data["is_compassion_moment"]

    def test_1s10_templates_are_compassion_moments(self):
        for template_name in ("UG-C-1S10-2", "TG-G-1S10-1", "MX-C-1S10-2"):
            with self.subTest(template=template_name):
                self.assertTrue(self._is_compassion_moment(template_name))

    def test_other_templates_are_not_compassion_moments(self):
        for template_name in ("UG-E-5S12-1", "BF-E-4S01-1", "CH-A-1S11-1"):
            with self.subTest(template=template_name):
                self.assertFalse(self._is_compassion_moment(template_name))

    def test_missing_template_is_not_a_compassion_moment(self):
        """No template, or an empty one, falls back to our own template."""
        self.assertFalse(
            self.env["correspondence"].json_to_data({})["is_compassion_moment"]
        )
        for template_name in (None, ""):
            with self.subTest(template=template_name):
                self.assertFalse(self._is_compassion_moment(template_name))
