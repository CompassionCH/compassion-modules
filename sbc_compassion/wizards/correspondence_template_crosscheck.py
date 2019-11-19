##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields
import base64
import tempfile
import logging
from ..tools import patternrecognition as pr
from os import remove

_logger = logging.getLogger(__name__)
try:
    import cv2
except ImportError:
    _logger.warning('Please install cv2 to use SBC module')


class CorrespondenceCrosscheck(models.TransientModel):
    """
    Model computing the crosscheck between all the patterns in
    correspondence.template and showing them in a wizard.
    """

    _name = 'correspondence.template.crosscheck'
    _description = 'Crosscheck of correspondence template'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    file_ = fields.Many2many('crosscheck.image', readonly=True,
                             default=lambda self: self._default_file_())

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _default_file_(self):
        """
        Compute the default value for the field file_
        This method runs a pattern recognition between all the chosen patterns
        or, if only one is selected, between this one and all the others.
        """
        # take active ids
        ret = []
        active_ids = self.env.context['active_ids']
        # avoid templates without pattern
        tpl = self.env['correspondence.template'].search(
            [('id', 'in', active_ids), ('pattern_image', '!=', None)])
        # loop over all the active templates
        for t1 in tpl:
            # if only one element check with all the other ones
            if len(tpl) == 1:
                tpl2 = self.env[
                    'correspondence.template'].search([
                        ('pattern_image', '!=', None)])
            # if more, do only the ones not done yet
            else:
                tpl2 = self.env[
                    'correspondence.template'].search([
                        ('id', '>=', t1.id), ('pattern_image', '!=', None)])

            # create the first pattern image
            with tempfile.NamedTemporaryFile() as template_file:
                template_file.write(base64.b64decode(
                    t1.pattern_image))
                template_file.flush()
                # Find the pattern inside the template image
                img = cv2.imread(template_file.name)

            # loop over second templates
            for t2 in tpl2:
                # create the second pattern image
                with tempfile.NamedTemporaryFile() as template_file:
                    template_file.write(base64.b64decode(
                        t2.pattern_image))
                    template_file.flush()
                    # Find the pattern inside the template image
                    img2 = cv2.imread(template_file.name)

                res = pr.patternRecognition(img, img2, full_result=True)
                if res is None:
                    kp1, kp2, good = None, None, None
                else:
                    kp1, kp2, good = res

                img3 = cv2.drawMatchesKnn(img, kp1, img2,
                                          kp2, good, None, flags=2)
                name = t1.name + '-' + t2.name + '.png'
                cv2.imwrite(name, img3)
                with open(name, 'r') as f:
                    img3 = f.read()
                    remove(name)
                image_id = self.env['crosscheck.image'].create({
                    'name': name,
                    'image': base64.b64encode(img3),
                })
                ret.append(image_id.id)
        return [(6, 0, ret)]


class CrosscheckImage(models.TransientModel):
    """
    Model for a line in the CorrespondenceCrosscheck class
    """
    _name = "crosscheck.image"
    _description = 'Crosscheck image'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    image = fields.Binary(required=True)
    name = fields.Char(required=True)
