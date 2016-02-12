# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
Define the class CheckboxReader that read a checkbox (the input image
should contains more or less only the box).
"""
import cv2
import numpy as np


class CheckboxReader:
    """
    Construct an object for reading an image of a checkbox.
    This class contains only one method for reading the brightness of
    the image in order to guess if the checkbox is checked or not.

    :param img: Image (array or str)
    :param float ratiomin: Ratio of black pixel required for being \
        considered as checked.
    """
    histogram = []

    ##########################################################################
    #                               INIT METHOD                              #
    ##########################################################################
    def __init__(self, img, ratiomin=0.01):
        self.min = ratiomin
        # read the image in greyscale
        if isinstance(img, str):
            self.img = cv2.imread(img, 0)
        else:
            self.img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        self.h, self.w = self.img.shape[:2]
        self.state = None
        self.corners = []
        # preprocessing of the image
        # (remove noise)
        self._preprocessing()
        # find all the corners
        # self._findCorner()
        self.histogram = cv2.calcHist([self.img], [0], None, [256], [0, 256])

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_pixels_count(self, min_brightness=0, max_brightness=256):
        """ Returns the number of pixels in the given brightness range.

        :param min_brightness: Minimum brightness value for pixels count
        :param max_brightness: Maximum brightness value for pixels count
        :returns: The number of pixels found.
        :rtype: float

        """
        if min_brightness < 0:
            min_brightness = 0
        if max_brightness > 256:
            max_brightness = 256
        count = 0
        if min_brightness < max_brightness:
            count = np.sum(self.histogram[min_brightness:max_brightness])
        return count

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _preprocessing(self):
        """Preprocessing done on the picture in order to facilitate the
        computation (denoising and threshold)
        """
        self.img = cv2.fastNlMeansDenoising(self.img, None, 10, 7, 21)
        self.img = cv2.adaptiveThreshold(self.img, 255,
                                         cv2.ADAPTIVE_THRESH_MEAN_C,
                                         cv2.THRESH_BINARY, 11, 2)
