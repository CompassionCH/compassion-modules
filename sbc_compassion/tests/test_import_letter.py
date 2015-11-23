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

import tools

import logging
import cv2
import os

logger = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(__file__)


class TestImportLetter(unittest.TestCase):
    """
    TODO doc
    """

    def setUp(self):
        self.test_document_normal = os.path.join(THIS_DIR,
                                                 'testdata/normal.png')

    def test_blue_corner_finder_should_find(self):
        """Blue corner should be found at known coordinates."""
        img = self._read_img(self.test_document_normal)
        bluecorner = tools.bluecornerfinder.BlueCornerFinder(img)
        bluecorner_position = bluecorner.getIndices()
        self.assertEqual(bluecorner_position, [2438, 76])
        # TODO add tests with more documents

    def test_blue_corner_finder_should_not_find(self):
        """Blue corner should not be found."""

    def test_pattern_recognition(self):
        """TODO doc"""
        # TODO: need image files or base64 representation of patterns to test

    def test_zxing_read_qr_code(self):
        """QR code should be read correctly."""
        bar_code_tool = tools.zxing.BarCodeTool()
        path = os.path.abspath(self.test_document_normal)
        qr_code = bar_code_tool.decode(path,
                                       try_harder=True)
        self.assertEqual(qr_code.data, "1509540XXGU4920269\n")
        # TODO add tests with more documents

    def test_zxing_no_qr_code(self):
        """Should report error for document that does not contain QR code."""
        # TODO implement

    def _read_img(self, path):
        img = cv2.imread(path)
        self.assertIsNotNone(img)
        return img
