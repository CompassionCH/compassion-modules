# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class FsFolderFieldWebApi(models.AbstractModel):
    _inherit = "fs.folder.field.web.api"

    @api.model
    def initialize_field_value(self, res_id, res_model, field_name, **kwargs):
        """The "Create Folder" button of the widget creates both folders.

        It goes through action_create_document_folders, which works around
        fs_folder reading fs.storage with the rights of the user.
        """
        if (res_model, field_name) == ("hr.employee", "hr_document_folder"):
            self.env["hr.employee"].browse(res_id).action_create_document_folders()
            return None
        if (res_model, field_name) == ("hr.employee.shared.folder", "folder"):
            shared = self.env["hr.employee.shared.folder"].browse(res_id)
            shared.check_access("write")
            shared.sudo().employee_id.action_create_document_folders()
            return None
        return super().initialize_field_value(res_id, res_model, field_name, **kwargs)
