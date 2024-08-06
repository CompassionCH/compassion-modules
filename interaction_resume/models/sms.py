from odoo import fields, models


class Sms(models.Model):
    _inherit = ["sms.sms", "interaction.source"]
    _name = "sms.sms"

    date = fields.Datetime(related="create_date", search="_search_date")

    def _search_date(self, operator, value):
        return [("create_date", operator, value)]

    def _get_interaction_data(self, partner_id):
        return [
            {
                "partner_id": partner_id,
                "res_model": self._name,
                "res_id": rec.id,
                "direction": "out",
                "date": rec.create_date,
                "communication_type": "SMS",
                "body": rec.body,
                "subject": rec.body[:50] + "..." if len(rec.body) > 50 else rec.body,
                "tracking_status": rec.state,
            }
            for rec in self
        ]

    def _postprocess_iap_sent_sms(
        self, iap_results, failure_reason=None, delete_all=False
    ):
        # Purpose is to avoid deleting SMS since we use them in interaction resume.
        return super(
            Sms, self.with_context(postprocess_iap=True)
        )._postprocess_iap_sent_sms(iap_results, failure_reason, delete_all)

    def unlink(self):
        if not self.env.context.get("postprocess_iap"):
            return super().unlink()
        # The SMS are not deleted,
        # but we need to update the state to avoid sending them again.
        return self.write({"state": "sent"})
