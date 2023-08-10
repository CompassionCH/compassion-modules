from odoo import api, models, fields


class TranslationCompetence(models.Model):
    _name = "translation.competence"
    _description = "Compassion Translation Competence"
    _order = "number_current_letters desc"

    source_language_id = fields.Many2one(
        "res.lang.compassion", "Source language", domain=[("translatable", "=", True)], required=True, index=True
    )
    dest_language_id = fields.Many2one(
        "res.lang.compassion", "Destination language", domain=[("translatable", "=", True)], required=True, index=True
    )
    fallback_competence_id = fields.Many2one(
        "translation.competence", "Fallback competence",
        help="Letters will move to this pool if they sit for too long waiting to be translated."
    )
    name = fields.Char(compute="_compute_name", store=True)  # We need to store it to filter on it
    all_letter_ids = fields.One2many(
        "correspondence", "translation_competence_id", "All letters"
    )
    current_letter_ids = fields.One2many(
        "correspondence", string="Current letters", compute="_compute_current_letters")
    number_current_letters = fields.Integer(compute="_compute_current_letters", store=True)
    skill_ids = fields.One2many("translation.user.skill", "competence_id", "Translator skills")
    number_translators = fields.Integer(compute="_compute_number_translators", store=True)
    number_active_translators = fields.Integer(compute="_compute_number_translators")

    _sql_constraints = [
        ("unique_competence", "unique(source_language_id,dest_language_id)", "This competence already exists.")
    ]

    @api.depends("dest_language_id", "source_language_id")
    def _compute_name(self):
        for competence in self:
            competence.name = competence.source_language_id.name + " -> " + competence.dest_language_id.name

    @api.depends("all_letter_ids")
    def _compute_current_letters(self):
        for competence in self:
            current_letters = self.env["correspondence"].search([
                ("state", "=", "Global Partner translation queue"),
                ("translation_competence_id", "=", competence.id),
                ("translation_competence_id", "!=", False)
            ])
            competence.current_letter_ids = current_letters
            competence.number_current_letters = len(current_letters)

    @api.depends("skill_ids", "skill_ids.translator_id.active")
    def _compute_number_translators(self):
        for competence in self:
            competence.number_translators = self.env["translation.user"].search_count([
                ("translation_skills.competence_id", "=", competence.id),
            ])
            competence.number_active_translators = self.env["translation.user"].search_count([
                ("translation_skills.competence_id", "=", competence.id),
                ("nb_translated_letters_this_year", ">", 0)])

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

    translator_id = fields.Many2one("translation.user", required=True, index=True, ondelete="cascade")
    competence_id = fields.Many2one("translation.competence", required=True, index=True, ondelete="cascade")
    verified = fields.Boolean(help="The competence has been approved by a manager.")
