This module helps Compassion CH to manage its planned events, by creating a
new model for tracking upcoming events.

 * Opportunities can generate new events
 * Each event is linked to an analytic account
 * Each event creates a sponsorship origin
 * Portal users have an analytic account to track sponsorships gained by them
 * Can set ambassadors to sponsorships in order to track who brought them

 Warning: This module deactivates e-mail notification for calendar events !
    If you want to enable it again, please remove the config_parameter
    'calendar.block_mail'.

Interaction Resume
------------------
New partner view to collect all history of communications with a partner and display them all at the same place.

Demand Planning
---------------
This module contains also the Demand Planning for the GMC Global Childpool.
It is useful to predict the number of children that will be needed and also
to review the past to watch the results and analyze the predictions that were
made.

Here is how the computations are done :

Demand
^^^^^^
 * Children for the website : each week a fixed number of children are
   requested for the website. This number is taken from the Settings
   (Settings -> Demand Planning)
 * Children for ambassadors : each week a fixed number of children are
   requested for ambassadors. This number is taken from the Settings
 * Children for SUB Sponsorships : This is a computed number based on
   statistics since one year. It takes the average number of registered
   SUB sponsorships per week and puts that number in all weeks of previsions
 * Children for the Events : This number is directly extracted from the
   planned events, with the "number_allocate_children" number and
   "hold_start_date" set on each event. The number of requested children is
   split evenly between the weeks separating the "hold_start_date" and the
   "event_start_date".

Resupply
^^^^^^^^
 * Web resupply : Substracts the average of registered sponsorships from the
   web since one year from the number requested (taken from the Settings)
 * Ambassador resupply : Computed like the web, but with the ambassador numbers
 * SUB Sponsorship resupply : Rejected SUB Sponsorships are those that were
   ended in 90 days following the sponsorship creation. Resupply is the
   average of sub rejections we had in the previous year.
 * Events Resupply : The number is extracted from the events and is equal
   to the "number_allocate_children" - "planned_sponsorships"
 * Sponsorships Cancellations : Cancellations are as well children that will
   be released to the Global Childpool. This number is also the average of
   cancellations from last year.

Weekly Revisions
^^^^^^^^^^^^^^^^
Revisions numbers are computed based on the actual holds that were created
in the revision period, as well as the sponsorships made.
