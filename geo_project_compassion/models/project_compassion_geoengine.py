# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Flückiger
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api
from odoo.addons.base_geoengine import geo_model
from odoo.addons.base_geoengine.fields import GeoPoint


class CompassionProject(geo_model.GeoModel):
    """Add geo_point to compassion.project"""

    _inherit = "compassion.project"

    geo_point = GeoPoint(
        readonly=True, store=True)

    @api.multi
    def details_answer(self, vals):
        super(CompassionProject, self).details_answer(vals)
        self.compute_geopoint()
        return True

    @api.multi
    def compute_geopoint(self):
        """ Compute geopoints. """
        for project in self.filtered(lambda p: p.gps_latitude and
                                     p.gps_longitude):
            geo_point = GeoPoint.from_latlon(
                self.env.cr,
                project.gps_latitude,
                project.gps_longitude)
            project.write({'geo_point': geo_point.wkt})
        return True
