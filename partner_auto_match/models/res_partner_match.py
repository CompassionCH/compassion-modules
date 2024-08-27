##############################################################################
#
#    Copyright (C) 2019-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime, timedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartnerMatch(models.AbstractModel):
    """
    Allows the matching of a partner from some given information.
    Can be extended or inherited to change the behaviour for some particular
    case.
    """

    _name = "res.partner.match"
    _description = "Match partner"

    @api.model
    def match_values_to_partner(self, vals, match_update=False, match_create=True):
        """
        Find the partner that match the given info or create one if none exists
        :param match_create: Allow creation of a new partner if none is found
        :param match_update: Allow update of partner vals after matching succeeded
        :param vals: A dict containing the information available to find the partner.
                     The keys should match the fields of res.partner.
        :return: The matched partner.
        """
        self._preprocess_vals(vals)
        partner = partner_obj = self.env["res.partner"]
        partner_id = vals.get("partner_id")
        if partner_id:
            partner = partner_obj.browse(partner_id).exists()

        for rule in self._match_get_rules_order():
            if len(partner) == 1:
                # Found a unique partner, match succeeded
                break

            # Applying successive rules in order to find a partner
            try:
                method = getattr(self, "_match_" + rule)
                partner = method(vals)
            except (AttributeError, KeyError):
                _logger.error("Matching rule %s not implemented correctly.", rule)
                continue

        # Postprocess partner (either update or create it depending on context options)
        if partner and len(partner) == 1 and match_update:
            self.update_partner(partner, vals)
        if not partner and match_create:
            partner = self._create_partner(vals)
        return partner

    @api.model
    def _create_partner(self, vals):
        """Create a new partner from a selection of the given infos."""
        create_infos = self._process_create_infos(vals)
        partner = self.env["res.partner"].create(create_infos)
        partner.activity_schedule(
            "partner_auto_match.activity_check_duplicates",
            date_deadline=datetime.date(datetime.today() + timedelta(weeks=1)),
            summary="Verify new partner",
            note="Please verify that this partner doesn't already exist",
            user_id=self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_auto_match.match_validation_responsible", self.env.uid),
        )
        return partner

    @api.model
    def _process_create_infos(self, vals):
        """
        From the info given by the user, select the one that should be used
        for the creation of the partner.
        """
        valid = self._get_valid_create_fields()
        create_infos = {}
        for key, value in vals.items():
            if key in valid:
                create_infos[key] = value
        create_infos.setdefault("lang", self.env.lang)
        create_infos.setdefault("tz", "Europe/Zurich")
        return create_infos

    @api.model
    def update_partner(self, partner, vals, async_mode=True, delay=1):
        delay = datetime.now() + timedelta(minutes=delay)
        filtered_vals = self._process_update_vals(partner, vals)
        partner_context = {"skip_check_zip": True, "no_upsert": True}
        if async_mode:
            partner.with_context(partner_context).with_delay(eta=delay).write(
                filtered_vals
            )
        else:
            partner.with_context(partner_context).write(filtered_vals)

    @api.model
    def _preprocess_vals(self, vals):
        """Transform, if needed and before matching, the infos received"""
        vals["name"] = vals["name"].strip(' -')

    @api.model
    def _process_update_vals(self, partner, vals):
        """
        From the info given by the user, select the one that should be used
        for the update of the partner.
        """
        valid = self._get_valid_update_fields()
        update_infos = {}
        partner_vals = partner.read(vals.keys())[0]
        for key, value in vals.items():
            if key in valid and partner_vals[key] != value:
                update_infos[key] = value
        return update_infos

    @api.model
    def _match_get_rules_order(self):
        """
        Get, in order, the name of the methods used to find a matching partner.
        Each of the listed method must take a partner_obj and the infos as
        their parameter. They must also return a recordset of partner.
        """
        return ["email_and_name", "name_and_zip"]

    @api.model
    def _match_email_and_name(self, vals):
        email = vals["email"].strip()
        return self.env["res.partner"].search(
            [
                ("name", "ilike", vals["name"]),
                ("email", "=ilike", email),
            ]
        )

    @api.model
    def _match_name_and_zip(self, vals):
        return self.env["res.partner"].search(
            [
                ("name", "ilike", vals["name"]),
                ("zip", "=", vals["zip"]),
            ]
        )

    @api.model
    def _get_valid_create_fields(self):
        """Return the fields which can be used at creation."""
        return [
            "name",
            "email",
            "phone",
            "mobile",
            "street",
            "city",
            "zip",
            "state_id",
            "country_id",
            "title",
            "lang",
            "function",
        ]

    @api.model
    def _get_valid_update_fields(self):
        """Return the fields which can be used at update."""
        return [
            "email",
            "phone",
            "mobile",
            "street",
            "city",
            "zip",
            "state_id",
            "country_id",
            "state_id",
            "function",
            "lang",
            "title",
        ]

