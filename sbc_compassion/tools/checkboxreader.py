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
import copy
from math import copysign


# Define some element for the morphological operator
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
        """
        # find the connection between the corners
        # and keep only the largest collection
        self.test = self._checkConnectivity()
        # if the collection does not have 4 corners
        # thus self.state stay at None
        if self.test and len(self.corners) == 4:
            # change the corners to make a square
            self._correctCorners()
            # find how large is the border
            i = self._findBorder()
            # find the state of the checkbox
            self._findState(i)
        """

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def getState(self, threshold=8):
        """
        Return the state of the checkbox
        :returns: The state of the checkbox (True->checked) and None if the \
        analysis has not been finished (usually means that the box is checked)
        :rtype: bool or None
        """
        # return self.state
        if len(self.corners) > threshold:
            return True
        else:
            return False

    def getLength(self):
        """
        Return the number of corners
        :returns: Number of corners
        :rtype: int
        """
        return len(self.corners)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _preprocessing(self):
        """
        Preprocessing done on the picture in order to facilitate the
        computation (denoising and threshold)
        """
        self.img = cv2.fastNlMeansDenoising(self.img, None, 10, 7, 21)
        self.img = cv2.adaptiveThreshold(self.img, 255,
                                         cv2.ADAPTIVE_THRESH_MEAN_C,
                                         cv2.THRESH_BINARY, 11, 2)

    def _correctCorners(self):
        """
        Change the corners in order to have a square.
        Keep the value of the second lowest, highest, leftmost and
        rightmost corners for the corners (in some case a point can be far away
        from the position required to create a corner)
        """
        raise Exception("Old Version: kept in case of improving the algorithm")
        # right
        right = 0
        temp = 0
        # find second smallest value
        for i in self.corners:
            if i[0] > right:
                if i[0] > temp:
                    right = temp
                    temp = i[0]
                else:
                    right = i[0]

        # left
        left = right
        temp = right
        # find second smallest value
        for i in self.corners:
            if i[0] < left:
                if i[0] < temp:
                    left = temp
                    temp = i[0]
                else:
                    left = i[0]

        # down
        down = 0
        temp = 0
        # find second smallest value
        for i in self.corners:
            if i[1] > down:
                if i[1] > temp:
                    down = temp
                    temp = i[1]
                else:
                    down = i[1]

        # up
        up = down
        temp = down
        # find second smallest value
        for i in self.corners:
            if i[1] < down:
                if i[1] < temp:
                    down = temp
                    temp = i[1]
                else:
                    down = i[1]

        self.corners = [(left, up), (right, up), (right, down), (left, down)]

    def _findState(self, border):
        """
        Count the number of pixel and black pixel inside the checkbox.
        Two threshold are applied to the ratio of black pixel obtained in
        order to check if something is written inside the checkbox

        :param int border: Thickness of the border (in pixel)
        """
        raise Exception("Old Version: kept in case of improving the algorithm")
        start = copy.deepcopy(self.corners[0])
        d = start[0] ** 2 + start[1] ** 2
        # find the upper-left (distance from the top-left
        # corner of the picture)
        for i in self.corners:
            d_tmp = i[0] ** 2 + i[1] ** 2
            if d_tmp < d:
                start = i
                d = d_tmp
        # find the lower-right corner (distance from the bottom-right
        # corner of the picture)
        end = copy.deepcopy(self.corners[0])
        d = (self.h - end[0]) ** 2 + (self.w - end[1]) ** 2
        for i in self.corners:
            d_tmp = (self.h - i[0]) ** 2 + (self.w - i[1]) ** 2
            if d_tmp < d:
                end = i
                d = d_tmp

        # count the number of (black) pixels
        black = 0
        pixel = 0
        for i in range(start[0] + border, end[0] - border):
            for j in range(start[1] + border, end[1] - border):
                pixel += 1
                if isBlack(self.img[i, j]):
                    black += 1

        if pixel == 0:
            ratio = 0
        else:
            ratio = float(black) / float(pixel)

        self.state = False
        # apply threshold
        if ratio > self.min:
            self.state = True

    def _findCorner(self):
        """
        Find the corners by using some morphological operator and then use
        the connectedComponents in order to isolate them.
        """
        self.img_corner = cv2.dilate(self.img, cross)
        self.img_corner = cv2.erode(self.img_corner, diamond)
        temp = cv2.dilate(self.img, xelem)
        temp = cv2.erode(temp, rect)
        self.img_corner = cv2.absdiff(temp, self.img_corner)
        ret, self.img_corner = cv2.threshold(255-self.img_corner, 190, 255, 0)
        temp = connectedComponents(self.img_corner, connectivity=8)
        N = np.max(temp)
        # loop over each region except background
        for n in range(1, N):
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

    def _checkPixel(self, i, j):
        """
        Check the pixel i,j in order to verify its neighbours and to know
        if it is considered as a corner.
        If it is a corner, write it in self.corners.
        :param int i: First coordinate
        :param int j: Second coordinate
        """
        raise Exception("Old Version: kept in case of improving the algorithm")
        # arrays used in order to simplify the reading
        down = [False, False]
        up = [False, False]
        right = [False, False]
        left = [False, False]
        # discard case where i,j is not black and discard case
        # too close to the border
        if (not isBlack(self.skel[i, j]) and i > 1 and i < self.h - 2 and
                j < self.w - 2 and j > 1):
            if not isBlack(self.skel[i + 1, j]):
                down[0] = True
            if not isBlack(self.skel[i + 2, j]):
                down[1] = True
            if not isBlack(self.skel[i - 1, j]):
                up[0] = True
            if not isBlack(self.skel[i - 2, j]):
                up[1] = True
            if not isBlack(self.skel[i, j + 1]):
                right[0] = True
            if not isBlack(self.skel[i, j + 2]):
                right[1] = True
            if not isBlack(self.skel[i, j - 1]):
                left[0] = True
            if not isBlack(self.skel[i, j - 2]):
                left[1] = True

        # check if the pixel is a corner
        if isCorner(down, up, right, left):
            self.corners.append((i, j))

    def _checkConnectivity(self):
        """
        Implementation of the connected-component labeling (Two-pass) in order
        to group the corners together.
        Delete in self.corners all the corners that are not inside the
        For the algorithm, see
        https://en.wikipedia.org/wiki/Connected-component_labeling
        """
        raise Exception("Old Version: kept in case of improving the algorithm")
        # apply a threshold in order to use the algorithm
        ret, sure_fg = cv2.threshold(self.img, 128, 255, 0)
        # create an image where each pixel value is the group id
        marker = connectedComponents(sure_fg)
        cluster = []
        # create the clusters
        while len(self.corners) != 0:
            ind = self.corners[0]
            ref = marker[ind]
            self.corners.pop(0)
            cluster.append([ind])
            tmp = copy.deepcopy(self.corners)
            for i in self.corners:
                if ref == marker[i]:
                    cluster[-1].append(i)
                    tmp.remove(i)
            self.corners = tmp

        # find the largest cluster
        self.corners = []
        for i in cluster:
            if len(i) > len(self.corners):
                self.corners = i

        a = 0
        # check that only one checkbox is on the image
        for i in cluster:
            if len(i) == len(self.corners):
                a += 1

        if a > 1:
            return False
        else:
            return True

    def _findBorder(self):
        """
        Find the thickness of the border.
        In order to simplify the code and speed it up a little bit, only
        the 8 points are checked (corners and middle point between two corners)
        :returns: Width of the border (in the direction of the inside)
        :rtype: int
        """
        raise Exception("Old Version: kept in case of improving the algorithm")
        width = np.inf
        # find the width of the checkbox
        for i in self.corners:
            for j in self.corners:
                if i != j:
                    dist_max = np.abs(i[0] - j[0])
                    dist_max = np.maximum(dist_max, np.abs(i[1] - j[1]))
                    if dist_max < width:
                        width = dist_max
        i = 1
        border = True
        # increase the size of the border until reaching the good one
        while i < width / 2 and border:
            border = self._isStillBorder(i)
            i += 1
        i = i - 1
        return i

    def _isStillBorder(self, distance):
        """
        Check the 8 points (of _findBorder)
        :param int distance: Distance from the border to try
        :returns: If it is still inside the border
        :rtype: bool
        """
        raise Exception("Old Version: kept in case of improving the algorithm")
        for i in self.corners:
            k = 0
            d = [-1, -1, -1]
            neigh = []
            # find the corner the most far away
            for j in self.corners:
                if j != i:
                    neigh.append(j)
                    d[k] = (j[0] - i[0]) ** 2 + (j[1] - i[1]) ** 2
                    k += 1
            d = d.index(max(d))
            k = 0
            # find direction other corners
            direct = [0, 0]
            if abs(neigh[d][0]) > 1:
                direct[0] = copysign(1, neigh[d][0]) * distance
            if abs(neigh[d][1]) > 1:
                direct[1] = copysign(1, neigh[d][1]) * distance

            # check corner
            ind = [i[0] + direct[0], i[1] + direct[1]]
            if not isBlack(self.img[tuple(ind)]):
                return False
            # check pixel between corners
            for j in neigh:
                if d != k:
                    ind = [(i[0] + j[0]) / 2, (i[0] + j[0]) / 2]
                    mdir = [0, 0]
                    if abs(j[0]) > 1:
                        mdir[1] = direct[1]
                    if abs(j[1]) > 1:
                        mdir[0] = direct[0]

                    ind = [ind[0] + mdir[0], ind[1] + mdir[1]]
                    if not isBlack(self.img[tuple(ind)]):
                        return False
                k += 1


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################
def isBlack(pixel, threshold=127):
    """
    Check if a pixel is black
    :param int pixel: Pixel value
    :param int threshold: Threshold value
    :returns: True if the pixel is black
    :rtype: bool
    """
    if pixel > threshold:
        return False
    else:
        return True


