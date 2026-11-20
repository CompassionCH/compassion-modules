Adds a **Documents** tab on partners showing a folder of an external file
system (configured with `fs_storage`, e.g. a Google Drive Shared Drive served
over WebDAV), where users can drop any kind of content.

- The folder is created on demand only (button *Create Documents Folder*), not
  for every partner.
- Folders of companies and individuals are filed by salesperson:
  `<salesperson>/<reference> - <name>` (`_Unassigned` when the partner has no
  salesperson).
- Folders of the contacts of a company are subfolders of the company folder:
  `<salesperson>/<company reference> - <company>/<reference> - <name>`. The
  company folder is created when needed, and the salesperson of the contact
  is not used.
- When the salesperson or the company of a partner changes, a queue job moves
  the folder to its new place and updates the links (also the ones of the
  contact folders inside a moved company folder).
- Access to the folder follows the access to the partner: reading the folder
  requires read access on the partner, changing its content requires write
  access.
