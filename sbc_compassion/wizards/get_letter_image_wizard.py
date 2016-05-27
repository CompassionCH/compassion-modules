# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from ..tools.onramp_connector import OnrampConnector

from openerp import api, models, fields, _
from openerp.exceptions import Warning, ValidationError


class GetLetterImageWizard(models.TransientModel):
    """ Wizard for retrieving image of letter from Perceptive
        (Remote storage of U.S. servers)
    """
    _name = 'letter.image.wizard'

    image = fields.Selection([
        ('original', _('Original')),
        ('final', _('Final'))], required=True)
    format = fields.Selection([
        ('jpeg', 'jpeg'),
        ('png', 'png'),
        ('pdf', 'pdf'),
        ('tif', 'tif')], default='jpeg')
    dpi = fields.Integer(default=96)
    page_number = fields.Integer(default=0)
    image_preview = fields.Binary(readonly=True)
    image_download = fields.Binary(readonly=True)

    @api.constrains('dpi')
    def check_dpi(self):
        for wizard in self:
            if not 96 <= wizard.dpi <= 1200:
                raise ValidationError(
                    _("Dpi value must be between 96 and 1200"))

    @api.multi
    def get_image_letter(self, letter_id):
        """ Allows to call get_image and specify a letter id. """
        return self.with_context(active_id=letter_id).get_image()

    @api.multi
    def get_image(self):
        letter = self.env['correspondence'].browse(
            self.env.context.get('active_id'))
        onramp = OnrampConnector()
        image_data = None
        if self.image == 'original' and letter.original_letter_url:
            image_data = onramp.get_letter_image(
                letter.original_letter_url, self.format,
                self.page_number, self.dpi)
        elif self.image == 'final' and letter.final_letter_url:
            image_data = onramp.get_letter_image(
                letter.final_letter_url, self.format,
                self.page_number, self.dpi)
        if image_data is None:
            raise Warning(
                _('Image does not exist'),
                _("Image requested was not found remotely."))
        self.write({
            'image_preview': image_data,
            'image_download': image_data
        })
        return {
            'name': _('Retrieve letter image'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'letter.image.wizard',
            'res_id': self.id,
            'context': self.env.context,
            'target': 'new',
        }
