# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.fs_folder import fields as fs_fields

SHARED_FOLDER_NAME = "Shared"


class HrEmployeeSharedFolder(models.Model):
    """Folder shared read-only with the employee.

    The employees cannot read hr.employee (HR only), and every employee can
    read every public profile (hr.employee.public) and every user (res.users):
    none of them can carry a folder that only its employee may see. This model
    can, with a record rule on its user.
    """

    _name = "hr.employee.shared.folder"
    _description = "Employee Shared Documents Folder"
    _rec_name = "employee_id"

    employee_id = fields.Many2one(
        "hr.employee", required=True, ondelete="cascade", index=True
    )
    user_id = fields.Many2one(related="employee_id.user_id", store=True, index=True)
    company_id = fields.Many2one(related="employee_id.company_id", store=True)
    folder = fs_fields.FsFolder(
        string="My Documents",
        create_parent_get="_get_folder_parent",
        create_name_get="_get_folder_name",
    )

    _sql_constraints = [
        (
            "employee_uniq",
            "unique(employee_id)",
            "An employee has only one shared documents folder.",
        )
    ]

    def _get_folder_parent(self, field, fs):
        return {
            shared.id: shared.sudo().employee_id.hr_document_folder.ref.split("/")
            for shared in self
        }

    def _get_folder_name(self, field, fs):
        return dict.fromkeys(self.ids, SHARED_FOLDER_NAME)

    @api.model
    def action_open_my_documents(self):
        shared = self.search([("user_id", "=", self.env.uid)], limit=1)
        if not shared.folder:
            raise UserError(_("You have no documents folder yet."))
        view = self.env.ref("hr_employee_fs_folder.view_shared_folder_form")
        return {
            "type": "ir.actions.act_window",
            "name": _("My Documents"),
            "res_model": self._name,
            "res_id": shared.id,
            "view_mode": "form",
            "views": [(view.id, "form")],
            "target": "current",
        }
