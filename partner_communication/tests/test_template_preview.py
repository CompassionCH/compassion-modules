from odoo.tests.common import TransactionCase


class TestTemplatePreview(TransactionCase):
    """The preview of a communication template renders a communication of a
    rule using it (T3523)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        job_model = cls.env["ir.model"]._get("partner.communication.job")
        cls.template = cls.env["mail.template"].create(
            {
                "name": "T3523 preview",
                "model_id": job_model.id,
                "body_html": "<p>Hello <t t-out='object.config_id.name'/></p>",
            }
        )
        cls.config = cls.env.ref("partner_communication.default_communication").copy(
            {"name": "T3523 preview rule", "email_template_id": cls.template.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "T3523 preview"})

    def _preview(self):
        return self.env["mail.template.preview"].create(
            {"mail_template_id": self.template.id}
        )

    def test_preview_uses_a_communication_of_the_template(self):
        job = self.env["partner.communication.job"].create(
            {"partner_id": self.partner.id, "config_id": self.config.id}
        )
        # A newer communication of another rule
        self.env["partner.communication.job"].create(
            {
                "partner_id": self.partner.id,
                "config_id": self.env.ref(
                    "partner_communication.default_communication"
                ).id,
            }
        )
        preview = self._preview()
        self.assertEqual(preview.resource_ref, job)
        self.assertFalse(preview.error_msg)

    def test_preview_without_communication_says_so(self):
        preview = self._preview()
        self.assertFalse(preview.resource_ref)
        self.assertTrue(preview.error_msg)
