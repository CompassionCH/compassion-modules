Adds a **Documents** tab on partners showing a folder of an external file
system (configured with `fs_storage`, e.g. a Google Drive Shared Drive served
over WebDAV), where users can drop any kind of content.

- The folder is created on demand only (button *Create Folder* of the tab), not
  for every partner.
- Folders of the partners without parent are filed by salesperson:
  `<salesperson>/<reference> - <name>` (`_Unassigned` when the partner has no
  salesperson).
- Folders of the partners with a parent (contacts of a company, subsidiaries)
  are subfolders of the parent folder:
  `<salesperson>/<company reference> - <company>/<reference> - <name>`. The
  parent folder is created when needed, and the salesperson of a partner with
  a parent is not used.
- When the salesperson, the parent, the name or the reference of a partner
  changes, a queue job moves or renames its folder and updates the links (also
  the ones of the folders inside it).
- Access to the folder follows the access to the partner: reading the folder
  requires read access on the partner, changing its content requires write
  access.
