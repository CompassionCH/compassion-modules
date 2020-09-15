##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta

from odoo.addons.queue_job.job import job

from odoo import api, models


class MatchPartner(models.AbstractModel):
    """
    Allows the matching of a partner from some given information.
    Can be extended or inherited to change the behaviour for some particular
    case.
    """

    _name = "res.partner.match"
    _description = "Match partner"

    @api.model
    def match_partner_to_infos(self, infos, options=None):
        """
        Find the partner that match the given info or create one if none exists
        :param infos: A dict containing the information available to find the
            partner.
            The keys should match the fields of res.partner. There is one
            exception, the partner_id key (be careful with it).
        :param options: An optional dict containing the options parameters.
        :return: The matched partner.
        """
        if options is None:
            options = {}

        # Default options
        opt = {
            "skip_create": False,  # When True, do not create a partner and
            # return None if no match is found.
            "skip_update": False,  # When True, do not use the given infos to
            # update the partner's fields.
        }
        opt.update(options)

        self.match_process_infos(infos, opt)

        new_partner = False
        partner_obj = self.env["res.partner"].sudo()
        partner = False

        partner_id = infos.get("partner_id")
        if partner_id:
            partner = partner_obj.browse(partner_id)

        for rule in self._match_get_rules_order():
            if not partner or len(partner) > 1:
                method = getattr(self, "_match_rule_" + rule)
                try:
                    partner = method(partner_obj, infos, opt)
                except KeyError:
                    # Not enough info for the matching rule
                    partner = False
            else:
                break

        if not partner or len(partner) > 1:
            # no match found or not sure which one -> creating a new one.
            if opt.get("skip_create"):
                return None
            else:
                partner = self.match_create(partner_obj, infos, opt)
                new_partner = True

        partner = self.match_after_match(partner, new_partner, infos, opt)

        return partner

    @api.model
    def match_after_match(self, partner, new_partner, infos, opt):
        """Once a match is found or created, this method allows to change it"""
        if not new_partner and not opt.get("skip_update"):
            delay = datetime.now() + timedelta(minutes=1)
            self.with_delay(eta=delay).match_update(partner, infos, opt)
        return partner

    @api.model
    def match_create(self, partner_obj, infos, options=None):
        """Create a new partner from a selection of the given infos."""
        create_infos = self.match_process_create_infos(infos, options)
        create_infos.setdefault("lang", self.env.lang)
        create_infos.setdefault("tz", "Europe/Zurich")
        partner = partner_obj.create(create_infos)
        partner.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=datetime.date(datetime.today() + timedelta(weeks=1)),
            summary="Verify new partner",
            note="Please verify that this partner doesn't already exist",
            user_id=self.env["ir.config_parameter"].sudo().get_param(
                "cms_form_compassion.match_validation_responsible")
        )
        return partner

    @api.model
    def match_process_create_infos(self, infos, options=None):
        """
        From the info given by the user, select the one that should be used
        for the creation of the partner.
        """
        valid = self._match_get_valid_create_fields()
        create_infos = {}
        for key, value in infos.items():
            if key in valid:
                create_infos[key] = value

        return create_infos

    @api.model
    @job
    def match_update(self, partner, infos, options=None):
        """Update the matched partner with a selection of the given infos."""
        update_infos = self.match_process_update_infos(infos, options)
        partner.with_context({"skip_check_zip": True}).write(update_infos)

    @api.model
    def match_process_infos(self, infos, options=None):
        """Transform, if needed and before matching, the infos received"""
        if "church_name" in infos:
            self._match_church(infos, options)

    @api.model
    def match_process_update_infos(self, infos, options=None):
        """
        From the info given by the user, select the one that should be used
        for the update of the partner.
        """
        valid = self._match_get_valid_update_fields()
        update_infos = {}
        for key, value in infos.items():
            if key in valid and value:
                update_infos[key] = value
        return update_infos

    @api.model
    def _match_church(self, infos, options=None):
        church_name = infos.pop("church_name")
        church = (
            self.env["res.partner"]
                .with_context(lang="en_US")
                .search(
                [("name", "like", church_name), ("category_id.name", "=", "Church")]
            )
        )
        if len(church) == 1:
            infos["church_id"] = church.id
        else:
            infos["church_unlinked"] = church_name

    @api.model
    def _match_get_rules_order(self):
        """
        Get, in order, the name of the methods used to find a matching partner.
        Each of the listed method must take a partner_obj and the infos as
        their parameter. They must also return a recordset of partner.
        """
        return ["email", "fullname_and_zip"]

    @api.model
    def _match_rule_email(self, partner_obj, infos, options=None):
        email = infos["email"].strip()
        return partner_obj.search(
            [
                ("email", "=ilike", email),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )

    @api.model
    def _match_rule_fullname_and_zip(self, partner_obj, infos, options=None):
        return partner_obj.search(
            [
                ("lastname", "ilike", infos["lastname"]),
                ("firstname", "ilike", infos["firstname"]),
                ("zip", "=", infos["zip"]),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )

    @api.model
    def _match_get_valid_create_fields(self):
        """Return the fields which can be used at creation."""
        return [
            "firstname",
            "lastname",
            "email",
            "phone",
            "mobile",
            "street",
            "city",
            "zip",
            "zip_id",
            "city_id",
            "state_id",
            "country_id",
            "state_id",
            "title",
            "lang",
            "birthdate",
            "church_unlinked",
            "church_id",
            "function",
            "spoken_lang_ids",
            "opt_out",
            "image"
        ]

    @api.model
    def _match_get_valid_update_fields(self):
        """Return the fields which can be used at update."""
        return [
            "email",
            "phone",
            "mobile",
            "street",
            "city",
            "zip",
            "zip_id",
            "city_id",
            "state_id",
            "country_id",
            "state_id",
            "church_unlinked",
            "church_id",
            "function",
            "spoken_lang_ids",
            "opt_out",
            "image"
        ]
