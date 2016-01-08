# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Serpent Consulting Services Pvt. Ltd.
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, fields, _


class label_main(models.Model):
    _name = 'label.brand'
    _rec_name = 'brand_name'

    brand_name = fields.Char(_("Name"), size=64, select=1)
    label_config_ids = fields.One2many(
        'label.config', 'label_main_id', _('Label Config'))


class label_config(models.Model):

    _name = 'label.config'

    name = fields.Char(_("Name"), size=64, required=True, select=1)
    height = fields.Float(_("Height (in mm)"), required=True)
    width = fields.Float(_("Width (in mm)"), required=True)
    top_margin = fields.Float(_("Top Margin (in mm)"), default=0.0)
    bottom_margin = fields.Float(_("Bottom Margin  (in mm)"), default=0.0)
    left_margin = fields.Float(_("Left Margin (in mm)"), default=0.0)
    right_margin = fields.Float(_("Right Margin (in mm)"), default=0.0)
    label_main_id = fields.Many2one('label.brand', _('Label'))
    cell_spacing = fields.Float("Cell Spacing (in mm)", default=0.0)