def isCorner(down, up, right, left):
    """
    Check if a pixel is a corner.
    :param [bool,bool] down: Pixels below
    :param [bool,bool] up: Pixels above
    :param [bool,bool] left: Pixels on the left
    :param [bool,bool] right: Pixels on the right
    :returns: True if it is a corner
    :rtype: bool
    """

    raise Exception("Old Version: kept in case of improving the algorithm")
    if (isDirectionOK(right, left) and
            isDirectionOK(down, up)):
        return True
    else:
        return False


def isDirectionOK(a, b):
    """
    Check if the pixels are TT-FF or FF-TT (T=True, F=False).
    :param [bool,bool] a: Pixel on one side
    :param [bool,bool] b: Pixel on the other side
    :returns: True if TT-FF or FF-TT
    :rtype: bool
    """
    raise Exception("Old Version: kept in case of improving the algorithm")
    # case where a True is on each side
    if (a[0] or a[1]) and (b[0] or b[1]):
        return False
    # case where a False is on each side
    elif (not a[0] or not a[1]) and (not b[0] or not b[1]):
        return False
    else:
        return True


def connectedComponents(img, connectivity=8):
    """
    Create the image composed of conectivity ids
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
        raise Exception('{}-connectivity does not exist'.format(connectivity))

    h, w = img.shape[:2]
    # square mask
    mh = (con.shape[0] - 1) / 2
    mw = mh
    ret = np.zeros((h, w), np.int8)
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
