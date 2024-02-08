## Access rights

- Assign the rights to the users so that they can access the new
  "Sponsorship" menu

## Configuration menu

- Find the configuration menu in Sponsorship/Configuration (must be
  given rights)
- Configure the default hold durations in the menu Global
  Childpool/Availability Management
- Assign people to be notified when receiving National Office Disaster
  Alerts using the menu Communication/Staff Notifications

## Odoo.conf file

To get weather information about each project location, you'll need to
add an API key from opernweathermap.org to the odoo.conf file.

openweathermap_api_key = AAAAAAAAAAA

## Demand planning

You can add in the system settings default values for weekly demand and
resupply quantities by setting the following keys:

- child_compassion.default_demand
- child_compassion.default_resupply
