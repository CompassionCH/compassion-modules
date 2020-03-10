##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
Define the class CheckboxReader that read a checkbox (the input image
should contains more or less only the box).
"""
import logging

_logger = logging.getLogger(__name__)
try:
    import cv2
    from cv2 import filter2D
    from numpy import logical_and as and2
    from numpy import logical_or as or2
    import numpy as np
except ImportError:
    _logger.warning("Please install cv2 and numpy on your system to use SBC " "module")


class CheckboxReader:
    """
    Construct an object for reading an image of a checkbox.
    :param img: Image (array or str)

    """

    histogram = []

    ##########################################################################
    #                               INIT METHOD                              #
    ##########################################################################
    def __init__(self, img, threshold=212.5):
        # read the image in greyscale
        if isinstance(img, str):
            self.img = cv2.imread(img, 0)
        else:
            self.img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            self.decision_threshold = threshold
            self.score = None

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def compute_boxscore(self, boxsize=17):
        """
        Basically, if we count the number of dark pixels on the image should
        give us a clue if the box is checked or not. But sometimes the
        sponsor write around the box, which increase the number of dark
        pixels. This is why we start by cropping precisely around the box.
        Then we compute the Canny Edge and Canny Curve and merge them.
        :param boxsize:
        :return:
        """
        # Negative image
        img = 255 - np.copy(self.img)

        # detect the box
        left, right, top, bottom = self._box_coordinates(img, squarsize=boxsize)

        # Detect the line borders withe Canny Edge
        canny1 = cv2.Canny(img, 20, 20)
        # Detect line itself with Canny Curve
        canny2 = self._canny_curve_detector(img, low_thresh=20, high_thresh=20)
        # Merge the two Canny by keeping the maximum for each pixels
        canny = cv2.max(canny1, canny2)
        # Crop around the box
        canny = canny[top:bottom, left:right]
        self.canny = canny
        # Comupte the integral of the image.
        count = cv2.sumElems(canny)[0] // 255
        return count

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    def _findmax(self, x):
        m = max(x)
        ind = [i for i, val in enumerate(x) if val == m]
        return m, ind

    def _box_coordinates(self, img, squarsize=17, linewidth=3):
        """
        Find the position of the checkbox, assuming it is not more rotated
        than a few degrees
        :param img:
        :param squarsize: The size of the checkbox in pixel. It is the
        minimum number of pixel needed to draw one border of the square.
        In 100 dpi a square is 17 pixel wide
        :param linewidth: This is the width of a border of the checkbox.
        3 is good for 100 dpi as it is a little bit more that the actual
        linewidth, which will make the algo a bit more robust to rotation
        :return left, right, top, bottom: Coordinates of a square
        containing the checkbox. The square is 6 pixels wider than the
        checkbox
        """
        sum0 = np.sum(img, axis=0)
        sum1 = np.sum(img, axis=1)
        a = [1] * linewidth
        b = [0] * (squarsize - 2 - (linewidth - 1))
        kernel = a + b + a

        sum0 = np.convolve(sum0, kernel, "valid")
        sum1 = np.convolve(sum1, kernel, "valid")

        left = self._findmax(sum0)[1][0]
        top = self._findmax(sum1)[1][0]
        right = left + squarsize + (linewidth + 1) // 2
        bottom = top + squarsize + (linewidth + 1) // 2

        # add margin
        margin = 2
        left -= margin
        top -= margin
        right += margin
        bottom += margin

        # anticipate the out of bound problem
        left = max(0, left)
        top = max(0, top)
        width, height = img.shape
        right = min(width, right)
        bottom = min(height, bottom)
        return left, right, top, bottom

    def _canny_curve_detector(self, img, low_thresh=35, high_thresh=60):
        # We start by blurring the image a little bit
        img = cv2.GaussianBlur(np.copy(img), (3, 3), 1)

        kernel1 = np.array([[0, 0, 0], [-1, 1, 0], [0, 0, 0]])
        kernel2 = np.array([[0, 0, 0], [0, 1, -1], [0, 0, 0]])
        localmax_x = filter2D(img, cv2.PARAM_INT, kernel1) > 0
        localmax_x = and2(localmax_x, filter2D(img, cv2.PARAM_INT, kernel2) > 0)

        kernel1 = kernel1.transpose()
        kernel2 = kernel2.transpose()
        localmax_y = filter2D(img, cv2.PARAM_INT, kernel1) > 0
        localmax_y = and2(localmax_y, filter2D(img, cv2.PARAM_INT, kernel2) > 0)

        localmax = or2(localmax_x, localmax_y)

        # We drop local maxima which are under an intensity threshold
        strong = and2(localmax, (high_thresh < img))

        # We finally take back local max which are not so weak, and which are
        # just next to a string local maxima
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        strong.dtype = "uint8"
        touch = cv2.morphologyEx(strong, cv2.MORPH_DILATE, kernel)
        touch.dtype = "bool"

        edge = and2(touch, (low_thresh < img))
        edge = and2(edge, localmax)
        edge.dtype = "uint8"
        return edge * 255
