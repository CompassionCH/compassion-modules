# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from functools import partial

from odoo import _, api, fields, models, registry
from odoo.exceptions import UserError

from odoo.addons.fs_folder import fields as fs_fields

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    hr_document_folder = fs_fields.FsFolder(
        string="HR Documents",
        groups="hr.group_hr_user",
        create_parent_get="_get_hr_document_folder_parent",
        create_name_get="_get_hr_document_folder_name",
    )
    shared_folder_ids = fields.One2many(
        "hr.employee.shared.folder", "employee_id", groups="hr.group_hr_user"
    )

    # ------------------------------------------------------------------
    # Folder location: <id> - <name>, the shared folder is its "Shared"
    # subfolder (fs_folder calls the hooks with (field, fs))
    # ------------------------------------------------------------------
    def _get_hr_document_folder_dirname(self):
        self.ensure_one()
        return f"{self.id} - {self.name}"

    def _get_hr_document_folder_parent(self, field, fs):
        return {employee.id: [] for employee in self}

    def _get_hr_document_folder_name(self, field, fs):
        return {
            employee.id: employee._get_hr_document_folder_dirname() for employee in self
        }

    @api.model
    def _is_document_folder_storage_configured(self):
        try:
            self.env["fs.storage"].get_default_storage_code_for_fs_content(
                "hr.employee", "hr_document_folder"
            )
        except ValueError:
            return False
        return True

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    def action_create_document_folders(self):
        """Create the HR folder of the employees and their shared subfolder.

        fs_folder reads fs.storage without sudo when it creates a folder
        (create_value_in_fs -> fs.storage.get_by_code), which users that are
        not system administrators cannot read (and must not: it holds the
        storage credentials). Check the access on the employee, then sudo.
        """
        self.check_access("write")
        for employee in self.sudo():
            if not employee.hr_document_folder:
                employee.hr_document_folder.initialize()
            shared = employee.shared_folder_ids[:1] or self.env[
                "hr.employee.shared.folder"
            ].sudo().create({"employee_id": employee.id})
            if not shared.folder:
                shared.folder.initialize()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        if self._is_document_folder_storage_configured():
            for employee in employees:
                employee.with_delay(
                    description=_("Create documents folders of %s", employee.name),
                    identity_key=f"hr_employee_fs_folder_create_{employee.id}",
                )._create_document_folders()
        return employees

    def _create_document_folders(self):
        return self.sudo().action_create_document_folders()

    # ------------------------------------------------------------------
    # Renaming
    # ------------------------------------------------------------------
    def write(self, vals):
        res = super().write(vals)
        if "name" in vals:
            for employee in self.sudo().filtered("hr_document_folder"):
                employee.with_delay(
                    description=_("Rename documents folder of %s", employee.name),
                    identity_key=f"hr_employee_fs_folder_rename_{employee.id}",
                )._rename_hr_document_folder()
        return res

    def _rename_hr_document_folder(self):
        """Rename the HR folder after the name of the employee.

        Idempotent: the target is computed from the current name. The links of
        the shared folders inside it are updated.
        """
        adapter = self.env["fs.folder.field.value.adapter"]
        for employee in self.sudo().filtered("hr_document_folder"):
            value = employee.hr_document_folder
            storage_code = value.storage_code
            storage = self.env["fs.storage"].get_by_code(storage_code)
            fs = self.env["fs.storage"].get_fs_by_code(storage_code)
            old_path = value.ref
            new_path = employee._get_hr_document_folder_dirname()
            if storage.sanitize_fs_name:
                new_path = storage.sanitize_fs_item_name(new_path)
            if new_path == old_path:
                continue
            if not fs.exists(old_path):
                _logger.warning(
                    "HR documents folder %s of employee %s not found on storage "
                    "%s: not renamed (was it moved or deleted on the storage?)",
                    old_path,
                    employee.id,
                    storage_code,
                )
                continue
            if fs.exists(new_path):
                raise UserError(
                    _(
                        "Cannot rename the documents folder of %(employee)s to "
                        "%(path)s: a folder with this name already exists.",
                        employee=employee.name,
                        path=new_path,
                    )
                )
            # recursive=True is required: webdav4 only creates the target
            # directory when moving a directory non-recursively
            fs.mv(old_path, new_path, recursive=True)
            self.env.cr.postrollback.add(
                partial(self._move_folder_back, storage_code, new_path, old_path)
            )
            employee.hr_document_folder = adapter._created_folder_name_to_stored_value(
                new_path, storage_code, fs
            )
            prefix = f"{old_path}/"
            for shared in employee.shared_folder_ids.filtered("folder"):
                shared_value = shared.folder
                if (
                    shared_value.storage_code == storage_code
                    and shared_value.ref.startswith(prefix)
                ):
                    shared.folder = adapter._created_folder_name_to_stored_value(
                        new_path + shared_value.ref[len(old_path) :],
                        storage_code,
                        fs,
                    )
        return True

    @api.model
    def _move_folder_back(self, storage_code, path, original_path):
        """Undo a folder move when the transaction that recorded it is rolled back.

        Runs after the rollback, in a new cursor (like fs_folder's own clean up).
        """
        try:
            with registry(self.env.cr.dbname).cursor() as cr:
                env = api.Environment(cr, self.env.uid, {})
                fs = env["fs.storage"].sudo().get_fs_by_code(storage_code)
                fs.mv(path, original_path, recursive=True)
        except Exception:
            _logger.exception(
                "Could not move documents folder %s back to %s after rollback",
                path,
                original_path,
            )
