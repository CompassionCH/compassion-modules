# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api
from ..mappings.compassion_child_pictures_mapping \
    import MobileChildPicturesMapping


logger = logging.getLogger(__name__)


class CompassionChildPictures(models.Model):
    """ A sponsored child """
    _inherit = 'compassion.child.pictures'

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        mapping = MobileChildPicturesMapping(self.env)
        # wrapper = 'Images' if multi else 'Images'
        if len(self) == 1:
            data = mapping.get_connect_data(self)
        else:
            data = []
            for child in self:
                data.append(mapping.get_connect_data(child))
        return data
