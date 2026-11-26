# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import posixpath
from functools import partial

from odoo import _, api, models, registry
from odoo.exceptions import UserError

from odoo.addons.fs_folder import fields as fs_fields

_logger = logging.getLogger(__name__)

UNASSIGNED_FOLDER = "_Unassigned"

# fields used in the name of the folder (firstname/lastname: partner_firstname)
FOLDER_NAME_FIELDS = {"name", "ref", "firstname", "lastname"}


class ResPartner(models.Model):
    _inherit = "res.partner"

    document_folder = fs_fields.FsFolder(
        string="Documents Folder",
        create_parent_get="_get_document_folder_parent",
        create_name_get="_get_document_folder_name",
    )

    # ------------------------------------------------------------------
    # Folder location:
    #   <salesperson>/<ref> - <name>                  (partner without parent)
    #   <parent folder>/<ref> - <name>                (contact, subsidiary...)
    # (fs_folder calls the hooks with (field, fs), see fs_folder/fields.py)
    # ------------------------------------------------------------------
    def _get_document_folder_holder(self):
        """Return the partner whose folder holds the folder of this partner.

        That is the parent partner: the company of a contact, the parent company
        of a subsidiary. Nothing for a partner without parent, whose folder is
        filed under its salesperson.
        """
        self.ensure_one()
        return self.parent_id

    def _get_document_folder_salesperson_dirname(self):
        self.ensure_one()
        return self.user_id.name or UNASSIGNED_FOLDER

    def _get_document_folder_parent_parts(self):
        """Return the path parts of the folder holding the documents folder.

        The folder of the parent partner is created if it is missing.
        """
        self.ensure_one()
        holder = self._get_document_folder_holder()
        if holder:
            if not holder.document_folder:
                holder.document_folder.initialize()
            return holder.document_folder.ref.split("/")
        return [self._get_document_folder_salesperson_dirname()]

    def _get_document_folder_parent(self, field, fs):
        return {
            partner.id: partner._get_document_folder_parent_parts() for partner in self
        }

    def _get_document_folder_dirname(self):
        self.ensure_one()
        return f"{self.ref or self.id} - {self.name or self.display_name}"

    def _get_document_folder_name(self, field, fs):
        return {partner.id: partner._get_document_folder_dirname() for partner in self}

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_create_document_folder(self):
        """Create the documents folder (the "Create Folder" button of the widget)."""
        # fs_folder reads fs.storage without sudo when it creates the folder
        # (create_value_in_fs -> fs.storage.get_by_code), which users that are
        # not system administrators cannot read (and must not: it holds the
        # storage credentials). Check the access on the partner, then sudo.
        self.check_access("write")
        for partner in self.sudo().filtered(lambda p: not p.document_folder):
            partner.document_folder.initialize()
        return True

    # ------------------------------------------------------------------
    # Keep the folder at its place and name when the salesperson, the parent
    # or the name of the partner changes. The folders inside it follow it.
    # ------------------------------------------------------------------
    def write(self, vals):
        res = super().write(vals)
        if "parent_id" in vals or FOLDER_NAME_FIELDS & vals.keys():
            partners = self.sudo()
        elif "user_id" in vals:
            # the salesperson is used only for the partners without parent
            partners = self.sudo().filtered(
                lambda p: not p._get_document_folder_holder()
            )
        else:
            return res
        for partner in partners.filtered("document_folder"):
            partner.with_delay(
                description=_("Move documents folder of %s", partner.display_name),
                identity_key=f"partner_fs_folder_move_{partner.id}",
            )._move_document_folder()
        return res

    def _move_document_folder(self):
        """Move (or rename) the documents folder to where it belongs now.

        Idempotent: the target is computed from the current salesperson, parent
        and name, so the job can be retried or run after several changes.
        The folders of the contacts inside the moved folder follow it: their
        links are updated.
        """
        adapter = self.env["fs.folder.field.value.adapter"]
        for partner in self.sudo().filtered("document_folder"):
            value = partner.document_folder
            storage_code = value.storage_code
            storage = self.env["fs.storage"].get_by_code(storage_code)
            fs = self.env["fs.storage"].get_fs_by_code(storage_code)
            old_path = value.ref
            parent_parts = partner._get_document_folder_parent_parts()
            name = partner._get_document_folder_dirname()
            if storage.sanitize_fs_name:
                parent_parts = storage.sanitize_fs_item_names(parent_parts)
                name = storage.sanitize_fs_item_name(name)
            parent = posixpath.join(*parent_parts)
            new_path = posixpath.join(parent, name)
            if new_path == old_path:
                continue
            if not fs.exists(old_path):
                _logger.warning(
                    "Documents folder %s of partner %s not found on storage %s: "
                    "not moved (was it moved or deleted on the storage?)",
                    old_path,
                    partner.id,
                    storage_code,
                )
                continue
            if fs.exists(new_path):
                raise UserError(
                    _(
                        "Cannot move the documents folder of %(partner)s to "
                        "%(path)s: a folder with this name already exists.",
                        partner=partner.display_name,
                        path=new_path,
                    )
                )
            fs.makedirs(parent, exist_ok=True)
            # recursive=True is required: webdav4 only creates the target
            # directory when moving a directory non-recursively
            fs.mv(old_path, new_path, recursive=True)
            self.env.cr.postrollback.add(
                partial(
                    self._move_document_folder_back,
                    storage_code,
                    new_path,
                    old_path,
                )
            )
            partner.document_folder = adapter._created_folder_name_to_stored_value(
                new_path, storage_code, fs
            )
            partner._update_document_subfolder_links(
                old_path, new_path, storage_code, fs
            )
        return True

    def _update_document_subfolder_links(self, old_path, new_path, storage_code, fs):
        """Update the links of all the folders moved with this folder.

        They are found by path, not by parent: a contact may have left the
        company before the job moving the company folder ran, its folder was
        moved all the same.
        """
        self.ensure_one()
        adapter = self.env["fs.folder.field.value.adapter"]
        prefix = adapter._created_folder_name_to_stored_value(
            f"{old_path}/", storage_code, fs
        )
        self.flush_model(["document_folder"])
        # left() rather than LIKE: "_" (as in _Unassigned) is a LIKE wildcard
        self.env.cr.execute(
            "SELECT id FROM res_partner "
            "WHERE left(document_folder, length(%s)) = %s AND id != %s",
            (prefix, prefix, self.id),
        )
        partners = (
            self.sudo()
            .with_context(active_test=False)
            .browse([row[0] for row in self.env.cr.fetchall()])
        )
        for partner in partners:
            ref = partner.document_folder.ref
            partner.document_folder = adapter._created_folder_name_to_stored_value(
                new_path + ref[len(old_path) :], storage_code, fs
            )

    @api.model
    def _move_document_folder_back(self, storage_code, path, original_path):
        """Undo a folder move when the transaction that recorded it is rolled back.

        Runs after the rollback, in a new cursor (like fs_folder's own clean up).
        """
        dbname = self.env.cr.dbname
        try:
            with registry(dbname).cursor() as cr:
                env = api.Environment(cr, self.env.uid, {})
                fs = env["fs.storage"].sudo().get_fs_by_code(storage_code)
                fs.mv(path, original_path, recursive=True)
        except Exception:
            _logger.exception(
                "Could not move documents folder %s back to %s after rollback",
                path,
                original_path,
            )
