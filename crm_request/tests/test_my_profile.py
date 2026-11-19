from odoo.tests import TransactionCase, new_test_user


class TestMyProfile(TransactionCase):
    def test_read_own_profile(self):
        """An employee who is not an HR officer opens "My Profile" (T3604)."""
        user = new_test_user(self.env, login="t3604_profile", groups="base.group_user")
        self.env["hr.employee"].create(
            {
                "name": "T3604 Employee",
                "user_id": user.id,
                "private_email": "t3604@example.org",
            }
        )
        profile = user.with_user(user).web_read(
            {"do_reminder_support_req": {}, "private_email": {}}
        )
        self.assertEqual(profile[0]["private_email"], "t3604@example.org")
