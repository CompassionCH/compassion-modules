from odoo import api, fields, models


class TranslationUser(models.Model):
    _name = "translation.user"
    _description = "Compassion Translator"

    user_id = fields.Many2one("res.users", "User", required=True, index=True)
    partner_id = fields.Many2one("res.partner", "Partner", related="user_id.partner_id")
    name = fields.Char(related="user_id.name")
    active = fields.Boolean(default=True)
    translator_since = fields.Datetime(default=fields.Datetime.now)
    translation_skills = fields.One2many("translation.user.skill", "translator_id", "Skills")
    translated_letter_ids = fields.One2many("correspondence", "new_translator_id", readonly=False)
    nb_translated_letters = fields.Integer("Total translations", compute="_compute_nb_translated_letters", store=True)
    nb_translated_letters_this_year = fields.Integer("Translations this year",
                                                     compute="_compute_nb_translated_letters_this_year", store=True)
    nb_translated_letters_last_year = fields.Integer("Translations last year",
                                                     compute="_compute_nb_translated_letters_last_year", store=True)
    search_source_lang = fields.Many2one("res.lang.compassion", domain=[("translatable", "=", True)],
                                         help="Utility field only used for the search view")
    search_dest_lang = fields.Many2one("res.lang.compassion", domain=[("translatable", "=", True)],
                                       help="Utility field only used for the search view")
    search_competence_id = fields.Many2one("translation.competence", help="Utility field only used for the search view")
    avatar = fields.Binary(related="partner_id.image_128")
    force_validation = fields.Boolean(
        help="If checked, all translations submitted by this user will require validation by a supervisor, regardless of their verified skills")

    _sql_constraints = [("unique_translator", "unique(user_id)", "This translator already exists.")]

    @api.depends("translated_letter_ids.translation_status")
    def _compute_nb_translated_letters(self):
        groups = self.env["correspondence"].read_group(
            [("new_translator_id", "in", self.ids), ("translation_status", "=", "done")],
            ["new_translator_id"], ["new_translator_id"]
        )
        mapped_data = {g["new_translator_id"][0]: g["new_translator_id_count"] for g in groups}
        for translator in self:
            translator.nb_translated_letters = mapped_data.get(translator.id, 0)

    @api.depends("translated_letter_ids.translation_status", "translated_letter_ids.translate_done")
    def _compute_nb_translated_letters_this_year(self):
        current_year = fields.Datetime.now().year
        groups = self.env["correspondence"].read_group(
            [("new_translator_id", "in", self.ids), ("translation_status", "=", "done"),
             ("translate_done", ">=", f"{current_year}-01-01 00:00:00"),
             ("translate_done", "<", f"{current_year + 1}-01-01 00:00:00")],
            ["new_translator_id"], ["new_translator_id"]
        )
        mapped_data = {g["new_translator_id"][0]: g["new_translator_id_count"] for g in groups}
        for translator in self:
            translator.nb_translated_letters_this_year = mapped_data.get(translator.id, 0)

    @api.depends("translated_letter_ids.translation_status", "translated_letter_ids.translate_done")
    def _compute_nb_translated_letters_last_year(self):
        last_year = fields.Datetime.now().year - 1
        groups = self.env["correspondence"].read_group(
            [("new_translator_id", "in", self.ids), ("translation_status", "=", "done"),
             ("translate_done", ">=", f"{last_year}-01-01 00:00:00"),
             ("translate_done", "<", f"{last_year + 1}-01-01 00:00:00")],
            ["new_translator_id"], ["new_translator_id"]
        )
        mapped_data = {g["new_translator_id"][0]: g["new_translator_id_count"] for g in groups}
        for translator in self:
            translator.nb_translated_letters_last_year = mapped_data.get(translator.id, 0)

    @api.model_create_multi
    def create(self, vals_list):
        """
        When creating a translator, put him the rights for using the platform.
        """
        records = super().create(vals_list)
        user_group = self.env.ref("sbc_translation.group_user")
        for translator in records:
            translator.user_id.write({"groups_id": [(4, user_group.id)], "translator_id": translator.id})
        return records

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

    def unlink(self):
        """
        Remove Translation Platform rights when removing translator.
        """
        user_group = self.env.ref("sbc_translation.group_user")
        self.mapped("user_id").write({"groups_id": [(3, user_group.id)]})
        return super().unlink()

    def open_translated_letters(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Translated letters",
            "res_model": "correspondence",
            "view_type": "form",
            "view_mode": "list,form",
            "context": {
                "search_default_new_translator_id": self.id,
                "form_view_ref": "sbc_translation.view_correspondence_form_translation",
                "list_view_ref": "sbc_translation.view_correspondence_translation_tree",
            },
        }

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

    def add_skill(self, competence_id):
        """
        Translation Platform API. Adds a new skill to the translator
        :param competence_id: translation.competence ID to add
        """
        return (
            self.env["translation.user.skill"]
            .create(
                [
                    {
                        "translator_id": translator.id,
                        "competence_id": competence_id,
                    }
                    for translator in self
                ]
            )
            .id
        )

    def unlink_skill(self, skill_dict):
        """
        Translation Platform API. Delete a skill to the translator
        :param skill_dict: Data about the skill to delete
        """
        for translation_usr in self:
            translation_usr.translation_skills.filtered(
                lambda s: s.competence_id.dest_language_id.name == skill_dict.get(
                    "target") and s.competence_id.source_language_id.name == skill_dict.get(
                    "source") and s.verified == skill_dict.get("verified")
            ).unlink()
        return True

    def _get_formatted_badges(self):
        self.ensure_one()
        self.env['translation.badge'].evaluate_badges(self.user_id)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        all_badges = self.env['translation.badge'].search([('is_active', '=', True)])
        unlocked_badge_ids = self.env['sbc.translation.user.badge'].search([('user_id', '=', self.user_id.id)]).mapped(
            'badge_id.id')
        corr_count = self.nb_translated_letters or 0
        streak_count = getattr(self, 'current_streak', 0)
        today = fields.Date.context_today(self)

        badges_by_category = {
            'volume': {'category': 'Volume', 'badges': []},
            'engagement': {'category': 'Engagement', 'badges': []},
            'campaign': {'category': 'Campaign', 'badges': []},
        }

        for badge in all_badges:
            is_unlocked = badge.id in unlocked_badge_ids
            progress = 0.0
            days_left = False
            days_until_start = False

            if is_unlocked:
                progress = 1.0
            else:
                if badge.condition_type == 'count' and badge.threshold:
                    progress = min(1.0, corr_count / badge.threshold)
                elif badge.condition_type == 'streak' and badge.threshold:
                    progress = min(1.0, streak_count / badge.threshold)
                elif badge.condition_type == 'campaign':
                    if badge.start_date and badge.start_date > today:
                        days_until_start = (badge.start_date - today).days
                    else:
                        domain = [('new_translator_id', '=', self.id), ('translation_status', '=', 'done')]
                        if badge.start_date:
                            domain.append(('translate_done', '>=', badge.start_date))
                        if badge.end_date:
                            domain.append(('translate_done', '<=', badge.end_date))

                        if badge.threshold:
                            campaign_count = self.env['correspondence'].search_count(domain)
                            progress = min(1.0, campaign_count / badge.threshold)

                        if badge.end_date:
                            if badge.end_date >= today:
                                days_left = (badge.end_date - today).days
                            else:
                                days_left = 0

            badge_dict = {
                'id': badge.id,
                'name': badge.name,
                'description': badge.description or '',
                'icon_url': f"{base_url}/web/image/theme.compassion.icons/{badge.icon_id.id}/icon" if badge.icon_id else f"{base_url}/web/static/img/smile.svg",                'is_unlocked': is_unlocked,
                'progress': progress,
                'threshold': badge.threshold or 0,
                'days_left': days_left,
                'days_until_start': days_until_start,
                'start_date': badge.start_date.strftime('%d/%m/%Y') if badge.start_date else False,
            }
            badges_by_category[badge.badge_type]['badges'].append(badge_dict)

        return [cat for cat in badges_by_category.values() if len(cat['badges']) > 0]

    def get_user_info(self):
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
            "skills": [{"source": skill.competence_id.source_language_id.name,
                        "target": skill.competence_id.dest_language_id.name, "verified": skill.verified} for skill in
                       self.translation_skills] or "None",
            "badges": self._get_formatted_badges(),
        }


class ResUsers(models.Model):
    _inherit = "res.users"
    translator_id = fields.Many2one("translation.user", "Translator")