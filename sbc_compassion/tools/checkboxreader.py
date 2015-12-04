# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>
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


class CheckboxConstant:
    """ Define some element for the morphological operator
    """
    rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    diamond = np.ones((5, 5), np.uint8)
    diamond[0, 0] = 0
    diamond[0, 1] = 0
    diamond[1, 0] = 0
    diamond[4, 4] = 0
    diamond[3, 4] = 0
    diamond[4, 3] = 0
    diamond[4, 0] = 0
    diamond[4, 1] = 0
    diamond[3, 0] = 0
    diamond[0, 4] = 0
    diamond[0, 3] = 0
    diamond[1, 4] = 0

    xelem = np.zeros((5, 5), np.uint8)
    for i in range(5):
        xelem[i, i] = 1
        xelem[4-i, i] = 1


class CheckboxReader:
    """
    Read the state of a checkbox contained in an image composed mainly by
    the checkbox.
    The algorithm consists in finding the 4 corners and counting the black
    pixels inside the box.
    In order to find the corners, the image scanned and for each pixel a check
    is made in order to see if there is 2 black pixels on each direction
    (if only two directions have 2 black pixels and the others are white, a
    corner is assumed).
    With this method, if the image contains an other partial square, it will
    not be able to check the state of the first one.
    Therefore a connected-component labeling is made in order to associate
    the corners together (only the largest collection of corner is kept).
    The last step consists in finding how large is the square of the box.
    It is computed by using 8 different points (corners and middle points
    [between corners]) for a decreasing size of the box.
    The border is assumed to be finish when at least one pixel is white.

    The function getState is used in order to obtain the state of the checkbox.
    Three different return values exist:
    - True means that the checkbox is checked
    - False means that the checkbox is empty
    - None means that a problem occured at a certain point (usually because
    the checkbox is checked and the corner are not found).

    :param img: Image (array or str)
    :param float ratiomin: Ratio of black pixel required for being \
        considered as checked.
    """

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
        self._findCorner()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def getState(self, threshold=8):
        """ Return the state of the checkbox

        :param threshold: Threshold for the number of corners find
        :returns: The state of the checkbox (True->checked) and None if the \
        analysis has not been finished (usually means that the box is checked)
        :rtype: bool or None

        """
        return (len(self.corners) > threshold)

    def getLength(self):
        """ Return the number of corners

        :returns: Number of corners
        :rtype: int

        """
        return len(self.corners)

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

    def _findCorner(self):
        """
        Find the corners by using some morphological operator and then use
        the connectedComponents in order to isolate them.
        """
        # a few morphological operator in order to find corners
        self.img_corner = cv2.dilate(self.img, CheckboxConstant.cross)
        self.img_corner = cv2.erode(self.img_corner, CheckboxConstant.diamond)
        temp = cv2.dilate(self.img, CheckboxConstant.xelem)
        temp = cv2.erode(temp, CheckboxConstant.rect)
        self.img_corner = cv2.absdiff(temp, self.img_corner)

        # threshold
        ret, self.img_corner = cv2.threshold(255-self.img_corner, 190, 255, 0)
        # find the different area
        temp = connectedComponents(self.img_corner, connectivity=8)
        N = np.max(temp)
        # loop over each region except background
        for n in range(1, N):
            # average position of the corner
            index = np.array((0, 0), int)
            count = 0
            for i in range(temp.shape[0]):
                for j in range(temp.shape[1]):
                    if temp[i, j] == n:
                        index += (i, j)
                        count += 1
            if count != 0:
                index /= count
                self.corners.append((index[0], index[1]))


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################
def connectedComponents(img, connectivity=8):
    """ Create the image composed of conectivity ids

    :param array img: Image to analyze
    :param int connectivity: Type of connectivity (4 or 8)
    :returns: Image of ids
    :rtype: array

    """
    con = np.zeros((3, 3), bool)
    if connectivity == 8:
        # 111
        # 110
        # 000
        con[0, :] = 1
        con[1, :2] = 1
    elif connectivity == 4:
        # 010
        # 110
        # 000
        con[0, 1] = 1
        con[1, :2] = 1
    else:
        raise Exception('{}-connectivity is not implemented'.format(
            connectivity))

    h, w = img.shape[:2]
    # square mask
    mh = (con.shape[0] - 1) / 2
    mw = mh
    ret = np.zeros((h, w), np.int16)
    col = 1
    E = []
    # first scan the image and gives temporary ids
    # loop over the first image
    for i in range(h):
        for j in range(w):
            # if not backgroud
            if img[i, j] == 0:
                col_tmp = -1
                # loop over the connectivity mask
                for x in range(con.shape[0]):
                    for y in range(con.shape[1]):
                        # if we stay inside the image
                        if (i + x - mh < h and i + x - mh >= 0 and
                                j - mw + y < w and j - mw + y >= 0):
                            # if not background and inside the mask
                            if ret[i + x - mh, j - mw + y] != 0 and con[x, y]:
                                a = ret[i + x - mh, j - mw + y]
                                # if pixel already threated
                                if col_tmp != -1:
                                    # add to the equivalence list
                                    if a not in E[col_tmp - 1]:
                                        E[col_tmp - 1].append(a)
                                    if col_tmp not in E[a - 1]:
                                        E[a - 1].append(col_tmp)
                                    # keep lowest index
                                    if a < col_tmp:
                                        col_tmp = a
                                else:
                                    col_tmp = a
                # if no neighbours, create new id
                if col_tmp == -1:
                    ret[i, j] = col
                    E.append([col])
                    col += 1
                else:
                    ret[i, j] = col_tmp

    # create an equivalence table from the list
    eq_table = col * np.ones(col - 1, int)
    for i in range(col - 1):
        eq_table[i] = min(E[i])

    # gives the final ids (use the equivalence in order to have the smallest
    # amount of ids)
    for i in range(h):
        for j in range(w):
            if ret[i, j] != 0:
                ret[i, j] = eq_table[ret[i, j] - 1]
    return ret
