from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TranslationBadge(models.Model):
    _name = "translation.badge"
    _description = "Translation Badge"

    name = fields.Char(string="Badge Name", required=True, translate=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(
        default=True,
        help="Archive a badge to stop awarding it while keeping existing awards.",
    )

    icon = fields.Image(max_width=128, max_height=128)

    badge_type = fields.Selection(
        [
            ("count", "Volume (Total Letters)"),
            ("streak", "Engagement (Consecutive Days)"),
            ("campaign", "Time-bound Campaign"),
        ],
        string="Type",
        required=True,
    )

    threshold = fields.Integer(
        string="Target",
        default=1,
        required=True,
    )

    start_date = fields.Date(string="Campaign Start Date")
    end_date = fields.Date(string="Campaign End Date")

    user_badge_ids = fields.One2many(
        "translation.user.badge", "badge_id", string="Granted to", readonly=True
    )

    _sql_constraints = [
        (
            "threshold_positive",
            "CHECK(threshold > 0)",
            "The target must be bigger than 0.",
        )
    ]

    @api.constrains("badge_type", "start_date", "end_date")
    def _check_campaign_dates(self):
        for badge in self.filtered(lambda b: b.badge_type == "campaign"):
            if not badge.start_date or not badge.end_date:
                raise ValidationError(
                    _("A campaign badge requires a start date and an end date.")
                )
            if badge.end_date < badge.start_date:
                raise ValidationError(
                    _("The campaign end date must be on or after its start date.")
                )


class TranslationUserBadge(models.Model):
    _name = "translation.user.badge"
    _description = "User Unlocked Badges"

    translator_id = fields.Many2one(
        "translation.user",
        required=True,
        index=True,
        ondelete="cascade",
    )

    badge_id = fields.Many2one(
        "translation.badge",
        required=True,
        ondelete="cascade",
    )

    unlocked_date = fields.Datetime(
        string="Unlocked On",
        default=fields.Datetime.now,
    )

    _sql_constraints = [
        (
            "unique_user_badge",
            "UNIQUE(translator_id, badge_id)",
            "A user can only unlock a specific badge once.",
        )
    ]
