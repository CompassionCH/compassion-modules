<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->

[![Pre-commit Status](https://github.com/CompassionCH/compassion-modules/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/CompassionCH/compassion-modules/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=CompassionCH_compassion-modules&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=CompassionCH_compassion-modules)

<!-- /!\ Non OCA Context : Set here the badge of your translation instance. -->

<!-- /!\ do not modify above this line -->

# Compassion Modules

This project holds Odoo modules needed for any Compassion office in order to manage
sponsorships of its country. It connects Odoo with GMC webservices.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[advanced_translation](advanced_translation/) | 18.0.1.0.0 |  | Advanced Translation
[child_compassion](child_compassion/) | 18.0.1.0.2 |  | Compassion Children
[child_protection](child_protection/) | 18.0.1.0.0 |  | Add fields for tracking acceptance of child protection charter
[crm_compassion](crm_compassion/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> | Compassion Events and Opportunities
[crm_request](crm_request/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> | Enables Customer Support Inbox
[gift_compassion](gift_compassion/) | 18.0.1.0.0 |  | Compassion Sponsorship Gifts
[interaction_resume](interaction_resume/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> | Display a timeline of all communications exchanged with a partner
[intervention_compassion](intervention_compassion/) | 18.0.1.0.0 |  | Compassion Interventions
[message_center_compassion](message_center_compassion/) | 18.0.1.0.1 |  | Compassion Connect
[mis_builder_analytic](mis_builder_analytic/) | 18.0.1.0.0 |  | Dummy module kept for migration purposes.
[mis_builder_spn_info](mis_builder_spn_info/) | 18.0.1.0.0 |  | Dummy module kept for migration purposes.
[onramp_simulator](onramp_simulator/) | 18.0.1.0.0 |  | Send messages to Compassion Onramps
[partner_auto_match](partner_auto_match/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> | Find existing contact given any partner data.
[partner_communication](partner_communication/) | 18.0.1.0.1 |  | Partner Communication
[partner_communication_compassion](partner_communication_compassion/) | 18.0.1.0.0 |  | Compassion Partner Communications
[partner_communication_crm_phone](partner_communication_crm_phone/) | 18.0.1.0.0 |  | Partner Communication CRM Phone
[partner_communication_omr](partner_communication_omr/) | 18.0.1.0.0 |  | Partner Communication OMR
[partner_communication_reminder](partner_communication_reminder/) | 18.0.1.0.0 |  | Reminder features
[partner_communication_revision](partner_communication_revision/) | 18.0.1.0.0 |  | Partner Communication Revisions
[partner_personal_info](partner_personal_info/) | 18.0.1.0.0 |  | Adds a tab on partners for showing personal information
[partner_salutation](partner_salutation/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> | Adds a salutation field on partners
[partner_search_fuzzy](partner_search_fuzzy/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> | Add fuzzy search on partners
[partner_segmentation](partner_segmentation/) | 18.0.1.0.0 |  | Segment Sponsors
[sbc_compassion](sbc_compassion/) | 18.0.1.0.0 |  | SBC - Supporter to Participant Communication
[sponsorship_compassion](sponsorship_compassion/) | 18.0.1.0.1 |  | Compassion Sponsorships
[sponsorship_reporting](sponsorship_reporting/) | 18.0.1.0.0 |  | Add the reports for the sponsorships
[sponsorship_sub_management](sponsorship_sub_management/) | 18.0.1.0.0 | <a href='https://github.com/ecino'><img src='https://github.com/ecino.png' width='32' height='32' style='border-radius:50%;' alt='ecino'/></a> <a href='https://github.com/NoeBerdoz'><img src='https://github.com/NoeBerdoz.png' width='32' height='32' style='border-radius:50%;' alt='NoeBerdoz'/></a> | Compassion SUB Sponsorships Management
[survival_sponsorship_compassion](survival_sponsorship_compassion/) | 18.0.1.0.0 |  | New type for the sponsorships that add the possibility to sponsor a country in the survival program (CSP).
[thankyou_letters](thankyou_letters/) | 18.0.1.0.0 |  | Thank You Letters
[wordpress_configuration](wordpress_configuration/) | 18.0.1.0.0 |  | Wordpress configuration for multi-company

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to
Compassion Switzerland policy. Consult each module's `__manifest__.py` file, which
contains a `license` key that explains its license.

---

<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
