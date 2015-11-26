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

from .. import tools

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
        self.test_document_noise = os.path.join(THIS_DIR, 'testdata/noise.png')
        self.test_document_white = os.path.join(THIS_DIR, 'testdata/white.png')

    def test_blue_corner_finder_should_find(self):
        """
        Blue corner should be found at known coordinates.
        """
        img = self._read_img(self.test_document_normal)
        blue_corner_position = self._blue_corner_position(img)
        self.assertEqual(blue_corner_position, [2439, 77])
        # TODO add tests with more documents

    def test_blue_corner_finder_should_not_find(self):
        """
        Blue corner should not be found.
        """
        img = self._read_img(self.test_document_white)
        blue_corner_position = self._blue_corner_position(img)
        self.assertIsNone(blue_corner_position)

    def test_pattern_recognition(self):
        """
        Pattern should be recognized correctly.
        """
        # TODO: need image files or base64 representation of patterns to test

    def test_zxing_read_qr_code(self):
        """
        QR code should be read correctly.
        """
        qr_code = self._qr_decode(self.test_document_normal)
        self.assertIsNotNone(qr_code)
        self.assertEqual(qr_code.data, "1509540XXGU4920269\n")
        # TODO add tests with more documents

    def test_zxing_no_qr_code(self):
        """
        Should report error for document that does not contain QR code.
        """
        qr_code = self._qr_decode(self.test_document_noise)
        self.assertIsNone(qr_code)
        qr_code = self._qr_decode(self.test_document_white)
        self.assertIsNone(qr_code)

    def test_check_box_reader(self):
        """
        Checkboxes should be read correctly.
        """
        # Load image that has the French box checked
        img = self._read_img(self.test_document_normal)
        # French
        box = self._make_box(1130, 80)
        self.assertTrue(self._checked_state(img[box]))
        # Italian
        box = self._make_box(1130, 160)
        self.assertFalse(self._checked_state(img[box]))
        # German
        box = self._make_box(1130, 250)
        self.assertFalse(self._checked_state(img[box]))
        # Spanish
        box = self._make_box(1570, 80)
        self.assertFalse(self._checked_state(img[box]))
        # English
        box = self._make_box(1570, 160)
        self.assertFalse(self._checked_state(img[box]))
        # Other
        box = self._make_box(1570, 250)
        self.assertFalse(self._checked_state(img[box]))
        # TODO add tests with more documents

    def _read_img(self, path):
        img = cv2.imread(path)
        self.assertIsNotNone(img)
        return img

    @staticmethod
    def _qr_decode(path):
        path = os.path.abspath(path)
        bar_code_tool = tools.zxing.BarCodeTool()
        qr_code = bar_code_tool.decode(path, try_harder=True)
        return qr_code

    @staticmethod
    def _blue_corner_position(img):
        blue_corner_finder = tools.bluecornerfinder.BlueCornerFinder(img)
        return blue_corner_finder.getIndices()

    @staticmethod
    def _make_box(x, y, size=50):
        return [slice(y, y + size), slice(x, x + size)]

    @staticmethod
    def _checked_state(img):
        checkbox_reader = tools.checkboxreader.CheckboxReader(img)
        return checkbox_reader.getState()
