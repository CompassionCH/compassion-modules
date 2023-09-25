##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################

    primary_segment_id = fields.Many2one(
        "res.partner.segment",
        string="Primary segmentation category",
        compute="_compute_prim_sec_segments",
        store=True,
    )
    secondary_segment_id = fields.Many2one(
        "res.partner.segment",
        string="Secondary segmentation category",
        compute="_compute_prim_sec_segments",
        store=True,
    )
    primary_segment_name = fields.Char(related="primary_segment_id.name")
    has_segment = fields.Boolean(compute="_compute_has_segment")

    segments_affinity_ids = fields.Many2many(
        "res.partner.segment.affinity", string="Affinity for each segment"
    )

    # Surveys
    survey_input_lines = fields.One2many(
        comodel_name="survey.user_input.line",
        inverse_name="partner_id",
        string="Surveys answers",
        readonly=False,
    )
    survey_inputs = fields.One2many(
        comodel_name="survey.user_input",
        inverse_name="partner_id",
        string="Surveys",
        readonly=False,
    )
    survey_input_count = fields.Integer(
        string="Survey number", compute="_compute_survey_input_count", store=True
    )

    @api.depends("segments_affinity_ids", "segments_affinity_ids.affinity")
    def _compute_prim_sec_segments(self):
        for partner in self:
            partner.primary_segment_id = partner.segments_affinity_ids[:1].segment_id
            partner.secondary_segment_id = partner.segments_affinity_ids[1:2].segment_id

    def _compute_has_segment(self):
        for partner in self:
            partner.has_segment = bool(partner.primary_segment_id)

    @api.depends("survey_inputs")
    def _compute_survey_input_count(self):
        for survey in self:
            survey.survey_input_count = len(survey.survey_inputs)
