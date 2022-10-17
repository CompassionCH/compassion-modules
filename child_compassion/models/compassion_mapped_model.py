import logging
import re

from odoo import models, _

from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector
from odoo.tools import flatten

_logger = logging.getLogger(__name__)


class MappedModel(models.AbstractModel):
    _inherit = "compassion.mapped.model"

    @property
    def translated_fields(self):
        """
        Should return all fields that contain terms translated.
        """
        return []

    def _get_ir_translated_fields(self):
        """
        Returns a dict with key the full field name and value the corresponding ir.model.field record.
        """
        res = dict()
        for full_field_name in self.translated_fields:
            relation, sep, f_name = full_field_name.rpartition(".")
            record = self
            if relation:
                record = self.mapped(relation)
            res[full_field_name] = self.env["ir.model.fields"].sudo().search([
                ("model", "=", record._name),
                ("name", "=", f_name)
            ])
        return res

    def _fetch_translations(self, gmc_action):
        """
        Contact GMC service in all installed languages in order to fetch all terms used in record description.
        """
        onramp = OnrampConnector(self.env)
        to_translate_manually = self.env[self._name]
        for lang in self.env["res.lang.compassion"].with_context(lang="en_US").search([
                ("translatable", "=", True), ("code_iso", "!=", "eng")]):
            for translated_record in self.with_context(lang=lang.lang_id.code):
                service_url = translated_record._get_service_url(gmc_action)
                english_record = translated_record.with_context(lang="en_US")
                gmc_result = onramp.send_message(service_url + f"?FinalLanguage={lang.name}", "GET")
                if gmc_result.get("code") != 200:
                    _logger.warning("Language not available at GMC: %s", lang.name)
                    continue
                gmc_data = gmc_result.get("content")
                gmc_english_data = onramp.send_message(service_url, "GET").get("content")
                if gmc_action.connect_answer_wrapper:
                    gmc_data = gmc_data[gmc_action.connect_answer_wrapper]
                    gmc_english_data = gmc_english_data[gmc_action.connect_answer_wrapper]
                # We want to deal with all possible received values, there can be multiple.
                if not isinstance(gmc_data, list):
                    gmc_data = [gmc_data]
                    gmc_english_data = [gmc_english_data]
                for full_field_name, t_field in translated_record._get_ir_translated_fields().items():
                    english_vals = english_record.mapped(full_field_name)
                    translated_vals = translated_record.mapped(full_field_name)
                    gmc_terms = english_vals
                    if full_field_name.endswith(".value"):
                        # Exception for multipicklist records where the gmc_terms are stored in "name" field
                        gmc_terms = english_record.mapped(full_field_name.replace(".value", ".name"))
                    f_type = t_field.ttype
                    for i, english_val in enumerate(english_vals):
                        # Update term only if English is the same as the translated
                        if english_val and english_val == translated_vals[i]:
                            new_translation = self._find_translation(
                                full_field_name, gmc_terms[i], gmc_action, gmc_data, gmc_english_data)
                            if new_translation == english_val:
                                to_translate_manually += english_record
                            if f_type == "selection":
                                # Update selection label translation.
                                s_field = lang.env["ir.model.fields.selection"].sudo().search([
                                    ("field_id", "=", t_field.id),
                                    ("name", "=", english_val)
                                ])
                                if s_field:
                                    s_field.with_context(lang=lang.lang_id.code).name = new_translation
                                else:
                                    # The selection is not stored, maybe it's translated in the code.
                                    lang.env["ir.translation"].search([
                                        ("lang", "=", lang.lang_id.code),
                                        ("src", "=ilike", english_val)
                                    ]).value = new_translation
                            else:
                                # Write the value inside the correct relation
                                record = translated_record
                                relation, sep, f_name = full_field_name.rpartition(".")
                                if relation:
                                    record = translated_record.mapped(relation)[i]
                                record.write({t_field.name: new_translation})
        if to_translate_manually:
            to_translate_manually.assign_translation()
        return True

    def edit_translations(self):
        """
        Returns action with domain for translating all values of the record
        """
        domain_parts = []
        for f_name, t_field in self._get_ir_translated_fields().items():
            if t_field.ttype == "selection":
                f_sel = t_field.selection_ids.filtered(lambda s: s.value in self.mapped(t_field.name))
                if f_sel:
                    domain_parts += [["&", ("res_id", "in", f_sel.ids), ("name", "like", "ir.model.fields.selection,")]]
                else:
                    srcs = self.with_context(lang="en_US").mapped(f_name)
                    if any(srcs):
                        domain_parts.append([("src", "in", srcs)])
            else:
                recs = self
                model_name, sep, final_field = f_name.rpartition(".")
                if model_name:
                    recs = self.mapped(model_name)
                if recs:
                    self.env["ir.translation"].insert_missing(self.env[recs._name]._fields[final_field], recs)
                    domain_parts += [["&", ("res_id", "in", recs.ids), ("name", "=ilike", f"{recs._name},%")]]
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

    def _find_translation(self, field_name, gmc_term, gmc_action, gmc_data, gmc_english_data):
        """
        Find a translation inside received GMC data. It will traverse the data in order to extract the desired values.

        :param field_name: full field_name (in Odoo) used to lookup inside gmc_data
        :param gmc_term: english value of the term expected from GMC
        :param gmc_action: GMC action providing the data
        :param gmc_data: Received GMC data in the desired language (list of data)
        :param gmc_english_data: Received GMC data in English (list of data)
        """
        field_path = field_name.split(".")
        field_mappings = gmc_action.mapping_id.json_spec_ids
        for field_part in field_path:
            field_mappings = field_mappings.filtered(
                lambda m: m.field_name == field_part or m.relational_field_id.name == field_part)
            keys_to_keep = field_mappings.mapped("json_name")
            gmc_data = self._filter_gmc_data(gmc_data, keys_to_keep)
            gmc_english_data = self._filter_gmc_data(gmc_english_data, keys_to_keep)
            if field_mappings.filtered("sub_mapping_id"):
                field_mappings = field_mappings.mapped("sub_mapping_id.json_spec_ids")
            else:
                break

        # Flatten the list of dictionaries in case the terms are spread into multiple fields
        gmc_data = flatten(map(lambda d: d.values() if isinstance(d, dict) else d, gmc_data))
        gmc_english_data = flatten(map(lambda d: d.values() if isinstance(d, dict) else d, gmc_english_data))
        try:
            translation_index = gmc_english_data.index(gmc_term)
            return gmc_data[translation_index]
        except (ValueError, IndexError):
            _logger.error("English term \"%s\" not found in data received from GMC: %s",
                          gmc_term, str(gmc_english_data))
            return gmc_term

    def _filter_gmc_data(self, gmc_data, keys_to_keep):
        """
        Utility for extracting values from JSON data from GMC.
        The data itself can be recursive lists and dictionaries, so the filtering
        process needs to find the keys inside the complex structure.

        :param gmc_data: JSON dict values or list of dicts.
        :param keys_to_keep: list of keys found in gmc_data
        :return: filtered list of dicts that contain given keys.
        """
        res = list()
        if not isinstance(gmc_data, list):
            gmc_data = [gmc_data]
        for item in gmc_data:
            if isinstance(item, dict):
                extract = dict()
                for key, value in item.items():
                    if key in keys_to_keep:
                        extract[key] = value
                    elif isinstance(value, (list, dict)):
                        res.extend(self._filter_gmc_data(value, keys_to_keep))
                if extract:
                    res.append(extract)
        return res
