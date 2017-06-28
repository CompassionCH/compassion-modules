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
from odoo import models, fields, _


class LabelBrand(models.Model):
    _name = 'label.brand'
    _rec_name = 'brand_name'
    _description = 'Label Brand'

    brand_name = fields.Char(_("Name"), size=64, index=1)
    label_config_ids = fields.One2many(
        'label.config', 'label_main_id', _('Label Config'))


class LabelConfig(models.Model):
    _name = 'label.config'
    _description = 'Label Config'

    name = fields.Char("Name", size=64, required=True, index=1)
    height = fields.Float("Height (in mm)", required=True)
    width = fields.Float("Width (in mm)", required=True)
    top_margin = fields.Float("Top Margin (in mm)", default=0.0)
    bottom_margin = fields.Float("Bottom Margin  (in mm)", default=0.0)
    left_margin = fields.Float("Left Margin (in mm)", default=0.0)
    right_margin = fields.Float("Right Margin (in mm)", default=0.0)
    label_main_id = fields.Many2one('label.brand', 'Label')
    cell_spacing = fields.Float("Cell Spacing (in mm)", default=0.0)
