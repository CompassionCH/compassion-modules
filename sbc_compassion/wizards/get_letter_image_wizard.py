##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..tools.onramp_connector import SBCConnector


class GetLetterImageWizard(models.TransientModel):
    """Wizard for retrieving image of letter from Perceptive
    (Remote storage of U.S. servers)
    """

    _name = "letter.image.wizard"
    _description = "Wizard for image letter"

    image = fields.Selection(
        [("original", _("Original")), ("final", _("Final"))], required=True
    )
    format = fields.Selection(
        [("jpeg", "jpeg"), ("png", "png"), ("pdf", "pdf"), ("tif", "tif")],
        default="jpeg",
    )
    dpi = fields.Integer(default=96)
    page_number = fields.Integer(default=0)
    image_preview = fields.Image(readonly=True)
    image_download = fields.Binary(readonly=True)

    @api.constrains("dpi")
    def check_dpi(self):
        for wizard in self:
            if not 96 <= wizard.dpi <= 1200:
                raise ValidationError(_("Dpi value must be between 96 and 1200"))

    def get_image_letter(self, letter_id):
        """Allows to call get_image and specify a letter id."""
        return self.with_context(active_id=letter_id).get_image()

    def get_image(self):
        letter = self.env["correspondence"].browse(self.env.context.get("active_id"))
        onramp = SBCConnector(self.env)
        image_data = None
        params = {
            "format": self.format,
            "dpi": self.dpi,
            "pg": self.page_number,
        }
        if self.image == "original" and letter.original_letter_url:
            image_data = onramp.get_letter_image(letter.original_letter_url, params)
        elif self.image == "final" and letter.final_letter_url:
            image_data = onramp.get_letter_image(letter.final_letter_url, params)
        if image_data is None:
            raise UserError(_("Image requested was not found remotely."))
        self.write(
            {
                "image_preview": image_data if self.format != "pdf" else None,
                "image_download": image_data,
            }
        )
        return {
            "name": _("Retrieve letter image"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "letter.image.wizard",
            "res_id": self.id,
            "context": self.env.context,
            "target": "new",
        }
