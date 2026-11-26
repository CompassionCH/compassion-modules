from datetime import datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

LEADERBOARD_TZ = pytz.timezone("Europe/Zurich")
CLOSING_DELAY = timedelta(hours=48)
TOP_SIZE = 10
WINDOW_SIZE = 2

# Fields only the system can write (lifecycle).
SYSTEM_FIELDS = {"state"}
# The period of a leaderboard is never set by hand: it follows the campaign
# dates (campaign) or is given by the system (weekly / monthly).
PERIOD_FIELDS = {"start_at", "end_at"}


def _is_system(env):
    """True for lifecycle writes made by the system itself.

    The ``leaderboard_system`` context key alone is not enough: an RPC
    caller can set any context key. System writes also run in superuser
    mode (``sudo()``), which an RPC call can never reach.
    """
    return env.su and bool(env.context.get("leaderboard_system"))


def _local_to_utc(local_dt):
    """Convert a naive Europe/Zurich datetime into a naive UTC datetime."""
    return LEADERBOARD_TZ.localize(local_dt).astimezone(pytz.utc).replace(tzinfo=None)


def _period_bounds(period_type, ref_date):
    """Return (start_at, end_at) in naive UTC for the period containing ref_date.

    Boundaries are computed in Europe/Zurich: start at 00:00:00, end at
    23:59:59 of the last day (inclusive, like the spec's BETWEEN).
    """
    if period_type == "weekly":
        first_day = ref_date - timedelta(days=ref_date.weekday())
        last_day = first_day + timedelta(days=6)
    elif period_type == "monthly":
        first_day = ref_date.replace(day=1)
        last_day = first_day + relativedelta(months=1, days=-1)
    else:
        raise ValueError(period_type)
    return (
        _local_to_utc(datetime.combine(first_day, time.min)),
        _local_to_utc(datetime.combine(last_day, time(23, 59, 59))),
    )


