# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import os
import shutil
import tempfile

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase

from ..models.res_partner import UNASSIGNED_FOLDER


class TestPartnerFsFolder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.root = tempfile.mkdtemp()
        cls.addClassCleanup(shutil.rmtree, cls.root)
        field = cls.env["ir.model.fields"]._get("res.partner", "document_folder")
        # a field can be linked to one storage only: detach the configured one
        configured = (
            cls.env["fs.storage"].search([]).filtered(lambda s: field in s.field_ids)
        )
        configured.write({"field_ids": [(3, field.id)]})
        cls.storage = cls.env["fs.storage"].create(
            {
                "name": "Partner documents (test)",
                "code": "partner_fs_folder_test",
                "protocol": "file",
                "directory_path": cls.root,
                "check_connection_method": "ls",
                "field_ids": [(6, 0, field.ids)],
            }
        )
        cls.sales_1 = new_test_user(
            cls.env, login="test_pfsf_sales_1", name="Anna Sales"
        )
        cls.sales_2 = new_test_user(
            cls.env, login="test_pfsf_sales_2", name="Bob Sales"
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Major Donor", "ref": "1234", "user_id": cls.sales_1.id}
        )
        cls.company = cls.env["res.partner"].create(
            {
                "name": "Acme SA",
                "ref": "5001",
                "is_company": True,
                "user_id": cls.sales_1.id,
            }
        )
        cls.contact = cls.env["res.partner"].create(
            {
                "name": "Jean Dupont",
                "ref": "5002",
                "parent_id": cls.company.id,
                # the salesperson of a contact of a company is not used
                "user_id": cls.sales_2.id,
            }
        )

    def setUp(self):
        super().setUp()
        # the database is rolled back after each test, the file system is not
        for entry in os.listdir(self.root):
            path = os.path.join(self.root, entry)
            if os.path.isdir(path):
                shutil.rmtree(path)

    def _abs(self, *parts):
        return os.path.join(self.root, *parts)

    def test_folder_created_under_salesperson(self):
        self.assertFalse(self.partner.document_folder)
        self.partner.action_create_document_folder()
        self.assertEqual(
            self.partner.document_folder.ref, "Anna Sales/1234 - Major Donor"
        )
        self.assertTrue(os.path.isdir(self._abs("Anna Sales", "1234 - Major Donor")))

    def test_folder_created_unassigned(self):
        partner = self.env["res.partner"].create({"name": "Nobody's Donor"})
        partner.action_create_document_folder()
        expected = f"{UNASSIGNED_FOLDER}/{partner.id} - Nobody's Donor"
        self.assertEqual(partner.document_folder.ref, expected)
        self.assertTrue(os.path.isdir(self._abs(*expected.split("/"))))

    def test_create_folder_is_idempotent(self):
        self.partner.action_create_document_folder()
        ref = self.partner.document_folder.ref
        self.partner.action_create_document_folder()
        self.assertEqual(self.partner.document_folder.ref, ref)

    def test_salesperson_change_moves_folder_with_content(self):
        self.partner.action_create_document_folder()
        self.partner.document_folder.fs.pipe_file("note.txt", b"hello")
        self.partner.user_id = self.sales_2
        self.assertEqual(
            self.partner.document_folder.ref, "Bob Sales/1234 - Major Donor"
        )
        self.assertFalse(os.path.exists(self._abs("Anna Sales", "1234 - Major Donor")))
        with open(self._abs("Bob Sales", "1234 - Major Donor", "note.txt"), "rb") as f:
            self.assertEqual(f.read(), b"hello")
        # through the field value, as the widget does
        self.assertEqual(self.partner.document_folder.fs.cat_file("note.txt"), b"hello")

    def test_salesperson_removed_moves_to_unassigned(self):
        self.partner.action_create_document_folder()
        self.partner.user_id = False
        self.assertEqual(
            self.partner.document_folder.ref, f"{UNASSIGNED_FOLDER}/1234 - Major Donor"
        )

    def test_partner_without_folder_not_affected(self):
        self.partner.user_id = self.sales_2
        self.assertFalse(self.partner.document_folder)
        self.assertFalse(os.path.exists(self._abs("Bob Sales")))

    def test_missing_folder_does_not_block_reassignment(self):
        self.partner.action_create_document_folder()
        ref = self.partner.document_folder.ref
        shutil.rmtree(self._abs("Anna Sales", "1234 - Major Donor"))
        self.partner.user_id = self.sales_2
        self.assertEqual(self.partner.user_id, self.sales_2)
        self.assertEqual(self.partner.document_folder.ref, ref)

    def test_existing_target_folder_raises(self):
        self.partner.action_create_document_folder()
        os.makedirs(self._abs("Bob Sales", "1234 - Major Donor"))
        with self.assertRaises(UserError):
            self.partner.user_id = self.sales_2

    def test_job_when_delayed(self):
        """Without the no-delay context, reassignment enqueues one move job."""
        self.partner.action_create_document_folder()
        partner = self.partner.with_context(queue_job__no_delay=False)
        jobs_before = self.env["queue.job"].search_count([])
        partner.user_id = self.sales_2
        partner.user_id = self.sales_1  # same identity key: no second job
        job = self.env["queue.job"].search([], order="id desc", limit=1)
        self.assertEqual(self.env["queue.job"].search_count([]), jobs_before + 1)
        self.assertEqual(job.method_name, "_move_document_folder")
        # folder not moved yet: still valid at its old place
        self.assertEqual(
            self.partner.document_folder.ref, "Anna Sales/1234 - Major Donor"
        )

    def test_non_admin_user_with_write_access_can_create(self):
        """A user who cannot read fs.storage can create a folder.

        NB: fs_folder reads fs.storage with the user's rights on folder creation
        (see action_create_document_folder). That bug only shows over HTTP, from
        the second request on; it could not be reproduced in a TransactionCase,
        so this test checks the behaviour, it does not catch that regression.
        """
        user = new_test_user(
            self.env,
            login="test_pfsf_fundraiser",
            groups="base.group_user,base.group_partner_manager",
        )
        self.assertFalse(self.env["fs.storage"].with_user(user).has_access("read"))
        self.partner.with_user(user).action_create_document_folder()
        self.assertEqual(
            self.partner.document_folder.ref, "Anna Sales/1234 - Major Donor"
        )

    def test_user_without_write_access_cannot_create(self):
        user = new_test_user(
            self.env, login="test_pfsf_reader", groups="base.group_user"
        )
        self.assertFalse(self.partner.with_user(user).has_access("write"))
        with self.assertRaises(AccessError):
            self.partner.with_user(user).action_create_document_folder()
        self.assertFalse(self.partner.document_folder)

    # ------------------------------------------------------------------
    # Contacts of a company
    # ------------------------------------------------------------------
    def test_contact_folder_created_in_company_folder(self):
        """The company folder is created on the fly, under its salesperson."""
        self.contact.action_create_document_folder()
        self.assertEqual(self.company.document_folder.ref, "Anna Sales/5001 - Acme SA")
        self.assertEqual(
            self.contact.document_folder.ref,
            "Anna Sales/5001 - Acme SA/5002 - Jean Dupont",
        )
        self.assertTrue(
            os.path.isdir(
                self._abs("Anna Sales", "5001 - Acme SA", "5002 - Jean Dupont")
            )
        )

    def test_contact_folder_in_existing_company_folder(self):
        self.company.action_create_document_folder()
        company_ref = self.company.document_folder.ref
        self.contact.action_create_document_folder()
        self.assertEqual(self.company.document_folder.ref, company_ref)
        self.assertEqual(
            self.contact.document_folder.ref, f"{company_ref}/5002 - Jean Dupont"
        )

    def test_contact_salesperson_change_does_not_move(self):
        self.contact.action_create_document_folder()
        ref = self.contact.document_folder.ref
        self.contact.user_id = self.sales_1
        self.contact.user_id = False
        self.assertEqual(self.contact.document_folder.ref, ref)
        self.assertTrue(os.path.isdir(self._abs(*ref.split("/"))))

    def test_company_salesperson_change_moves_contact_folders(self):
        self.contact.action_create_document_folder()
        self.contact.document_folder.fs.pipe_file("cv.txt", b"contact")
        self.company.user_id = self.sales_2
        self.assertEqual(self.company.document_folder.ref, "Bob Sales/5001 - Acme SA")
        self.assertEqual(
            self.contact.document_folder.ref,
            "Bob Sales/5001 - Acme SA/5002 - Jean Dupont",
        )
        self.assertFalse(os.path.exists(self._abs("Anna Sales", "5001 - Acme SA")))
        self.assertEqual(self.contact.document_folder.fs.cat_file("cv.txt"), b"contact")

    def test_contact_linked_to_company_moves_into_company_folder(self):
        self.partner.action_create_document_folder()
        self.partner.document_folder.fs.pipe_file("note.txt", b"hello")
        self.partner.parent_id = self.company
        self.assertEqual(
            self.partner.document_folder.ref,
            "Anna Sales/5001 - Acme SA/1234 - Major Donor",
        )
        self.assertFalse(os.path.exists(self._abs("Anna Sales", "1234 - Major Donor")))
        self.assertEqual(self.partner.document_folder.fs.cat_file("note.txt"), b"hello")

    def test_contact_detached_moves_under_own_salesperson(self):
        self.contact.action_create_document_folder()
        self.contact.parent_id = False
        self.assertEqual(
            self.contact.document_folder.ref, "Bob Sales/5002 - Jean Dupont"
        )
        self.assertFalse(
            os.path.exists(
                self._abs("Anna Sales", "5001 - Acme SA", "5002 - Jean Dupont")
            )
        )

    def test_contact_changes_company(self):
        other = self.env["res.partner"].create(
            {"name": "Beta AG", "ref": "6001", "is_company": True}
        )
        self.contact.action_create_document_folder()
        self.contact.parent_id = other
        self.assertEqual(
            other.document_folder.ref, f"{UNASSIGNED_FOLDER}/6001 - Beta AG"
        )
        self.assertEqual(
            self.contact.document_folder.ref,
            f"{UNASSIGNED_FOLDER}/6001 - Beta AG/5002 - Jean Dupont",
        )

    def test_contact_left_company_before_company_move(self):
        """A contact detached while the company move is pending keeps its folder.

        The company job moves the folder of the former contact with the company
        folder: its link must follow, so that its own job can then move it.
        """
        self.contact.action_create_document_folder()
        self.contact.document_folder.fs.pipe_file("cv.txt", b"contact")
        delayed = dict(queue_job__no_delay=False)
        self.company.with_context(**delayed).user_id = self.sales_2
        self.contact.with_context(**delayed).parent_id = False
        # the jobs run in this order
        self.company._move_document_folder()
        self.assertEqual(
            self.contact.document_folder.ref,
            "Bob Sales/5001 - Acme SA/5002 - Jean Dupont",
        )
        self.contact._move_document_folder()
        self.assertEqual(
            self.contact.document_folder.ref, "Bob Sales/5002 - Jean Dupont"
        )
        self.assertEqual(self.contact.document_folder.fs.cat_file("cv.txt"), b"contact")
