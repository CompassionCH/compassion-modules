##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Flückiger
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class CompassionProject(models.Model):
    """Add geo_point to compassion.project"""

    _inherit = "compassion.project"
    _description = "Project Geolocation Point"

    geo_point = fields.GeoPoint(readonly=True, store=True)

    @api.multi
    def details_answer(self, vals):
        super().details_answer(vals)
        self.compute_geopoint()
        return True

    @api.multi
    def compute_geopoint(self):
        """ Compute geopoints. """
        for project in self.filtered(lambda p: p.gps_latitude and p.gps_longitude):
            geo_point = fields.GeoPoint.from_latlon(
                self.env.cr, project.gps_latitude, project.gps_longitude
            )
            project.write({"geo_point": geo_point.wkt})
        return True
