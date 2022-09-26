##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models, fields, _


class ConnectMultipicklist(models.AbstractModel):
    _name = "connect.multipicklist"
    _description = "Connect Multipicklist"
    _inherit = ["mail.activity.mixin", "mail.thread"]

    name = fields.Char(required=True, translate=False)
    res_model = "connect.multipicklist"
    res_field = "id"

    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            _("You cannot have two picklist values with same name."),
        )
    ]

    
    def get_res_view(self):
        """
        Method to find all children given a property
        :return: Tree view of records having that property
        """
        res_ids = self.get_res_ids()
        return {
            "type": "ir.actions.act_window",
            "name": "Related records",
            "res_model": self.res_model,
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["id", "in", res_ids]],
        }
    
    def get_res_ids(self):
        """
        :return: Recordset of records having a given property
        """
        res_ids = list()
        for prop_id in self.ids:
            res_ids.extend(
                self.env[self.res_model].search([(prop_id, "in", self.res_field)]).ids
            )
        return res_ids

    def assign_translation(self):
        """Assign an activity for manually translating the value."""
        notify_ids = (
            self.env["res.config.settings"].sudo().get_param(
                "translate_notify_ids")
        )
        # Remove previous todos
        self.activity_unlink("mail.mail_activity_data_todo")
        if notify_ids:  # check if not False
            for user_id in notify_ids[0][2]:
                act_vals = {
                    "user_id": user_id
                }
                self.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("A new value needs translation"),
                    note=_(
                        "This is a new value that needs translation "
                        "for printing the child dossier."),
                    **act_vals
                )
