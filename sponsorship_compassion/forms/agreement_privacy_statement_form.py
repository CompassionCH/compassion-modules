##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import datetime

from odoo.http import request
from odoo import models, fields, _


class PrivacyStatementForm(models.AbstractModel):
    """ Form to display the privacy statement and make the user accept it.
     The statement id that is displayed should be passed to the method
     form_init using the key privacy_statement_id """

    _name = "cms.form.partner.privacy.statement"
    _inherit = "cms.form"

    _form_model = "res.partner"

    privacy_statement_id = None
    privacy_statement_agreement = fields.Boolean(
        "Check to agree to the privacy statement"
    )

    _form_model_fields = ["privacy_statement_agreement"]
    _form_required_fields = ["privacy_statement_agreement"]

    def form_init(self, req, main_object=None, **kw):
        form = super(PrivacyStatementForm, self).form_init(
            req, main_object, **kw
        )
        form.privacy_statement_id = kw["privacy_statement_id"]
        return form

    @property
    def form_msg_success_updated(self):
        return _("Thank you for reading the privacy statement carefully.")

    @property
    def _form_fieldsets(self):
        return [
            {
                "id": "agreements",
                "description": _(
                    "I acknowledge that I have read and "
                    "fully understood the content of the privacy statement. "
                    "I agree with all the conditions mentioned above. "
                    "If I do not comply with these conditions,"
                    "Compassion reserves the right to deactivate my "
                    "translator account and cancel my sponsorships."
                ),
                "fields": ["privacy_statement_agreement"],
            }
        ]

    def form_cancel_url(self, main_object=None):
        """URL to redirect to after click on "cancel" button."""
        redirect = request.httprequest.args.get("redirect")
        return redirect if redirect else request.httprequest.full_path

    def form_before_create_or_update(self, write_values, extra_values):
        pass

    def form_after_create_or_update(self, values, extra_values):
        if extra_values.get("privacy_statement_agreement"):
            agreement = request.env["privacy.statement.agreement"].sudo()\
                .create({
                    "partner_id": self.main_object.id,
                    "agreement_date": datetime.today(),
                    "privacy_statement_id": self.privacy_statement_id.id,
                    "version": self.privacy_statement_id.version,
                    "origin_signature": "my_account",
                })
            self.main_object.write({
                "privacy_statement_ids": [(6, 0, [agreement.id])]
            })
