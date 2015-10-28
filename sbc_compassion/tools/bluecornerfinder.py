"""
Define the class BlueCornerFinder that try to find the upper-right corner of
the blue square in all the compassion documents.
"""
import cv2
import numpy as np
from collections import deque
from math import floor


class BlueCornerFinder:

    """
    Class used in order to compute the position of the upper-right corner
    of the blue square (is used in order to find the scaling of a scan).
    This class uses a method that start from the corner and draws a serie of
    circle until reaching the corner (check if it is a cluster [more than just
    two in the eight closest pixels]).


    :param str img: Name of the file
    :param list[] box: relative position where to cut the image
    :param int threshold: Threshold applied for the definition of blue
    """

    def __init__(self, img, box=[0.66, 0.25], threshold=90):
        """
        Read and cut the image to the requested value.
        """
        self.threshold = threshold
        self.img = cv2.imread(img)
        # get size of the image
        h, w = self.img.shape[:2]
        # save the original size
        self.h_ori = h
        self.w_ori = w
        self.xmin = int(round(box[0] * w))
        ymax = round(box[1] * h)
        self.img = self.img[:ymax, self.xmin:]
        h, w = self.img.shape[:2]
        self.h = h
        self.w = w
        self._readBlueCorner()
        del self.img

    def _readBlueCorner(self):
        """
        Is called at the initialization of an instance.
        Compute the coordinates of the blue square.
        In order to get them afterward, use getIndices.

        :returns: Indices of the square
        :rtype: list
        """
        # distance in integer (rounded down)
        self.dist = np.zeros((self.h, self.w), dtype=int)
        # is used in order to know when to stop the loop
        # and knowing if a blue pixel has been found in
        # the image
        self.found = False
        # distance to the corner (rounded down)
        self.n = -1
        # the scan stop if we reach an other corner
        while not self.found and self.n < self.w:
            self.n += 1
            # queue containing the next cells
            self.todo = deque([[0, self.w - self.n - 1]])
            # scan all the pixel until the end of the queue
            while len(self.todo) != 0:
                # get and remove first job
                ind = self.todo[0]
                self.todo.popleft()
                # set distance in the map
                self.dist[ind] = self.n
                # scan the closest neighborhood and add
                # them (if required) in the todo queue
                self._scan(ind)
                # check if a good blue pixel is found
                if checkColor(self.img[tuple(ind)], self.threshold):
                    if self._checkNext(ind):
                        self.found = True

        # case where a blue pixel has been found
        if self.found:
            self._findmin()
        else:
            self.ind = None

        return self.ind

    def getIndices(self):
        """
        Returns the indices of the blue square
        :returns: Indices of the blue square (width, height)
        :rtype: list
        """
        return self.ind

    def getDistance(self):
        """
        Returns the distance between the blue square and the corner
        :returns: Distance of the blue square
        :rtype: float
        """
        return self.dist

    def getSizeOriginal(self):
        """
        Returns the size of the original image
        :returns: Size of the original image (width, height)
        :rtype: list
        """
        return [self.w_ori, self.h_ori]

    def _findmin(self):
        """
        From the distance map and the 'ring' where a blue pixel has been found,
        compute the position with a blue pixel the closest to the corner.
        """
        d_exact = np.inf
        ind = [0, 0]
        # the loops are not over the full size because
        # the good pixels are inside a square of size self.n
        # loop over the height
        for i in range(self.n + 1):
            # loop over the width
            for j in range(self.w - self.n - 1, self.w):
                # check if it is on the good ring
                if self.dist[i, j] == self.n:
                    # check the color of the pixel
                    if checkColor(self.img[i, j], self.threshold):
                        # compute the exact distance (float not int)
                        tmp = np.sqrt(i ** 2 + (self.w - j - 1) ** 2)
                        # check if closer and has at least 2 neighbours
                        if d_exact > tmp and self._checkNext((i, j)):
                            d_exact = tmp
                            ind = [i, j]
        # save the values
        self.ind = [ind[1] + self.xmin, ind[0]]
        self.dist = d_exact

    def _checkNext(self, ind):
        """
        Check the pixel next to the position 'ind' in order
        to check if the pixel is isolated or is in a cluster.
        :param list ind: Position to check
        :returns: True if at least 2 blue pixel are in the 8 closest pixels
        :rtype: bool
        """
        count = 0
        # check in each direction
        if ind[0] != 0:
            tmp = (ind[0] - 1, ind[1])
            if checkColor(self.img[tmp], self.threshold):
                count += 1
            if ind[1] != 0:
                tmp = (ind[0] - 1, ind[1] - 1)
                if checkColor(self.img[tmp], self.threshold):
                    count += 1
            if ind[1] != self.w - 1:
                tmp = (ind[0] - 1, ind[1] + 1)
                if checkColor(self.img[tmp], self.threshold):
                    count += 1

        if ind[0] != self.h - 1:
            tmp = (ind[0] + 1, ind[1])
            if checkColor(self.img[tmp], self.threshold):
                count += 1
            if ind[1] != 0:
                tmp = (ind[0] + 1, ind[1] - 1)
                if checkColor(self.img[tmp], self.threshold):
                    count += 1
            if ind[1] != self.w - 1:
                tmp = (ind[0] + 1, ind[1] + 1)
                if checkColor(self.img[tmp], self.threshold):
                    count += 1

        if ind[1] != self.w - 1:
            tmp = (ind[0], ind[1] + 1)
            if checkColor(self.img[tmp], self.threshold):
                count += 1

        if ind[1] != 0:
            tmp = (ind[0], ind[1] - 1)
            if checkColor(self.img[tmp], self.threshold):
                count += 1

        # return value for the different cases
        if count >= 2:
            return True
        else:
            return False

    def _scan(self, ind):
        """
        Look the 8 closest pixels and append them in the todo queue
        (if they are at the good distance)
        :param list ind: Indices
        """

        if ind[0] != 0:
            self._tryPixel((ind[0] - 1, ind[1]))
            if ind[1] != 0:
                self._tryPixel((ind[0] - 1, ind[1] - 1))
            if ind[1] != self.w - 1:
                self._tryPixel((ind[0] - 1, ind[1] + 1))
        if ind[0] != self.h - 1:
            self._tryPixel((ind[0] + 1, ind[1]))
            if ind[1] != 0:
                self._tryPixel((ind[0] + 1, ind[1] - 1))
            if ind[1] != self.w - 1:
                self._tryPixel((ind[0] + 1, ind[1] + 1))
        if ind[1] != self.w - 1:
            self._tryPixel((ind[0], ind[1] + 1))
        if ind[1] != 0:
            self._tryPixel((ind[0], ind[1] - 1))

    def _tryPixel(self, ind):
        """
        Compute the distance of the pixel (if not already done)
        and append the pixel in the todo queue when required
        :param list ind: Indices
        """
        if self.dist[ind] == 0:
            d = np.sqrt(ind[0] ** 2 + (self.w - ind[1] - 1) ** 2)
            d = floor(d)
            if d == self.n:
                if ind not in self.todo:
                    self.todo.append(ind)


def checkColor(pixel, threshold):
    """
    Check if a pixel is blue by using the threshold given
    :param list pixel: BGR color
    :param int threshold: Threshold applied for each channel
    """
    if (pixel[0] > threshold and pixel[1] < threshold and
            pixel[2] < threshold):
        return True
    else:
        return False
