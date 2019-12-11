Module to track the sponsorship departures and SUB sponsorships.
It is based on a new state : sds_state.
It adds a new kanban, tree and form view to track sponsorships after child departure.

Color conventions for SDS Tracking Kanban View :

0 - Blank - Default color
1 - Black - Sponsorships with NO SUB (cancelled, or no_sub)
2 - Red - Sub_rejected sponsorships or sponsorships that are likely to become sub_reject.
3 - Yellow - Indicates a higher priority action is required on this sponsorship.
4 - Light green - Indicates an action is required on this sponsorship, typically a mailing is to be sent to the sponsor. This is a low priority action.
5 - Green - Sub_accepted sponsorships or sponsorships likely to become sub_accept.
6 - Light blue - not used
7 - Blue - Draft sponsorships
8 - Violet - not used
9 - Pink - not used
