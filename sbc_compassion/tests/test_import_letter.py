# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import unittest

import logging
import cv2
import os
from tools import bluecornerfinder as bcf

logger = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(__file__)


class TestImportLetter(unittest.TestCase):
    """
    TODO doc
    """

    def setUp(self):
        self.test_document_normal = os.path.join(THIS_DIR,
                                                 'testdata/normal.png')

    def test_blue_corner_finder(self):
        """TODO doc"""
        img = cv2.imread(self.test_document_normal)
        self.assertIsNotNone(img)
        bluecorner = bcf.BlueCornerFinder(img)
        bluecorner_position = bluecorner.getIndices()
        self.assertEqual(bluecorner_position, [2438, 76])
