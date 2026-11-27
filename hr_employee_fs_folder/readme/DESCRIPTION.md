Gives each employee a documents folder on an external file system
(configured with `fs_storage`, e.g. a Google Drive Shared Drive served over
WebDAV), with a subfolder shared read-only with the employee:

```
<id> - <name>/          HR only (contract, evaluations...)
  Shared/               HR and the employee (salary certificate, payslips...)
```

- HR officers see the whole folder in the **HR Documents** tab of the employee.
- Each employee sees only their own **Shared** folder, in *Employees > My
  Documents*, read only (download and preview).
- The folders are created by a queue job when an employee is created, or with
  the action *Create Documents Folders* on existing employees. The folder is
  renamed when the employee is renamed.

The employees cannot read `hr.employee` (HR only), and every employee can read
every public profile (`hr.employee.public`) and every user (`res.users`): the
shared folder is therefore on its own model, `hr.employee.shared.folder`, with
a record rule restricting each employee to their own folder (and HR officers to
their companies).
