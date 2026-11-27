# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import os
import shutil
import tempfile

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase

FIELDS = [
    ("hr.employee", "hr_document_folder"),
    ("hr.employee.shared.folder", "folder"),
]


class TestHrEmployeeFsFolder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.root = tempfile.mkdtemp()
        cls.addClassCleanup(shutil.rmtree, cls.root)
        fields = cls.env["ir.model.fields"]
        for model, name in FIELDS:
            fields |= fields._get(model, name)
        # a field can be linked to one storage only: detach the configured one
        configured = (
            cls.env["fs.storage"].search([]).filtered(lambda s: s.field_ids & fields)
        )
        configured.write({"field_ids": [(3, field.id) for field in fields]})
        cls.storage = cls.env["fs.storage"].create(
            {
                "name": "HR documents (test)",
                "code": "hr_employee_fs_folder_test",
                "protocol": "file",
                "directory_path": cls.root,
                "check_connection_method": "ls",
                "field_ids": [(6, 0, fields.ids)],
            }
        )
        cls.hr_officer = new_test_user(
            cls.env,
            login="test_hefs_hr",
            groups="base.group_user,hr.group_hr_user",
        )
        cls.user_1 = new_test_user(cls.env, login="test_hefs_emp1", name="Marie Martin")
        cls.user_2 = new_test_user(cls.env, login="test_hefs_emp2", name="Paul Muster")
        cls.employee_1 = (
            cls.env["hr.employee"]
            .with_user(cls.hr_officer)
            .create({"name": "Marie Martin", "user_id": cls.user_1.id})
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {"name": "Paul Muster", "user_id": cls.user_2.id}
        )
        cls.shared_1 = cls.employee_1.sudo().shared_folder_ids
        cls.shared_2 = cls.employee_2.sudo().shared_folder_ids

    def _abs(self, *parts):
        return os.path.join(self.root, *parts)

    def _api(self, user):
        return self.env["fs.folder.field.web.api"].with_user(user)

    def _upload(self, user, model, res_id, field, name, data):
        return self._api(user).upload_file(
            res_id,
            model,
            field,
            path="",
            file_name=name,
            file_data=base64.b64encode(data).decode(),
        )

    def _names(self, user, model, res_id, field):
        children = self._api(user).get_children(res_id, model, field, path="")
        return sorted(os.path.basename(c["name"].rstrip("/")) for c in children)

    def test_folders_created_with_employee(self):
        """Created by the HR officer (no access to fs.storage) through the job."""
        ref = f"{self.employee_1.id} - Marie Martin"
        self.assertEqual(self.employee_1.sudo().hr_document_folder.ref, ref)
        self.assertEqual(self.shared_1.folder.ref, f"{ref}/Shared")
        self.assertEqual(self.shared_1.user_id, self.user_1)
        self.assertTrue(os.path.isdir(self._abs(ref, "Shared")))

    def test_employee_reads_own_shared_folder(self):
        self._upload(
            self.hr_officer,
            "hr.employee.shared.folder",
            self.shared_1.id,
            "folder",
            "certificate.pdf",
            b"%PDF",
        )
        self._upload(
            self.hr_officer,
            "hr.employee",
            self.employee_1.id,
            "hr_document_folder",
            "evaluation.pdf",
            b"%PDF",
        )
        # the employee sees the shared folder only, not the HR folder around it
        self.assertEqual(
            self._names(
                self.user_1, "hr.employee.shared.folder", self.shared_1.id, "folder"
            ),
            ["certificate.pdf"],
        )
        # HR sees everything
        self.assertEqual(
            self._names(
                self.hr_officer, "hr.employee", self.employee_1.id, "hr_document_folder"
            ),
            ["Shared", "evaluation.pdf"],
        )

    def test_employee_cannot_read_other_shared_folder(self):
        with self.assertRaises(AccessError):
            self._names(
                self.user_1, "hr.employee.shared.folder", self.shared_2.id, "folder"
            )

    def test_employee_cannot_read_hr_folder(self):
        with self.assertRaises(AccessError):
            self._names(
                self.user_1, "hr.employee", self.employee_1.id, "hr_document_folder"
            )

    def test_employee_cannot_upload(self):
        with self.assertRaises(AccessError):
            self._upload(
                self.user_1,
                "hr.employee.shared.folder",
                self.shared_1.id,
                "folder",
                "note.txt",
                b"hello",
            )

    def test_employee_cannot_escape_shared_folder(self):
        with self.assertRaises(Exception):  # noqa: B017 (refused by the rooted fs)
            self._api(self.user_1).get_children(
                self.shared_1.id, "hr.employee.shared.folder", "folder", path="../"
            )

    def test_open_my_documents(self):
        action = (
            self.env["hr.employee.shared.folder"]
            .with_user(self.user_1)
            .action_open_my_documents()
        )
        self.assertEqual(action["res_id"], self.shared_1.id)
        nobody = new_test_user(self.env, login="test_hefs_nobody")
        with self.assertRaises(UserError):
            self.env["hr.employee.shared.folder"].with_user(
                nobody
            ).action_open_my_documents()

    def test_rename_employee_renames_folder(self):
        self._upload(
            self.hr_officer,
            "hr.employee.shared.folder",
            self.shared_1.id,
            "folder",
            "certificate.pdf",
            b"%PDF",
        )
        self.employee_1.name = "Marie Dupont"
        ref = f"{self.employee_1.id} - Marie Dupont"
        self.assertEqual(self.employee_1.sudo().hr_document_folder.ref, ref)
        self.assertEqual(self.shared_1.folder.ref, f"{ref}/Shared")
        self.assertEqual(
            self._names(
                self.user_1, "hr.employee.shared.folder", self.shared_1.id, "folder"
            ),
            ["certificate.pdf"],
        )

    def test_create_action_on_existing_employee(self):
        employee = self.env["hr.employee"].with_context(queue_job__no_delay=False)
        employee = employee.create({"name": "Late Employee"})
        self.assertFalse(employee.hr_document_folder)
        employee.with_user(self.hr_officer).action_create_document_folders()
        self.assertTrue(employee.hr_document_folder)
        self.assertEqual(
            employee.shared_folder_ids.folder.ref,
            f"{employee.id} - Late Employee/Shared",
        )

    def test_widget_button_for_hr_officer(self):
        employee = self.env["hr.employee"].with_context(queue_job__no_delay=False)
        employee = employee.create({"name": "Widget Employee"})
        self._api(self.hr_officer).initialize_field_value(
            employee.id, "hr.employee", "hr_document_folder"
        )
        self.assertTrue(employee.shared_folder_ids.folder)

    def test_hr_officer_of_other_company(self):
        company = self.env["res.company"].create({"name": "Other Company"})
        officer = new_test_user(
            self.env,
            login="test_hefs_hr_other",
            groups="base.group_user,hr.group_hr_user",
            company_id=company.id,
            company_ids=[(6, 0, company.ids)],
        )
        with self.assertRaises(AccessError):
            self._names(
                officer, "hr.employee.shared.folder", self.shared_1.id, "folder"
            )
