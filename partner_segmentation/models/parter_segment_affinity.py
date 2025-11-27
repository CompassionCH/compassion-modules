##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <jonathan.guerne@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from math import exp

from odoo import api, fields, models


class ResPartnerSegmentAffinity(models.Model):
    _name = "res.partner.segment.affinity"
    _description = "Partner segment affinity"
    _order = "partner_id desc, affinity desc"

    partner_id = fields.Many2one("res.partner", "Partner")
    segment_id = fields.Many2one("res.partner.segment", "Segment")

    affinity = fields.Float(
        help="affinity of the partner for this segment (in percentage)."
    )

    # matrix used to compute partner segmentation.
    # This was given by GMC (on a spreadsheet)
    answer_matrix_engine = [
        [
            0.997150993572249,
            -0.232528927794568,
            0.0413534389887897,
            0.211672855669691,
            0,
        ],
        [0.928637961891426, 1.07809459110299, 0.809374673519616, -0.353365425615717, 0],
        [
            -0.774287516323442,
            -0.353077503405008,
            -0.497598067137283,
            0.0290171579471129,
            0,
        ],
        [
            -0.828702041340668,
            -0.306263089055513,
            -0.25127881181768,
            0.137330144026763,
            0,
        ],
        [
            -0.384199925830168,
            0.443946593143302,
            -0.302689514147442,
            0.253657198644858,
            0,
        ],
        [3.54868078219565, 2.66016235435566, 2.28574280852505, 2.80261081232386, 0],
        [-4.59775894027253, -3.23370010451551, -3.66724594594727, -4.95710084189806, 0],
        [1.2299235065104, 0.906575903270276, 1.37232439891468, 3.6478947839409, 0],
        [-0.599463678308653, 0.714537607121647, 0.658485497623637, 3.01503974415245, 0],
        [5.2854633316847, 0.768600074282266, 2.05494988508751, 1.91537774009433, 0],
        [-0.586730821135251, 4.81639714039051, 1.07860150950627, -0.313814663844513, 0],
        [0.419406946212015, 3.52011283937107, -0.0904914401521656, 1.48613302522681, 0],
        [3.27441838834939, 2.31547036626548, 1.25261807258415, -0.0581689249944622, 0],
        [3.78506130192645, 5.24363911372303, 12.5977127472917, 4.52310726653152, 0],
        [1.28067931119687, 1.70830995385041, 2.51325849188955, 4.67121860393647, 0],
        [2.87067542083762, 3.65808756025025, 1.04515961202297, 0.103879143859532, 0],
        [-2.75036736789197, 1.48322694007813, -0.044493695141326, 0.922371536304811, 0],
        [3.25435356257396, 3.75237572538854, 1.75659766673739, 2.69909342147935, 0],
        [4.31350592706276, 1.45554124575379, 2.05265659545987, 3.26897563923801, 0],
        [-3.01212837180177, -1.59517466032187, 0.471983883796657, 1.95598757748298, 0],
        [-5.06030329552021, -3.60413990223956, -1.04375649300268, -4.47657656335253, 0],
        [-1.66377418504539, -5.32573310317821, -2.44074881077657, -4.50674881857412, 0],
        [-4.77259566923145, -3.15598279721272, -3.52425639320478, -6.67368137733622, 0],
        [0.880182155165077, -1.44671948132195, -2.4884760610343, -1.02472137413719, 0],
        [
            -0.0326103888365477,
            -2.99571602280864,
            -2.69104850676188,
            -1.75084871433893,
            0,
        ],
        [-0.783439038458744, 0.917536337079493, 0.86575431420832, 2.93637326365812, 0],
        [
            -0.566278267023883,
            -0.893538321476831,
            -3.80511027210482,
            -4.14668710742975,
            0,
        ],
        [2.86138579763347, 3.3103473304014, 12.7709974491643, 3.46942313908716, 0],
        [-0.404907139047755, -2.55346578831099, 13.4855455716769, 1.55681107187723, 0],
    ]

    answer_constant_engine = [
        -6.7614377947751,
        -8.85904330388748,
        -5.02071420157718,
        -6.23710433298537,
        0,
    ]

    @api.model_create_multi
    def create(self, vals):
        """
        Create a segment_affinity instance.
        Update partner reference on segment affinity
        :param vals: values used for model creation
        :return: id of the newly created model
        """
        segments = super().create(vals)
        # update partner.all_segment_affinity will trigger primary
        # and secondary segment computation
        for seg_affin in segments:
            seg_affin.partner_id.segments_affinity_ids = [(4, seg_affin.id)]
        return segments

    def unlink(self):
        """
        Unlink insance of the model. Update partner reference.
        :return: True
        """
        for seg_affin in self:
            seg_affin.partner_id.segments_affinity_ids = [(2, seg_affin.id)]
        return super().unlink()

    def segment_affinity_engine(self, answer_as_array, partner_id):
        """
        Adaptation of the segmentation engine used by GMC.
        Output the segmentation affinity for each of the 5 segment
        describe by GMC. Creating all the segment affinity instance
        will update the partner primary and secondary segment.

        :param answer_as_array: A well formatted list of user_input_line
                                quizz_mark (see partner_compassion.survey)
        :param partner_id: the id of the partner related to the answers
        :return: True (update partner all_segments_affinity)
        """

        # simplified explanation of the segmentation percentage computation
        # answer_array * matrix -> scaled matrix ( + constant)
        # -> segmentation score
        # -> segmentation percentage (= segmentation affinity)

        vals = {"partner_id": partner_id}

        # first each row of the engine matrix is multiplied by the nth entry
        # in the answer array.
        # This output a scaled matrix engine
        scaled_engine = [
            list(map(lambda x: answer_as_array[i] * x, self.answer_matrix_engine[i]))
            for i in range(len(self.answer_matrix_engine))
        ]

        # the score for each segment is computed by summing all the scaled
        # engine rows + the engine constant.
        # example:
        # scale engine     constant
        # [[1, 2, 3],
        #  [4, 5, 6],
        #  [7, 8, 9]]
        # =========
        # [12, 15, 18]  +  [ 1, 2, 3]  = [13, 17, 20] (= segment score)
        segment_score = [
            sum(x)
            for x in zip(
                [sum(x) for x in zip(*scaled_engine)], self.answer_constant_engine
            )
        ]

        # compute the percentage with the same approach as GMC's engine
        segment_percent = [exp(s) / sum(map(exp, segment_score)) for s in segment_score]

        # create a segment_affinity for each segment (with the partner)
        for index, percent_value in enumerate(segment_percent):
            seg = self.env["res.partner.segment"].search(
                [("segment_index", "=", index)]
            )
            vals["segment_id"] = seg.id
            vals["affinity"] = round(percent_value * 100, 3)
            self.create(vals)
        return True
