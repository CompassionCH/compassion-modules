1. Create a storage in *Settings > Technical > FS Storage* (for instance
   protocol `webdav` pointing to an `rclone serve webdav` of a Shared Drive).
   Set *Check connection method* to *List File*: the default *Create Marker
   file* rewrites a file on every use, which is slow on Google Drive.
2. In the storage, add the field *Documents Folder* (`res.partner`) to the
   *Fields* linked to this storage (or mark the storage as default for
   filesystem contents).

Do not move or rename the folders directly on the storage: the link between a
partner and its folder is the folder path. Give users a role on the storage
that does not allow moving folders (e.g. *Contributor* on a Shared Drive).

**Google Drive through rclone with a service account**

1. In Google Cloud, create a service account (no domain-wide delegation) and a
   JSON key. A service account has no storage of its own: use a Shared Drive.
2. Add the service account e-mail to the Shared Drive as *Content manager*.
   Give the users *Contributor*, so that they cannot move or delete folders.
3. Create the rclone remote:
   `rclone config create gdrive_partners drive scope=drive service_account_file=/path/key.json team_drive=<shared drive id>`
4. Serve it over WebDAV, on localhost only, as a service:
   `rclone serve webdav gdrive_partners: --addr 127.0.0.1:8081 --user odoo --pass <secret> --dir-cache-time 30s --poll-interval 30s --vfs-cache-mode off`
5. Create the storage with protocol `webdav` and options
   `{"base_url": "http://127.0.0.1:8081", "auth": ["odoo", "<secret>"], "timeout": 60}`.

Files added on the Drive side show in Odoo after the rclone cache delay
(`--dir-cache-time`, about 30 s).
