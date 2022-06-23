from odoo import api, models, fields


class TranslationCompetence(models.Model):
    _name = "translation.competence"
    _description = "Compassion Translation Competence"

    source_language_id = fields.Many2one(
        "res.lang.compassion", "Source language", domain=[("translatable", "=", True)], required=True, index=True
    )
    dest_language_id = fields.Many2one(
        "res.lang.compassion", "Destination language", domain=[("translatable", "=", True)], required=True, index=True
    )
    name = fields.Char(compute="_compute_name")

    _sql_constraints = [
        ("unique_competence", "unique(source_language_id,dest_language_id)", "This competence already exists.")
    ]

    def _compute_name(self):
        for competence in self:
            competence.name = competence.source_language_id.name + " -> " + competence.dest_language_id.name

    @api.model
    def get_translation_languages(self):
        """
        Translation API returning all available languages for translation.
        """
        competences = self.with_context(lang="en_US").search([])
        languages = competences.mapped("source_language_id") | competences.mapped("dest_language_id")
        return languages.mapped("name")


class TranslationUserSkill(models.Model):
    _name = "translation.user.skill"
    _description = "Translation user skill"

    translator_id = fields.Many2one("translation.user", required=True, index=True)
    competence_id = fields.Many2one("translation.competence", required=True, index=True)
    verified = fields.Boolean(help="The competence has been approved by a manager.")
