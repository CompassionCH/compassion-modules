##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime as dt

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    interaction_resume_ids = fields.One2many(
        "interaction.resume", "partner_id", "Interaction resume"
    )

    # Do not clutter the mail thread with emails that can be seen in
    # interaction resume
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [
            ("model", "=", self._name),
            ("subtype_id", "in", [self.env.ref("mail.mt_note").id]),
        ],
        auto_join=True,
    )
    last_interaction_fetch_date = fields.Datetime(
        "Last interaction fetch date",
        help="Last date the interactions were fetched for this partner",
        readonly=True,
    )
    last_interaction_fetch_page = fields.Integer(required=True, default=0)

    def open_interaction(self):
        self.ensure_one()
        if not self.interaction_resume_ids:
            self.fetch_interactions()
        return {
            "name": _("Interaction resume"),
            "type": "ir.actions.act_window",
            "res_model": "interaction.resume",
            "view_mode": "tree,form",
            "context": {"search_default_partner_id": self.id},
        }

    def fetch_interactions(
        self,
        page=0,
    ):
        """
        Get interactions for a partner
        :param page: page number for fetching the past years
        :return: total number interaction found, for knowing if more
                 interactions exist further in the past.
        """
        self.ensure_one()
        # Each page shows interactions for two years
        years_to_fetch = 2
        years = page * years_to_fetch
        # Do not fetch invalid negative years interactions
        if years > dt.now().year:
            return True
        until = fields.Datetime.now() - relativedelta(years=years)
        since = until - relativedelta(years=years_to_fetch)
        models = [
            "partner.communication.job",
            "crm.claim",
            "crm.phonecall",
            "sms.sms",
            "mailing.trace",
            "partner.log.other.interaction",
        ]
        for model in models:
            self.env[model].fetch_interaction(self, since, until)
        self.last_interaction_fetch_date = fields.Datetime.now()
        self.last_interaction_fetch_page += page
        return True
