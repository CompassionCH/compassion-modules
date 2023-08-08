from odoo import api, models, fields


class TranslationUser(models.Model):
    _name = "translation.user"
    _description = "Compassion Translator"

    user_id = fields.Many2one("res.users", "User", required=True, index=True)
    partner_id = fields.Many2one("res.partner", "Partner", related="user_id.partner_id")
    name = fields.Char(related="user_id.name", store=True)
    active = fields.Boolean(default=True)
    translator_since = fields.Datetime(default=fields.Datetime.now)
    translation_skills = fields.One2many("translation.user.skill", "translator_id", "Skills")
    translated_letter_ids = fields.One2many(
        "correspondence", "new_translator_id", readonly=False
    )
    nb_translated_letters = fields.Integer(
        "Total translations", compute="_compute_nb_translated_letters", store=True
    )
    nb_translated_letters_this_year = fields.Integer(
        "Translations this year", compute="_compute_nb_translated_letters_this_year", store=True
    )
    nb_translated_letters_last_year = fields.Integer(
        "Translations last year", compute="_compute_nb_translated_letters_last_year", store=True
    )
    search_source_lang = fields.Many2one(
        "res.lang.compassion", domain=[("translatable", "=", True)],
        help="Utility field only used for the search view"
    )
    search_dest_lang = fields.Many2one(
        "res.lang.compassion", domain=[("translatable", "=", True)],
        help="Utility field only used for the search view"
    )
    search_competence_id = fields.Many2one(
        "translation.competence",
        help="Utility field only used for the search view"

    )
    avatar = fields.Binary(related="partner_id.image_small")

    _sql_constraints = [
        ("unique_translator", "unique(user_id)", "This translator already exists.")
    ]

    @api.multi
    @api.depends("translation_skills")
    def _compute_competences(self):
        for translator in self:
            translator.search_competence_ids = translator.mapped("translation_skills.competence_id")

    @api.multi
    @api.depends("translated_letter_ids")
    def _compute_nb_translated_letters(self):
        for translator in self:
            translator.nb_translated_letters = len(translator.translated_letter_ids)

    @api.multi
    @api.depends("translated_letter_ids")
    def _compute_nb_translated_letters_this_year(self):
        for translator in self:
            translator.nb_translated_letters_this_year = len(translator.translated_letter_ids.filtered(
                lambda it: it.translate_date.year == fields.Datetime.now().year))

    @api.multi
    @api.depends("translated_letter_ids")
    def _compute_nb_translated_letters_last_year(self):
        for translator in self:
            translator.nb_translated_letters_last_year = len(translator.translated_letter_ids.filtered(
                lambda it: it.translate_date.year == fields.Datetime.now().year - 1))

    @api.model
    def create(self, vals_list):
        """
        When creating a translator, put him the rights for using the platform.
        """
        records = super().create(vals_list)
        user_group = self.env.ref("sbc_translation.group_user")
        for translator in records:
            translator.user_id.write({
                "groups_id": [(4, user_group.id)],
                "translator_id": translator.id
            })
        return records

    @api.multi
    def write(self, vals):
        """
        When activating/deactivating a translator, update rights accordingly.
        """
        super().write(vals)
        if "active" in vals:
            user_group = self.env.ref("sbc_translation.group_user")
            action = 4 if vals["active"] else 3  # Add or remove group
            self.mapped("user_id").write({"groups_id": [(action, user_group.id)]})
        return True

    @api.multi
    def unlink(self):
        """
        Remove Translation Platform rights when removing translator.
        """
        user_group = self.env.ref("sbc_translation.group_user")
        self.mapped("user_id").write({"groups_id": [(3, user_group.id)]})
        return super().unlink()

    @api.multi
    def open_translated_letters(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Translated letters",
            "res_model": "correspondence",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": {"search_default_new_translator_id": self.id,
                        "form_view_ref": "sbc_translation.view_correspondence_form_translation",
                        "tree_view_ref": "sbc_translation.view_correspondence_translation_tree"},
        }

    @api.multi
    def list_users(self):
        """
        Translation Platform API call to fetch user info.
        """
        return [t.get_user_info() for t in self]

    @api.model
    def get_my_info(self):
        """
        Translation Platform API call to fetch user info.
        """
        translator = self.search([("user_id", "=", self.env.uid)])
        return translator.get_user_info()

    @api.multi
    def add_skill(self, competence_id):
        """
        Translation Platform API. Adds a new skill to the translator
        :param competence_id: translation.competence ID to add
        """
        return self.env["translation.user.skill"].create([{
            "translator_id": translator.id,
            "competence_id": competence_id,
        } for translator in self]).id

    @api.multi
    def unlink_skill(self, skill_dict):
        """
        Translation Platform API. Delete a skill to the translator
        :param skill_dict: Data about the skill to delete
        """
        for translation_usr in self:
            translation_usr.translation_skills.filtered(
                lambda s: s.competence_id.dest_language_id.name == skill_dict.get("target")
                and s.competence_id.source_language_id.name == skill_dict.get("source")
                and s.verified == skill_dict.get("verified")
            ).unlink()
        return True

    @api.multi
    def get_user_info(self):
        """
        Translation Platform API call to fetch user info.
        """
        self.ensure_one()
        user = self.user_id.sudo()
        partner = self.partner_id.sudo()
        group_user = self.env.ref("sbc_translation.group_user")
        group_admin = self.env.ref("sbc_translation.group_manager")
        role = "admin" if group_admin in user.groups_id else ("user" if group_user in user.groups_id else None)
        language = self.env["res.lang"].search([("code", "=", partner.lang)])
        return {
            "email": user.email or "None",
            "role": role,
            "name": partner.name or "None",
            "preferredName": partner.preferred_name,
            "age": partner.age or "None",
            "language": language.name or "None",
            "total": self.nb_translated_letters or "None",
            "year": self.nb_translated_letters_this_year or "None",
            "lastYear": self.nb_translated_letters_last_year or "None",
            "translatorId": self.id,
            "skills": [{
                "source": skill.competence_id.source_language_id.name,
                "target": skill.competence_id.dest_language_id.name,
                "verified": skill.verified
            } for skill in self.translation_skills] or "None",
        }


class ResUsers(models.Model):
    _inherit = "res.users"

    translator_id = fields.Many2one("translation.user", "Translator")
