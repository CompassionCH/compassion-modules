##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


class SuccessStory(models.Model):
    _name = "success.story"
    _description = "Success Story: story in a blue layout added in letters."
    _order = "state asc, print_count asc, date_start asc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char()
    type = fields.Selection(
        [("story", "Story"), ("sentence", "Sentence")], default="story", required=True
    )
    body = fields.Html(translate=True, sanitize=False)
    body_text = fields.Text(translate=True)
    date_start = fields.Date(
        readonly=True, states={"new": [("readonly", False)]}, copy=False
    )
    date_stop = fields.Date(
        readonly=True, states={"new": [("readonly", False)]}, copy=False
    )
    is_active = fields.Boolean(copy=False)
    state = fields.Selection(
        [("new", "New"), ("active", "Active"), ("used", "Used")],
        compute="_compute_state",
        store=True,
        default="new",
        copy=False,
    )
    only_when_chosen = fields.Boolean(
        help="Set this to use the story only for given products or when "
        "manually chosen. The story won't be used automatically."
    )
    print_count = fields.Integer(copy=False)
    current_usage_count = fields.Integer(compute="_compute_current_usage")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends("is_active")
    def _compute_state(self):
        for story in self:
            if story.is_active:
                story.state = "active"
            else:
                story.state = "used" if story.print_count else "new"

    def _compute_current_usage(self):
        for story in self:
            story.current_usage_count = self.env[
                "partner.communication.job"
            ].search_count(
                [("success_story_id", "=", story.id), ("state", "!=", "cancel")]
            )

    @api.constrains("date_start", "date_stop")
    def _check_dates(self):
        for story in self.filtered(lambda s: s.type == "story"):
            date_start = story.date_start
            date_stop = story.date_stop
            if date_stop <= date_start:
                raise ValidationError(_("Period is not valid"))

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def validity_cron(self):
        today = fields.Date.today()
        active_stories = self.search(
            [
                ("is_active", "=", True),
                ("type", "=", "story"),
            ]
        )
        current_stories = self.search(
            [
                ("date_start", "<=", today),
                ("date_stop", ">=", today),
                ("type", "=", "story"),
            ]
        )
        # Deactivate old stories
        (active_stories - current_stories).write({"is_active": False})
        # Activate current stories
        current_stories.write({"is_active": True})
