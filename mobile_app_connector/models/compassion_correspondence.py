# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api
from ..mappings.compassion_correspondence_mapping import \
    MobileCorrespondenceMapping


class CompassionCorrespondence(models.Model):
    _inherit = 'correspondence'

    @api.model
    def mobile_post_letter(self, json_data, **parameters):
        """
            Mobile app method:
            POST a letter between a child and a sponsor

            :param parameters: all request parameters
            :return: sample response
        """
        result = "Letter Submitted"

        mapping = MobileCorrespondenceMapping(self.env)

        dict = mapping.get_vals_from_connect(json_data)

        letter = self.env['correspondence'].create(dict)

        if letter:
            return result
