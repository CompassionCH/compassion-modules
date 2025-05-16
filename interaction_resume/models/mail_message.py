from odoo import models


class MailMessage(models.Model):
    _inherit = "mail.message"

    def convert_as_other_interaction(self):
        """Convert the message to an interaction resume"""
        interactions = self.env["partner.log.other.interaction"]
        partner_ids = set()
        for message in self:
            # Create the interaction resume
            partner_id = False
            if message.model == "res.partner":
                partner_id = message.res_id
            elif message.partner_ids:
                partner_id = message.partner_ids[0].id
            else:
                res_model = self.env[message.model]
                if hasattr(res_model, "partner_id"):
                    partner_id = res_model.browse(message.res_id).partner_id.id
            if not partner_id:
                continue
            user = message.author_id.user_ids[:1] or message.create_uid or self.env.user
            if user.share:
                user = self.env.user
            interactions += interactions.with_user(user).create(
                {
                    "partner_id": partner_id,
                    "date": message.date,
                    "communication_type": "Email",
                    "subject": message.subject,
                    "body": message.body,
                    "other_type": "Direct message converted to interaction",
                    "direction": "out" if message.author_id.id != partner_id else "in",
                }
            )
            partner_ids.add(partner_id)
            message.unlink()
        if partner_ids:
            self.env["res.partner"].browse(list(partner_ids)).reset_interactions()
        action = {
            "type": "ir.actions.act_window",
            "name": "Converted Interactions",
            "res_model": "partner.log.other.interaction",
            "view_mode": "tree,form",
            "domain": [("id", "in", interactions.ids)],
            "target": "current",
        }
        if len(interactions) == 1:
            action.update(
                {
                    "res_id": interactions.id,
                    "view_mode": "form",
                }
            )
        return action
