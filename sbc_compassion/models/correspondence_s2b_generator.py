##############################################################################
#
#    Copyright (C) 2016-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import Command, _, api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class CorrespondenceS2bGenerator(models.Model):
    """Generation of S2B Letters with text."""

    _name = "correspondence.s2b.generator"
    _description = "Correspondence Generator"
    _inherit = "correspondence.metadata"
    _order = "date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    state = fields.Selection(
        [("draft", "Draft"), ("preview", "Preview"), ("done", "Done")],
        default="draft",
        copy=False,
    )
    name = fields.Char(required=True)
    date = fields.Datetime(default=fields.Datetime.now, copy=False)
    image_ids = fields.Many2many(
        "ir.attachment", string="Attached images", readonly=False
    )
    template_id = fields.Many2one(required=True, domain=[("type", "=", "s2b")])
    background = fields.Image(related="template_id.template_image")
    selection_domain = fields.Char(
        default=[
            ("partner_id.category_id", "=", "Correspondance by Compassion"),
            ("state", "=", "active"),
            ("child_id", "!=", False),
        ]
    )
    sponsorship_ids = fields.Many2many(
        "recurring.contract", string="Sponsorships", required=True, readonly=False
    )
    language_id = fields.Many2one(
        "res.lang.compassion",
        "Language",
        default=lambda s: s.env.ref("advanced_translation.lang_compassion_english").id,
        required=True,
    )
    body = fields.Text(
        required=True,
        help="You can use the following tags to replace with values :\n\n"
        "* %child%: child name\n"
        "* %age%: child age (1, 2, 3, ...)\n"
        "* %firstname%: sponsor firstname\n"
        "* %lastname%: sponsor lastname\n",
    )
    letter_ids = fields.One2many(
        "correspondence", "generator_id", "Letters", copy=False
    )
    nb_letters = fields.Integer(compute="_compute_nb_letters")
    preview = fields.Html(compute="_compute_preview")
    month = fields.Selection("_get_months")

    def _compute_nb_letters(self):
        for generator in self:
            generator.nb_letters = len(generator.letter_ids)

    @api.model
    def _get_months(self):
        return self.env["compassion.child"]._get_months()

    @api.depends("letter_ids")
    def _compute_preview(self):
        for generator in self:
            generator.preview = generator.letter_ids[:1].preview

    @api.onchange("selection_domain")
    def onchange_domain(self):
        if self.selection_domain:
            self.sponsorship_ids = self.env["recurring.contract"].search(
                safe_eval(self.selection_domain)
            )

    @api.onchange("month")
    def onchange_month(self):
        if self.month:
            domain = safe_eval(self.selection_domain)
            month_select = ("child_id.birthday_month", "=", self.month)
            index = 0
            for search_filter in domain:
                if search_filter[0] == "child_id.birthday_month":
                    index = domain.index(search_filter)
            if index:
                domain[index] = month_select
            else:
                domain.append(month_select)
            self.selection_domain = str(domain)

    def action_preview(self):
        self.generate_letters_job(preview_mode=True)
        return self.write(
            {
                "state": "preview",
            }
        )

    def action_edit(self):
        return self.write({"state": "draft"})

    def generate_letters(self):
        """
        Launch S2B Creation job
        :return: True
        """
        self.with_delay().generate_letters_job()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Letters are being generated in background."),
                "type": "success",
            },
        }

    def generate_letters_job(self, preview_mode=False):
        """
        Create S2B Letters
        :return: True
        """
        letters = self.env["correspondence"]
        sponsorships = (
            self.sponsorship_ids[:1] if preview_mode else self.sponsorship_ids
        )
        for sponsorship in sponsorships:
            text = self._get_text(sponsorship)
            vals = {
                "sponsorship_id": sponsorship.id,
                "template_id": self.template_id.id,
                "direction": "Supporter To Beneficiary",
                "source": self.source,
                "original_language_id": self.language_id.id,
                "original_text": text,
                "state": "Draft" if preview_mode else "Received in the system",
            }
            if self.image_ids:
                vals["original_attachment_ids"] = [Command.clear()] + [
                    Command.create(
                        {
                            "datas": atchmt.datas,
                            "name": atchmt.name,
                            "res_model": letters._name,
                        }
                    )
                    for atchmt in self.image_ids
                ]
            letter = self.letter_ids.filtered(
                lambda c, _sp=sponsorship: c.sponsorship_id == _sp
            )
            if letter:
                letter.write(vals)
            else:
                letter = letters.create(vals)
            letters += letter
        letters.create_text_boxes()
        self.write({"letter_ids": [Command.set(letters.ids)]})
        if not preview_mode:
            self.write(
                {
                    "state": "done",
                    "date": fields.Datetime.now(),
                }
            )
        return True

    def open_letters(self):
        letters = self.letter_ids
        return {
            "name": letters._description,
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": letters._name,
            "context": self.env.context,
            "domain": [("id", "in", letters.ids)],
            "target": "current",
        }

    def unlink(self):
        self.mapped("letter_ids").filtered(lambda c: c.state == "Draft").unlink()
        return super().unlink()

    def _get_text(self, sponsorship):
        """Generates the text given a sponsorship."""
        self.ensure_one()
        sponsor = sponsorship.correspondent_id
        child = sponsorship.child_id
        keywords = {
            "%child%": child.preferred_name,
            "%age%": str(child.age),
            "%firstname%": sponsor.firstname or sponsor.name,
            "%lastname%": sponsor.firstname and sponsor.lastname or "",
        }
        text = self.body
        for keyword, replacement in list(keywords.items()):
            text = text.replace(keyword, replacement)
        return text
