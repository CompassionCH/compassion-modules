# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
from io import BytesIO
from openerp import models, api, fields
from zipfile import ZipFile


class DownloadChildPictures(models.TransientModel):
    """
    Utility to select multiple letters and download the attachments
    as a zip archive.
    """

    _name = 'child.pictures.download.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    fname = fields.Char(default=lambda s: s.get_file_name())
    type = fields.Selection([
        ('headshot', 'Headshot'),
        ('fullshot', 'Fullshot')
    ], default='headshot')
    dpi = fields.Integer()
    height = fields.Integer()
    download_data = fields.Binary(readonly=True)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def get_file_name(self):
        return fields.Date.context_today(self) + '_child_pictures.zip'

    @api.multi
    def get_pictures(self):
        """ Create the zip archive from the selected letters. """
        partners = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])
        children = self.env['recurring.contract'].search([
            '|',
            ('correspondant_id', 'in', partners.ids),
            ('partner_id', 'in', partners.ids),
            ('type', 'in', ['S', 'SC']),
            ('state', '=', 'active')
        ]).mapped('child_id')
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_data:
            found = False
            custom = self.dpi or self.height
            for child in children:
                if not custom:
                    pic = getattr(child.pictures_ids[0], self.type)
                else:
                    pic = self.env['compassion.child.pictures']._get_picture(
                        child.id, child.code, False, self.type, self.dpi,
                        height=self.height)
                if pic:
                    fname = child.sponsor_id.ref + '_' + child.code + '.jpg'
                    zip_data.writestr(fname, base64.b64decode(pic))
                    found = True
        zip_buffer.seek(0)
        self.download_data = found and base64.b64encode(zip_buffer.read())
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'context': self.env.context,
            'target': 'new',
        }
