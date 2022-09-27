import logging
import re

from odoo import models, _

from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector

_logger = logging.getLogger(__name__)


class MappedModel(models.AbstractModel):
    _inherit = "compassion.mapped.model"

    @property
    def translated_fields(self):
        """
        Should return all fields that contain terms translated.
        """
        return []

    def _fetch_translations(self, gmc_action):
        """
        Contact GMC service in all installed languages in order to fetch all terms used in record description.
        """
        onramp = OnrampConnector()
        to_translate_manually = self.env[self._name]
        for lang in self.env["res.lang.compassion"].with_context(lang="en_US").search([
                ("translatable", "=", True), ("code_iso", "!=", "eng")]):
            for translated_record in self.with_context(lang=lang.lang_id.code):
                service_url = translated_record._get_service_url(gmc_action)
                english_record = translated_record.with_context(lang="en_US")
                gmc_data = onramp.send_message(service_url + f"?FinalLanguage={lang.name}", "GET").get("content")
                gmc_english_data = onramp.send_message(service_url, "GET").get("content")
                if gmc_action.connect_answer_wrapper:
                    gmc_data = gmc_data[gmc_action.connect_answer_wrapper]
                    gmc_english_data = gmc_english_data[gmc_action.connect_answer_wrapper]
                if isinstance(gmc_data, list):
                    gmc_data = gmc_data[0]
                    gmc_english_data = gmc_english_data[0]
                for t_field, t_attrs in translated_record.fields_get(
                        self.translated_fields, ["type", "relation"]).items():
                    english_vals = english_record.mapped(t_field)
                    translated_vals = translated_record.mapped(t_field)
                    gmc_terms = english_vals
                    f_type = t_attrs["type"]
                    if f_type in ("one2many", "many2many"):
                        # connect.multipicklist related objects
                        english_vals = english_vals.mapped("value")
                        translated_vals = translated_vals.mapped("value")
                        gmc_terms = gmc_terms.mapped("name")
                    elif f_type == "many2one":
                        english_vals = english_vals.mapped("name")
                        gmc_terms = english_vals
                        translated_vals = translated_vals.mapped("name")
                    for i, english_val in enumerate(english_vals):
                        # Update term only if English is the same as the translated
                        if english_val and english_val == translated_vals[i]:
                            json_names = gmc_action.mapping_id.json_spec_ids.filtered(
                                lambda m: t_field == m.field_name or (
                                        t_field == m.relational_field_id.name and
                                        t_attrs.get("relation") == m.field_id.model)
                            ).mapped("json_name")
                            gmc_translated_vals = list()
                            gmc_english_vals = list()
                            for jname in json_names:
                                t_val = gmc_data.get(jname, [])
                                e_val = gmc_english_data.get(jname, [])
                                if not isinstance(e_val, list):
                                    t_val = [t_val]
                                    e_val = [e_val]
                                gmc_translated_vals += t_val
                                gmc_english_vals += e_val
                            if not gmc_translated_vals:
                                continue
                            try:
                                translation_index = gmc_english_vals.index(gmc_terms[i])
                                new_translation = gmc_translated_vals[translation_index]
                            except ValueError:
                                _logger.error("English term \"%s\" not found in data received from GMC: %s",
                                              gmc_terms[i], str(gmc_english_vals))
                            if new_translation == english_val:
                                to_translate_manually += english_record
                            if f_type in ("one2many", "many2many"):
                                # This should be a connect.multipicklist for which we update the value field.
                                translated_record.mapped(t_field)[i].value = new_translation
                            elif f_type == "many2one":
                                # In that case we update the name field of the relation.
                                translated_record.mapped(t_field).name = new_translation
                            elif f_type == "selection":
                                # Update selection label translation.
                                o_field = lang.env["ir.model.fields"].search([  # Fetch in English
                                    ("model", "=", self._name),
                                    ("name", "=", t_field)
                                ])
                                s_field = lang.env["ir.model.fields.selection"].search([
                                    ("field_id", "=", o_field.id),
                                    ("name", "=", english_val)
                                ])
                                s_field.with_context(lang=lang.lang_id.code).name = new_translation
                            else:
                                translated_record.write({t_field: new_translation})
        if to_translate_manually:
            to_translate_manually.assign_translation()
        return True

    def edit_translations(self):
        """
        Returns action with domain for translating all values of the record
        """
        domain_parts = []
        for t_field, attrs in self.fields_get(self.translated_fields, ["type"]).items():
            if attrs["type"] in ["one2many", "many2many", "many2one"]:
                recs = self.mapped(t_field)
                if recs:
                    domain_parts += [["&", ("res_id", "in", recs.ids), ("name", "=ilike", f"{recs._name},%")]]
            elif attrs["type"] == "selection":
                f_sel = self.env["ir.model.fields"].search([
                    ("name", "=", t_field), ("model", "=", self._name)
                ]).selection_ids.filtered(lambda s: s.value in self.mapped(t_field))
                if f_sel:
                    domain_parts += [["&", ("res_id", "in", f_sel.ids), ("name", "like", "ir.model.fields.selection,")]]
        domain = ["|"] * (len(domain_parts) - 1)
        for d in domain_parts:
            domain += d
        action = {
            'name': _('Translate'),
            'res_model': 'ir.translation',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('base.view_translation_dialog_tree').id,
            'target': 'current',
            'domain': domain,
            'context': {},
        }
        return action

    def assign_translation(self):
        """Assign an activity for manually translating the value."""
        # Remove previous todos
        self.activity_unlink("mail.mail_activity_data_todo")
        notify_ids = self.env["res.config.settings"].sudo().get_param("translate_notify_ids")
        if notify_ids:  # check if not False
            for user_id in notify_ids[0][2]:
                act_vals = {"user_id": user_id}
                self.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("A new value needs translation"),
                    note=_(
                        "This is a new value that needs translation "
                        "for printing the child dossier."),
                    **act_vals
                )

    def _get_service_url(self, gmc_action):
        assert gmc_action.model == self._name
        self.ensure_one()
        url_endpoint = gmc_action.connect_service

        def _replace_object_string(object_match):
            """ Takes a string like ${object.field} and returns the field. """
            field_name = object_match.groups()[1]
            field_value = self.mapped(field_name)[0]
            return str(field_value)

        if "${object" in url_endpoint:
            url_endpoint = re.sub(
                r"\$\{(object\.)(.+?)\}",
                lambda match: _replace_object_string(match),
                url_endpoint,
            )
        return url_endpoint
