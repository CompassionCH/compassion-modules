from odoo import api, fields, models


class TranslationBadge(models.Model):
    _name = 'translation.badge'
    _description = 'Translation Badge'

    name = fields.Char(string="Badge Name", required=True, translate=True)
    description = fields.Text(string="Description", translate=True)
    is_active = fields.Boolean(string="Active", default=True)

    icon_id = fields.Many2one('theme.compassion.icons', string="Badge Icon", required=True)

    badge_type = fields.Selection([
        ('volume', 'Volume (Total Letters)'),
        ('engagement', 'Engagement (Streaks)'),
        ('campaign', 'Time-bound Campaign')
    ], string="Category", required=True)

    condition_type = fields.Selection([
        ('count', 'Letter Count'),
        ('streak', 'Consecutive Months'),
        ('campaign', 'Campaign Participation')
    ], string="Condition Type", required=True)

    threshold = fields.Integer(string="Threshold (Target)", default=0)

    start_date = fields.Date(string="Campaign Start Date")
    end_date = fields.Date(string="Campaign End Date")

    user_badge_ids = fields.One2many(
        'sbc.translation.user.badge',
        'badge_id',
        string="Granted to",
        readonly=True
    )

    @api.model
    def evaluate_badges(self, user):
        translator = self.env['translation.user'].search([('user_id', '=', user.id)], limit=1)
        if not translator:
            return

        corr_count = translator.nb_translated_letters or 0
        streak_count = getattr(translator, 'current_streak', 0)

        unlocked_ids = self.env['sbc.translation.user.badge'].search([
            ('user_id', '=', user.id)
        ]).mapped('badge_id.id')

        available_badges = self.search([
            ('is_active', '=', True),
            ('id', 'not in', unlocked_ids)
        ])

        for badge in available_badges:
            should_unlock = False

            if badge.condition_type == 'count' and corr_count >= (badge.threshold or 0):
                should_unlock = True

            elif badge.condition_type == 'streak' and streak_count >= (badge.threshold or 0):
                should_unlock = True

            elif badge.condition_type == 'campaign':
                domain = [
                    ('new_translator_id', '=', translator.id),
                    ('translation_status', '=', 'done')
                ]
                if badge.start_date:
                    domain.append(('translate_done', '>=', badge.start_date))
                if badge.end_date:
                    domain.append(('translate_done', '<=', badge.end_date))

                campaign_count = self.env['correspondence'].search_count(domain)

                if campaign_count >= (badge.threshold or 1):
                    should_unlock = True

            if should_unlock:
                self.env['sbc.translation.user.badge'].create({
                    'user_id': user.id,
                    'badge_id': badge.id
                })


class TranslationUserBadge(models.Model):
    _name = 'sbc.translation.user.badge'
    _description = 'User Unlocked Badges'

    user_id = fields.Many2one('res.users', string="User", required=True)
    badge_id = fields.Many2one('translation.badge', string="Badge", required=True, ondelete='cascade')
    unlocked_date = fields.Datetime(string="Unlocked On", default=fields.Datetime.now)