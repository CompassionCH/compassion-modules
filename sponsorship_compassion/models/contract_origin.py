##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from psycopg2 import IntegrityError

from odoo import models, fields, api, _

logger = logging.getLogger(__name__)


class ContractOrigin(models.Model):
    """ Origin of a contract """

    _name = "recurring.contract.origin"
    _description = "Recurring Contract Origin"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(compute="_compute_name", store=True)
    type = fields.Selection(
        "_get_origin_types",
        help="Origin of contract : "
             " * Contact with sponsor/ambassador : an other sponsor told the "
             "person about Compassion."
             " * Event : sponsorship was made during an event"
             " * Marketing campaign : sponsorship was made after specific "
             "campaign (magazine, ad, etc..)"
             " * Crowdfunding : sponsorship obtained from a crowdunfding project"
             " * Transfer : sponsorship transferred from another country."
             " * Other : select only if none other type matches.",
        required=True,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", "Partner", readonly=False)
    analytic_id = fields.Many2one(
        "account.analytic.account", "Analytic Account", readonly=False
    )
    contract_ids = fields.One2many(
        "recurring.contract", "origin_id", "Sponsorships originated", readonly=True
    )
    country_id = fields.Many2one("res.country", "Country", readonly=False)
    other_name = fields.Char("Give details", size=128)
    won_sponsorships = fields.Integer(compute="_compute_won_sponsorships", store=True)
    conversion_rate = fields.Float(compute="_compute_won_sponsorships", store=True)

    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            _(
                "You cannot have two origins with same name."
                "The origin does probably already exist."
            ),
        )
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends("type")
    def _compute_name(self):
        for origin in self:
            name = ""
            if origin.type == "partner":
                if origin.partner_id.parent_id:
                    name = origin.partner_id.parent_id.name + ", "
                name += origin.partner_id.name or _("Contact with Sponsor/Ambassador")
            elif origin.type in ("event", "marketing"):
                name = origin.analytic_id.name
            elif origin.type == "crowdfunding":
                name = origin.event_id.name
            elif origin.type == "transfer":
                if origin.country_id:
                    name = _("Transfer from ") + origin.country_id.name
                else:
                    name = _("Transfer from partner country")
            elif origin.type == "other":
                name = origin.other_name or "Other"

            origin.name = name

    def _get_origin_types(self):
        return [
            ("partner", _("Contact with sponsor/ambassador")),
            ("event", _("Event")),
            ("marketing", _("Marketing campaign")),
            ("crowdfunding", _("Crowdfunding")),
            ("transfer", _("Transfer")),
            ("other", _("Other")),
        ]

    @api.depends("contract_ids.origin_id", "contract_ids.activation_date")
    @api.multi
    def _compute_won_sponsorships(self):
        for origin in self.filtered("contract_ids"):
            # not tacking sponsors with parent_id or in cancelled state.
            contract_ids = origin.contract_ids.filtered(lambda c: not c.parent_id)
            origin.won_sponsorships = len(contract_ids.filtered(lambda c: c.state != "cancelled"))
            # sponsor who cancelled their sponsorship are used to compute conversion_rate to avoid bias
            origin.conversion_rate = (
                len(contract_ids.filtered("activation_date"))
                / float(len(contract_ids))
                * 100
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """Try to find existing origin instead of raising an error."""
        try:
            res = super().create(vals)
        except IntegrityError as error:
            # Find the origin
            logger.error(str(error))
            self.env.cr.rollback()
            self.env.clear()
            origin = self._find_same_origin(vals)
            if origin:
                res = origin
            else:
                raise

        # Put analytic account of the user if it exists
        partner = res.partner_id
        if res.type == "partner" and partner and not res.analytic_id:
            partner_name = partner.name
            if partner.parent_id:
                partner_name = partner.parent_id.name + ", " + partner_name
            analytic_account = (
                self.env["account.analytic.account"]
                    .with_context(lang="en_US")
                    .search([("name", "=", partner_name)], limit=1)
            )
            res.analytic_id = analytic_account

        return res

    def _find_same_origin(self, vals):
        return self.search(
            [
                ("type", "=", vals.get("type")),
                ("partner_id", "=", vals.get("partner_id")),
                ("analytic_id", "=", vals.get("analytic_id")),
                ("country_id", "=", vals.get("country_id")),
                ("other_name", "=", vals.get("other_name")),
            ],
            limit=1,
        )
