## Tracking mailings sent outside of Odoo

Communications carry three UTM fields (Source, Medium, Campaign) so that mailings sent
outside of Odoo — through a printing house, for instance — can be analysed together with
the digital ones.

Each communication type carries its own **Campaign Tracking** defaults, in the *General
configuration* of its form. A communication starts with the values of its type, and they
can then be changed on the communication itself.

A communication **created directly in the Done state** records a mailing that was already
dispatched: Odoo generates nothing and sends nothing for it, and it is not merged into a
pending communication. Its sending date is filled in automatically when it is not given.
Such a communication keeps no content, since what was printed did not come from Odoo.

### Importing a recipient list

To record a mailing that has already been dispatched, import the recipient list sent to the
printer from *Contacts → Partner Communication → Communication Jobs*, with the standard
**Import records** button. Useful columns:

| Column            | Content                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `partner_id`      | Partner reference (the `ref` field), or the partner name           |
| `config_id`       | Name of the communication type                                     |
| `state`           | `Done` for a mailing that was already dispatched                   |
| `send_mode`       | `Print report` for a letter (or the technical value `physical`)    |
| `subject`         | Optional — a readable label, otherwise the lines show no subject   |
| `utm_source_id`   | Optional — defaults to the source of the communication type        |
| `utm_medium_id`   | Optional — defaults to the medium of the communication type        |
| `utm_campaign_id` | Optional — defaults to the campaign of the communication type      |
| `sent_date`       | Optional — dispatch date, defaults to the date of the import       |

An **empty cell is not the same as a missing column**: it sets the field to empty instead
of falling back on the default of the communication type. To rely on the defaults, leave
the column out of the file entirely.

Prefer the partner **reference** over the name: a name is matched through `name_search`,
which silently picks the first record when several partners share it. UTM records given by
name must exist beforehand, and their names must be unique for the same reason.

Without the `state` column, the lines are imported as regular pending communications, ready
to be sent by Odoo. As a safety net, an import never sends anything on its own, whatever
the state — importing a recipient list is meant to record mailings, and a communication type
set to send automatically would otherwise dispatch the whole file.

Once imported, the communication list groups by Campaign, Medium and Source.
