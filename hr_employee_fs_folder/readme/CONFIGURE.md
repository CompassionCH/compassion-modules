1. Create a storage in *Settings > Technical > FS Storage* (for instance
   protocol `webdav` pointing to an `rclone serve webdav` of an HR Shared
   Drive, separate from other storages). Set *Check connection method* to
   *List File*.
2. In the storage, add both fields to the *Fields* linked to it:
   *HR Documents* (`hr.employee`) and *My Documents*
   (`hr.employee.shared.folder`). Leave *Models* empty.
3. Run the action *Create Documents Folders* on the existing employees.

On Google Drive, only HR is member of the Shared Drive (as *Contributor*): the
employees access their documents through Odoo only. Do not move or rename the
folders on the Drive: the link between an employee and their folder is the
folder path.
