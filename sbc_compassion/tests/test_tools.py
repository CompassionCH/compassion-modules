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

from .. import tools
from openerp.tests import common

import logging
import cv2
import numpy as np
import os

logger = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(__file__)


class TestTools(common.TransactionCase):
    """
    Tests all utility functions used for importing letters.
    """

    def setUp(self):
        super(TestTools, self).setUp()
        self.test_document_normal = os.path.join(THIS_DIR,
                                                 'testdata/normal.png')
        self.test_document_noise = os.path.join(THIS_DIR, 'testdata/noise.png')
        self.test_document_white = os.path.join(THIS_DIR, 'testdata/white.png')
        template_obj = self.env['sponsorship.correspondence.template']
        self.templates = template_obj.search([('pattern_image', '!=', False)])

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
        template, pattern_center = self._pattern_recognition(
            self.test_document_normal)
        self.assertEqual(template.name, 'Test Template 1')
        np.testing.assert_allclose(pattern_center,
                                   np.array([1247.08, 3308.57]),
                                   atol=0.1)

    def test_pattern_recognition_no_pattern(self):
        """
        Pattern should not be found.
        """
        template, _ = self._pattern_recognition(self.test_document_noise)
        self.assertIsNone(template)
        template, _ = self._pattern_recognition(self.test_document_white)
        self.assertIsNone(template)

    def test_zxing_read_qr_code(self):
        """
        QR code should be read correctly.
        """
        qr_code = self._qr_decode(self.test_document_normal)
        self.assertIsNotNone(qr_code)
        self.assertEqual(qr_code.data, '1509540XXGU4920269\n')
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

    def _pattern_recognition(self, path):
        img = self._read_img(path)
        return tools.patternrecognition.find_template(img, self.templates)

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