class TranslationLeaderboard(models.Model):
    _name = "translation.leaderboard"
    _description = "Translation Leaderboard"
    _order = "start_at desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    name_key = fields.Char(
        compute="_compute_name_key",
        store=True,
        # Computed before the INSERT: the column is NOT NULL and the form
        # does not send this field. Not readonly at the ORM level so that the
        # key given by the system for weekly / monthly leaderboards is kept
        # (it is readonly in the form view).
        precompute=True,
        required=True,
        readonly=False,
        copy=False,
        help="Technical key used by the platform to translate the period name.",
    )
    leaderboard_type = fields.Selection(
        [
            ("campaign", "Campaign"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        string="Type",
        required=True,
        default="campaign",
        index=True,
    )
    campaign_id = fields.Many2one(
        "translation.badge",
        string="Campaign",
        # The period is taken from the campaign: it needs both dates
        domain=[
            ("badge_type", "=", "campaign"),
            ("start_date", "!=", False),
            ("end_date", "!=", False),
        ],
        ondelete="restrict",
        index=True,
    )
    start_at = fields.Datetime(
        compute="_compute_period",
        store=True,
        precompute=True,
        readonly=False,
        required=True,
        index=True,
    )
    end_at = fields.Datetime(
        compute="_compute_period",
        store=True,
        precompute=True,
        readonly=False,
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("live", "Live"),
            ("closing", "Results being finalized"),
            ("final", "Final"),
        ],
        default="scheduled",
        required=True,
        readonly=True,
        index=True,
        copy=False,
    )
    created_by = fields.Many2one(
        "res.users",
        readonly=True,
        copy=False,
        help="Administrator who created the leaderboard. Empty for leaderboards "
        "generated automatically by the system.",
    )
    show_inactive_users = fields.Boolean(
        help="List translators with 0 points after the ranked ones, "
        "without rank number ('Not ranked yet')."
    )

    # Final snapshot
    entry_ids = fields.One2many(
        "translation.leaderboard.entry",
        "leaderboard_id",
        "Final ranking",
        groups="sbc_translation.group_manager",
    )
    participant_count = fields.Integer(compute="_compute_participant_count")

    _sql_constraints = [
        (
            "unique_name_key",
            "UNIQUE(name_key)",
            "A leaderboard already exists for this period.",
        ),
        (
            "period_valid",
            "CHECK(end_at > start_at)",
            "The end of the leaderboard must be after its start.",
        ),
    ]

    # ------------------------------------------------------------------
    # Computes & constraints
    # ------------------------------------------------------------------
    @api.depends("leaderboard_type", "start_at", "campaign_id.name")
    def _compute_name(self):
        for board in self:
            if board.leaderboard_type == "campaign":
                board.name = board.campaign_id.name or _("Campaign")
            elif board.start_at:
                start = pytz.utc.localize(board.start_at).astimezone(LEADERBOARD_TZ)
                if board.leaderboard_type == "weekly":
                    iso_year, iso_week, _day = start.isocalendar()
                    board.name = _("Week %(week)s - %(year)s") % {
                        "week": iso_week,
                        "year": iso_year,
                    }
                else:
                    board.name = start.strftime("%m/%Y")
            else:
                board.name = False

    @api.depends("leaderboard_type", "campaign_id")
    def _compute_name_key(self):
        """Campaign leaderboards are keyed by their campaign. Weekly and
        monthly keys are given by the system when it creates them.
        """
        for board in self:
            if board.leaderboard_type == "campaign" and board.campaign_id:
                board.name_key = f"leaderboard.campaign.{board.campaign_id.id}"
            else:
                board.name_key = board.name_key

    @api.depends("campaign_id.start_date", "campaign_id.end_date")
    def _compute_period(self):
        for board in self:
            campaign = board.campaign_id
            # Once started, the period is frozen: changing the campaign dates
            # must not alter a live, closing or final leaderboard.
            if (
                board.leaderboard_type != "campaign"
                or not campaign
                or board.state in ("live", "closing", "final")
            ):
                continue
            if campaign.start_date:
                board.start_at = _local_to_utc(
                    datetime.combine(campaign.start_date, time.min)
                )
            if campaign.end_date:
                board.end_at = _local_to_utc(
                    datetime.combine(campaign.end_date, time(23, 59, 59))
                )

    @api.depends("state", "entry_ids")
    def _compute_participant_count(self):
        for board in self:
            if board.state == "final":
                board.participant_count = len(board.sudo().entry_ids)
            elif board.state in ("live", "closing"):
                board.participant_count = len(board._compute_ranking())
            else:
                board.participant_count = 0

    @api.constrains("leaderboard_type", "campaign_id")
    def _check_campaign(self):
        for board in self:
            if board.leaderboard_type == "campaign" and not board.campaign_id:
                raise ValidationError(_("A campaign leaderboard needs a campaign."))
            if board.leaderboard_type != "campaign" and board.campaign_id:
                raise ValidationError(
                    _("Only campaign leaderboards can be linked to a campaign.")
                )

    # ------------------------------------------------------------------
    # ORM overrides: protect the ranking from manual edition
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        is_system = _is_system(self.env)
        for vals in vals_list:
            if not is_system:
                if vals.get("leaderboard_type", "campaign") != "campaign":
                    raise UserError(
                        _("Weekly and monthly leaderboards are created automatically.")
                    )
                vals["created_by"] = self.env.uid
                # Computed from the campaign dates
                for fname in PERIOD_FIELDS:
                    vals.pop(fname, None)
            vals.pop("state", None)
        boards = super().create(vals_list)
        boards._update_state()
        return boards

    def write(self, vals):
        if not _is_system(self.env):
            if set(vals) & SYSTEM_FIELDS:
                raise UserError(_("The state of a leaderboard cannot be edited."))
            if set(vals) & PERIOD_FIELDS:
                raise UserError(
                    _(
                        "The period of a campaign leaderboard follows the dates "
                        "of its campaign: change the campaign dates instead."
                    )
                )
            if self.filtered(lambda b: b.state != "scheduled"):
                raise UserError(_("Only scheduled leaderboards can be edited."))
            if "leaderboard_type" in vals and vals["leaderboard_type"] != "campaign":
                raise UserError(_("Only campaign leaderboards can be edited."))
        elif self.filtered(lambda b: b.state == "final"):
            raise UserError(_("A final leaderboard cannot be modified."))
        res = super().write(vals)
        # Other campaign, so other period: start the leaderboard now if
        # needed, without waiting for the cron
        if not _is_system(self.env) and "campaign_id" in vals:
            self._update_state()
        return res

    def _is_cancellable(self):
        """A scheduled leaderboard can always be cancelled. A running campaign
        leaderboard too (e.g. created by mistake): live rankings are not
        stored, so nothing is lost. A final leaderboard holds the frozen
        ranking and is never deleted; running weekly and monthly
        leaderboards are managed by the system.
        """
        self.ensure_one()
        return self.state == "scheduled" or (
            self.leaderboard_type == "campaign" and self.state in ("live", "closing")
        )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_final_or_periodic(self):
        if self.filtered(lambda b: not b._is_cancellable()):
            raise UserError(
                _(
                    "Final leaderboards and running weekly or monthly "
                    "leaderboards cannot be cancelled."
                )
            )

    def action_cancel(self):
        """Admin action: cancel a scheduled or running campaign leaderboard."""
        self.unlink()
        return {"type": "ir.actions.act_window_close"}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _get_target_state(self, now):
        self.ensure_one()
        if now < self.start_at:
            return "scheduled"
        if now <= self.end_at:
            return "live"
        if now < self.end_at + CLOSING_DELAY:
            return "closing"
        return "final"

    def _update_state(self):
        """Move leaderboards forward in their lifecycle. Never goes backward."""
        order = ["scheduled", "live", "closing", "final"]
        now = fields.Datetime.now()
        system = self.with_context(leaderboard_system=True).sudo()
        for board in system:
            if board.state == "final":
                continue
            target = board._get_target_state(now)
            if order.index(target) <= order.index(board.state):
                continue
            if target == "final":
                board._finalize()
            else:
                board.state = target

    def _finalize(self):
        """Compute the ranking one last time and freeze it as entries."""
        self.ensure_one()
        ranking = self._compute_ranking()
        self.env["translation.leaderboard.entry"].with_context(
            leaderboard_system=True
        ).sudo().create(
            [
                {
                    "leaderboard_id": self.id,
                    "user_id": row["user_id"],
                    "rank": row["rank"],
                    "score": row["score"],
                    "score_reached_at": fields.Datetime.to_datetime(
                        row["score_reached_at"]
                    ),
                    "lifetime_count": row["lifetime_count"],
                }
                for row in ranking
            ]
        )
        self.with_context(leaderboard_system=True).sudo().write({"state": "final"})

    @api.model
    def _ensure_periodic_leaderboards(self):
        """Create the weekly and monthly leaderboards of the current period."""
        today = datetime.now(LEADERBOARD_TZ).date()
        to_create = []
        for period_type in ("weekly", "monthly"):
            start_at, end_at = _period_bounds(period_type, today)
            local_start = pytz.utc.localize(start_at).astimezone(LEADERBOARD_TZ)
            name_key = (
                "leaderboard.weekly.%s-W%02d" % local_start.isocalendar()[:2]
                if period_type == "weekly"
                else f"leaderboard.monthly.{local_start:%Y-%m}"
            )
            if not self.search_count([("name_key", "=", name_key)]):
                to_create.append(
                    {
                        "leaderboard_type": period_type,
                        "name_key": name_key,
                        "start_at": start_at,
                        "end_at": end_at,
                    }
                )
        if to_create:
            self.with_context(leaderboard_system=True).sudo().create(to_create)

    @api.model
    def cron_refresh_leaderboards(self):
        """Periodic job (every 10 minutes): leaderboard lifecycle only.

        Creates the weekly and monthly leaderboards, moves leaderboards
        through their states and freezes the final ranking. Live rankings are
        not stored: they are computed when the leaderboard is opened.
        """
        self._ensure_periodic_leaderboards()
        self.search([("state", "!=", "final")])._update_state()

    # ------------------------------------------------------------------
    # Ranking computation
    # ------------------------------------------------------------------
    def _compute_ranking(self):
        """Compute the strict ranking of the leaderboard from translation data.

        score            = number of validated translations in [start_at, end_at]
        score_reached_at = validation time of the translation that brought the
                           user to his current score (the latest counted one)
        Tie-breakers: score desc, score_reached_at asc, lifetime_count desc,
        user_id asc.
        Computed on each request: a single aggregated query, fast thanks to
        the index on correspondence.translate_done (~10 ms for a month).
        :return: list of dicts sorted by rank (only users with score >= 1)
        """
        self.ensure_one()
        groups = (
            self.env["correspondence"]
            .sudo()
            ._read_group(
                [
                    ("new_translator_id", "!=", False),
                    ("new_translator_id.active", "=", True),
                    ("new_translator_id.user_id.active", "=", True),
                    ("translation_status", "=", "done"),
                    ("translate_done", ">=", self.start_at),
                    ("translate_done", "<=", self.end_at),
                ],
                ["new_translator_id"],
                ["__count", "translate_done:max"],
            )
        )
        rows = [
            {
                "user_id": translator.user_id.id,
                "translator_id": translator.id,
                "score": count,
                "score_reached_at": reached_at,
                "lifetime_count": translator.nb_translated_letters,
            }
            for translator, count, reached_at in groups
            if count >= 1
        ]
        rows.sort(
            key=lambda r: (
                -r["score"],
                r["score_reached_at"],
                -r["lifetime_count"],
                r["user_id"],
            )
        )
        for rank, row in enumerate(rows, start=1):
            row["rank"] = rank
            row["score_reached_at"] = fields.Datetime.to_string(row["score_reached_at"])
        return rows

    # ------------------------------------------------------------------
    # Translation Platform API (live rankings computed on request)
    # ------------------------------------------------------------------
    @api.model
    def _get_default_leaderboard(self):
        campaign = self.search(
            [
                ("leaderboard_type", "=", "campaign"),
                ("state", "in", ["live", "closing"]),
            ],
            order="start_at desc",
            limit=1,
        )
        return campaign or self._get_current("weekly")

    @api.model
    def _get_current(self, leaderboard_type):
        return self.search(
            [
                ("leaderboard_type", "=", leaderboard_type),
                ("state", "in", ["live", "closing"]),
            ],
            order="start_at desc",
            limit=1,
        )

    @api.model
    def get_available_leaderboards(self):
        """Translation Platform API: tabs to display (campaign, week, month)."""
        boards = self.browse()
        for leaderboard_type in ("campaign", "weekly", "monthly"):
            boards |= self._get_current(leaderboard_type)
        default = self._get_default_leaderboard()
        return [
            {
                "id": board.id,
                "type": board.leaderboard_type,
                "nameKey": board.name_key,
                "name": board.name,
                "isDefault": board == default,
            }
            for board in boards
        ]

    def get_standings(self):
        """Translation Platform API: standings of the leaderboard for the
        current user. Called on an empty recordset, returns the default view
        (live campaign, otherwise current week).
        """
        board = self[:1] or self._get_default_leaderboard()
        if not board:
            return {}
        if board.state == "scheduled":
            raise UserError(_("This leaderboard has not started yet."))
        board = board.sudo()
        if board.state == "final":
            ranking = [
                {
                    "user_id": entry.user_id.id,
                    "rank": entry.rank,
                    "score": entry.score,
                }
                for entry in board.entry_ids.sorted("rank")
            ]
        else:
            ranking = board._compute_ranking()

        uid = self.env.uid
        my_index = next(
            (i for i, row in enumerate(ranking) if row["user_id"] == uid), None
        )
        top = ranking[:TOP_SIZE]
        around = []
        if my_index is not None and my_index >= TOP_SIZE:
            start = max(my_index - WINDOW_SIZE, TOP_SIZE)
            around = ranking[start : my_index + WINDOW_SIZE + 1]
        users = (
            self.env["res.users"]
            .sudo()
            .browse([row["user_id"] for row in top + around])
        )
        names = {user.id: user._get_leaderboard_name() for user in users}

        def _format(row):
            is_me = row["user_id"] == uid
            return {
                "rank": row["rank"],
                "score": row["score"],
                "displayName": names[row["user_id"]],
                "isCurrentUser": is_me,
            }

        result = {
            "id": board.id,
            "type": board.leaderboard_type,
            "nameKey": board.name_key,
            "name": board.name,
            "state": board.state,
            "startAt": fields.Datetime.to_string(board.start_at),
            "endAt": fields.Datetime.to_string(board.end_at),
            "participantCount": len(ranking),
            "top": [_format(row) for row in top],
            # Rows below the top 10 down to the current user (+2). Contiguous
            # with the top 10 when the user is ranked 11th or 12th.
            "around": [_format(row) for row in around],
            # True when there is a gap between the top 10 and "around":
            # the UI displays a separator (...) before this block.
            "showSeparator": bool(around) and around[0]["rank"] > TOP_SIZE + 1,
            # XML-RPC cannot marshal None: False means "not ranked"
            "myRank": ranking[my_index]["rank"] if my_index is not None else False,
            "myScore": ranking[my_index]["score"] if my_index is not None else 0,
        }
        if board.show_inactive_users and board.state != "final":
            ranked = {row["user_id"] for row in ranking}
            inactive = (
                self.env["translation.user"]
                .sudo()
                .search(
                    [("user_id", "not in", list(ranked)), ("user_id.active", "=", True)]
                )
            )
            result["notRanked"] = [
                {
                    "displayName": t.user_id._get_leaderboard_name(),
                    "isCurrentUser": t.user_id.id == uid,
                }
                for t in inactive
            ]
        return result

    @api.model
    def get_my_profile_standings(self):
        """Translation Platform API: leaderboard info for the user profile."""
        user = self.env.user
        board_model = self

        def _current(leaderboard_type):
            # XML-RPC cannot marshal None: False means "no leaderboard / not ranked"
            board = board_model._get_current(leaderboard_type).sudo()
            if not board:
                return False
            ranking = board._compute_ranking()
            row = next((r for r in ranking if r["user_id"] == user.id), None)
            return {
                "id": board.id,
                "type": board.leaderboard_type,
                "nameKey": board.name_key,
                "name": board.name,
                "state": board.state,
                "rank": row["rank"] if row else False,
                "score": row["score"] if row else 0,
                "participantCount": len(ranking),
            }

        best = (
            self.env["translation.leaderboard.entry"]
            .sudo()
            .search(
                [
                    ("user_id", "=", user.id),
                    ("leaderboard_id.leaderboard_type", "=", "campaign"),
                ],
                order="rank asc",
                limit=1,
            )
        )
        return {
            "weekly": _current("weekly"),
            "campaign": _current("campaign"),
            "bestCampaignRank": best.rank or False,
            "visibility": user.leaderboard_visibility,
        }


class TranslationLeaderboardEntry(models.Model):
    _name = "translation.leaderboard.entry"
    _description = "Translation Leaderboard Final Entry"
    _order = "leaderboard_id, rank"

    leaderboard_id = fields.Many2one(
        "translation.leaderboard",
        required=True,
        readonly=True,
        index=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users", required=True, readonly=True, index=True, ondelete="cascade"
    )
    rank = fields.Integer(required=True, readonly=True)
    score = fields.Integer(required=True, readonly=True)
    score_reached_at = fields.Datetime(required=True, readonly=True)
    lifetime_count = fields.Integer(required=True, readonly=True)

    _sql_constraints = [
        (
            "unique_user",
            "UNIQUE(leaderboard_id, user_id)",
            "A user can only appear once in a leaderboard.",
        ),
        (
            "unique_rank",
            "UNIQUE(leaderboard_id, rank)",
            "Two users cannot share the same rank.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_system(self.env):
            raise UserError(_("Leaderboard entries are written by the system only."))
        return super().create(vals_list)

    def write(self, vals):
        if not _is_system(self.env):
            raise UserError(_("A final leaderboard ranking cannot be modified."))
        return super().write(vals)
