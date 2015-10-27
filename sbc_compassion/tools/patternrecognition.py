# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammannn@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
Define a few function that are useful in order to detect a pattern using the
sift implementation in opencv.
A method (keyPointCenter) has been defined in order to find an approximation
of the center based on the keypoint detected.
"""
import cv2
import numpy as np
import base64
import tempfile
from copy import deepcopy

from openerp import _
from openerp.exceptions import Warning


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################
def patternRecognition(image, pattern, crop_area=[0, 1, 0, 1],
                       threshold=2, save_res=False):
    """
    Try to find a pattern in the subset (given by crop_area) of the image.
    :param image: Image to analyze (array or str)
    :param str pattern: Pattern image data (encoded in base64)
    :param list crop_area: Subset of the image to cut (relative position). \
                           [x_min, x_max, y_min, y_max]
    :param int threshold: Number of keypoints to find in order \
    to define a match
    :param bool save_res: Save an image ('sift_result.jpg')\
    showing the keypoints

    :returns: None if not enough keypoints found, position of the keypoints \
    (first index image/pattern)
    :rtype: np.array(), np.array()
    """
    # read images
    if isinstance(image, str):
        img1 = cv2.imread(image)
    else:
        img1 = deepcopy(image)
    if img1 is None:
        raise Warning(
            _("Could not read template image"),
            _("Template image is broken"))
    with tempfile.NamedTemporaryFile() as temp:
        temp.write(base64.b64decode(pattern))
        temp.flush()
        img2 = cv2.imread(temp.name,
                          cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        if img2 is None:
            raise Warning(
                _("Could not read pattern image"),
                _("The pattern image is broken"))

    # cut the part useful for the recognition
    (xmin, ymin), img1 = subsetImage(img1, crop_area)

    # compute the keypoints
    sift = cv2.xfeatures2d.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # find matches between the two pictures
    good = findMatches(des1, des2)

    if save_res:
        img3 = cv2.drawMatchesKnn(img2, kp2, img1, kp1, good, None, flags=2)
        cv2.imwrite('sift_result.png', img3)

    if len(good) >= threshold:
        # put in a np.array the position of the image's keypoints
        keypoints = np.array([kp1[i[0].trainIdx].pt for i in good])
        # compute the position in the original picture
        keypoints = keypoints + np.array((xmin, ymin))
        return keypoints
    else:
        return None


def subsetImage(img, crop_area):
    """
    Cut a part of the image given by crop_area.
    Box is a tuple (of 2) containg a list of two elements.
    The tuple gives the choice between the width and the height,
    the list between the min and the max
    :param array img: Image read by cv2.imread
    :param list[] crop_area: Relative coordinate to cut
    :returns: Minimum in X and Y and the subset of the image
    :rtype: tuple(),array
    """
    h, w = img.shape[:2]
    # compute absolute coordinates
    xmin = round(w * crop_area[0])
    xmax = round(w * crop_area[1])
    ymin = round(h * crop_area[2])
    ymax = round(h * crop_area[3])
    # in opencv first index->height
    return (xmin, ymin), img[ymin:ymax, xmin:xmax]


def findMatches(des1, des2, test=0.8):
    """
    Look through the descriptor in order to find some matches.
    :param list[] des1: Descriptor of the image
    :param list[] des2: Descriptor of the template
    :returns: Matches found in the descriptors
    :rtype: list[Keypoints]
    """
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des2, des1, k=2)
    # Apply ratio test
    good = []
    for m, n in matches:
        if m.distance < test * n.distance:
            good.append([m])

    return good


def keyPointCenter(keypoint):
    """
    Compute the Center of the keypoints by using a weight computed
    with the distance (therefore a point far away from the main group
    [for example in case of error in the matching function] will have
    a small weight)

    :param np.array() keypoint: Keypoints computed by \
    :func:`patternRecognition` for either the image or the template
    :returns: Coordinates of the center
    :rtype: list[float]
    """
    if type(keypoint) is bool:
        return
    if len(keypoint) <= 1:
        return keypoint
    else:
        # normalization of the weights
        N = 0
        # return value
        center = np.array([0.0, 0.0])
        for i in keypoint:
            omega = 0
            for j in keypoint:
                # compute the distance
                omega += np.sum((np.array(i) - np.array(j)) ** 2)
            # invert the weight in order to have a small one
            # for a keypoint far away
            if omega == 0:
                omega = 1e-8
            omega = 1.0 / np.sqrt(omega)
            N += omega
            center += omega * np.array(i)
        return center / N
