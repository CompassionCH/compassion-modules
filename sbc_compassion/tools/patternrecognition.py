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
import time
import math
from copy import deepcopy

from openerp import _
from openerp.exceptions import Warning


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################
def patternRecognition(image, pattern, crop_area=None,
                       threshold=2, full_result=False):
    """
    Try to find a pattern in the subset (given by crop_area) of the image.

    :param image: Image to analyze array
    :param pattern: Pattern image data (array or str encoded in base64)
    :param list crop_area: Subset of the image to cut (relative position). \
                           [x_min, x_max, y_min, y_max]
    :param int threshold: Number of keypoints to find in order \
    to define a match
    :param bool full_result: if True, returns result from pattern too
    :param float new_dpi: A new dpi smaller than 300 to reduce computation
    time

    :returns: None if not enough keypoints found, position of the keypoints \
    (first index image/pattern)
    :rtype: np.array(), np.array()
    """
    if crop_area is None:
        crop_area = [0, 1, 0, 1]
    # read images
    img1 = deepcopy(image)
    if img1 is None:
        raise Warning(
            _("Could not read template image"),
            _("Template image is broken"))
    if isinstance(pattern, str):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(base64.b64decode(pattern))
            temp.flush()
            img2 = cv2.imread(temp.name,
                              cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    else:
        img2 = pattern
    if img2 is None:
        raise Warning(
            _("Could not read pattern image"),
            _("The pattern image is broken"))

    # cut the part useful for the recognition
    (xmin, ymin), img1 = subsetImage(img1, crop_area)

    tic = time.time()
    algo = 'ORB'
    if algo == 'SIFT':
        # compute the keypoints and descriptors using SIFT
        sift = cv2.xfeatures2d.SIFT_create()
        kp1, des1 = sift.detectAndCompute(img1, None)
        kp2, des2 = sift.detectAndCompute(img2, None)
        if not full_result:
            print("\tSIFT keypoints: " + str(time.time() - tic))
    elif algo == 'ORB':
        # compute keypoints with ORB (FAST detector and BRIEF descriptor)
        orb = cv2.ORB_create()
        # ORB detect the corners (keypoints) with FAST
        kp1_tmp = orb.detect(img1, None)
        kp2_tmp = orb.detect(img2, None)
        # And compute the descriptors with BRIEF
        kp1, des1 = orb.compute(img1, kp1_tmp)
        kp2, des2 = orb.compute(img2, kp2_tmp)
        if not full_result:
            print("\tORB keypoints: " + str(time.time() - tic))

    if des1 is None or des2 is None:
        return None

    # find matches between the two pictures
    tic = time.time()
    good12 = findMatches(des1, des2)

    if not full_result:
        print("\tfindMatches: "+str(len(good12)) +
              " matches.\t" + str(time.time() - tic))
    better12 = removeBadMatches(good12, kp1, kp2)
    if not full_result:
        print("\tremoveBadMatches: "+str(len(better12)) +
              " matches.\t" + str(time.time() - tic))

    good21 = findMatches(des2, des1)
    better21 = removeBadMatches(good21, kp2, kp1)

    best12 = keepReciproqueMatches(better12, better21)
    if not full_result:
        print("\tkeepReciproqueMatches: "+str(len(best12)) +
              " matches.\t" + str(time.time() - tic))

    if full_result:
        return kp1, kp2, best12
    if len(best12) >= threshold:
        # list of positions of good keypoints
        # tic = time.time()
        posA = np.array([kp1[i[0].queryIdx].pt for i in best12])
        posB = np.array([kp2[i[0].trainIdx].pt for i in best12])
        angleA = np.array([kp1[i[0].queryIdx].angle for i in best12])
        angleB = np.array([kp2[i[0].trainIdx].angle for i in best12])
        # scaleAB, R, t = scaled_rigid_transform(posA, posB)
        # print "scaled_rigid_transform: " + str(time.time() - tic)

        disorder_pt, disorder_angle = measure_disorder(
            posA, posB, angleA, angleB)

        # put in a np.array the position of the image's keypoints
        keypoints = np.array([kp1[i[0].queryIdx].pt for i in best12])
        # compute the position in the original picture
        keypoints = keypoints + np.array((xmin, ymin))
        return keypoints, disorder_pt, disorder_angle
    else:
        return None, None, None


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
    xmin = int(round(w * crop_area[0]))
    xmax = int(round(w * crop_area[1]))
    ymin = int(round(h * crop_area[2]))
    ymax = int(round(h * crop_area[3]))
    # in opencv first index->height
    return (xmin, ymin), img[ymin:ymax, xmin:xmax]


def findMatches(desA, desB, test=0.8):
    """
    Look through the descriptor in order to find some matches.

    :param list[] des1: Descriptor of the image
    :param list[] des2: Descriptor of the template
    :returns: Matches found in the descriptors
    :rtype: list[Keypoints]
    """
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(desA, desB, k=2)
    # Apply ratio test
    good = []
    for m, n in matches:
        if m.distance < test * n.distance:
            good.append([m])

    return good


def removeBadMatches(goodAB, kpA, kpB, max_angle=45):
    betterAB = []
    for match in goodAB:
        angleA = kpA[match[0].queryIdx].angle
        angleB = kpB[match[0].trainIdx].angle
        dAngle = math.fabs(angleA-angleB)
        dAngle = dAngle if dAngle < 180 else 360-dAngle
        if dAngle < max_angle:
            betterAB.append(match)
    return betterAB


def keepReciproqueMatches(betterAB, betterBA):
    bestAB = []
    for matchAB in betterAB:
        idA = matchAB[0].queryIdx
        idB = matchAB[0].trainIdx
        for matchBA in betterBA:
            if idA == matchBA[0].trainIdx and idB == matchBA[0].queryIdx:
                bestAB.append(matchAB)
    return bestAB


def measure_disorder(posA, posB, angA, angB):
    """
    Naive function to check if the matching point clouds looks the same
    :param posA:
    :param posB:
    :param angA:
    :param angB:
    :return:
    """

    # centering positions around their mean
    posA = posA - posA.mean(axis=0)
    posB = posB - posB.mean(axis=0)

    # if the the two patterns are similar, with no deformation and with same
    # scale and orientations, then the sum of absolute differences should
    # be close to zero
    SAD = (np.absolute(posA-posB)).sum()
    # we return the mean of the Sum of Absolute Difference
    disorder_pt = SAD / len(posA)

    disorder_angle = (np.absolute(angA-angB)).mean()

    return disorder_pt, disorder_angle


def scaled_rigid_transform(A, B):
    """
    The rigid transform is made of translation and rotations.
    More explanations on http://nghiaho.com/?page_id=671
    Here we've modified the rigid transform by adding the scaling term. It is
    not a rigid transform anymore, but it still should find a nearly optimal
    transformation made of scaling, rotation and translation.
    """
    assert len(A) == len(B)

    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)

    # centre the points
    AA = A - centroid_A
    BB = B - centroid_B

    # compute the scale factor from AA to BB. To do so, we compute the sum
    # of magnitude A and B. (sum of pythagor)
    magnitude_A = np.sum(np.sqrt(np.sum((np.square(AA)), axis=1)))
    magnitude_B = np.sum(np.sqrt(np.sum((np.square(BB)), axis=1)))

    scaleAB = magnitude_B/magnitude_A
    AA *= scaleAB

    # dot is matrix multiplication for array
    H = np.transpose(AA) * BB

    # compute the singular value decomposition transformation.
    U, S, Vt = np.linalg.svd(H)

    R = Vt.T * U.T

    # special reflection case
    if np.linalg.det(R) < 0:
        print("Reflection detected")
        Vt[1, :] *= -1
        R = Vt.T * U.T

    t = -scaleAB*R * centroid_A.T + centroid_B.T

    return scaleAB, R, t


def keyPointCenter(keypoints):
    """
    Compute the Center of the keypoints by using a weight computed
    with the distance (therefore a point far away from the main group
    [for example in case of error in the matching function] will have
    a small weight)

    :param np.array() keypoints: Keypoints computed by \
    :func:`patternRecognition` for either the image or the template
    :returns: Coordinates of the center
    :rtype: list[float]
    """
    # if not keypoints:
    if type(keypoints) is bool:
        return
    if len(keypoints) <= 1:
        return keypoints
    else:
        # normalization of the weights
        N = 0
        # return value
        center = np.array([0.0, 0.0])
        for i in keypoints:
            omega = 0
            for j in keypoints:
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


def find_template(img, templates, test=False,
                  threshold=0.8, resize_ratio=1.0):
    """
    Use pattern recognition to detect which template correponds to img.

    :param img: Opencv Image to analyze
    :param templates: Collection of all templates
    :param bool test: Enable the test mode (return an image as the last \
        parameter). If False, the image is None.
    :param threshold: Ratio of the templates' keypoints requested
    :returns: Detected template, center position of detected pattern,\
        image showing the detected keypoints for all the template
    :rtype: template, layout, None or np.array
    """
    # number of keypoint related between the picture and the pattern
    nb_keypoints = 0.0
    # TODO: min_disorder = sys.float_info.max
    key_img = False
    matching_template = None
    if test:
        test_img = []
    else:
        test_img = None

    for template in templates:
        # Crop the image to speedup detection and avoid false positives
        crop_area = template.get_pattern_area()

        # resizing the pattern, assuming it had been saved at 300dpi
        temp_image = []
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(base64.b64decode(template.pattern_image))
            temp.flush()
            temp_image = cv2.imread(temp.name,
                                    cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        temp_image = cv2.resize(temp_image, None,
                                fx=resize_ratio, fy=resize_ratio,
                                interpolation=cv2.INTER_CUBIC)
        if test:
            # TODO CROP IMAGE BEFOR FUNCTION CALL
            recognition = patternRecognition(
                img, temp_image, crop_area, full_result=True)

            # with tempfile.NamedTemporaryFile() as temp:
            #    temp.write(base64.b64decode(template.pattern_image))
            #    temp.flush()
            #    img2 = cv2.imread(temp.name)
            (xmin, ymin), img1 = subsetImage(img, crop_area)
            if recognition is not None:
                kp1, kp2, good = recognition
                img3 = cv2.drawMatchesKnn(img1, kp1, temp_image,
                                          kp2, good, None, flags=2)
            else:
                img3 = img1
            test_img.append(img3)

        print("\n" + str(template.id) + ") " + template.name + ": ")
        # try to recognize the pattern
        res = patternRecognition(img, temp_image, crop_area)
        if res is None:
            continue

        tmp_key, tmp_disorder_pt, tmp_disorder_angle = res
        if tmp_key is None:
            continue

        print("\tAngle disorder: " + str(tmp_disorder_angle))
        print("\tPositions disorder: " + str(tmp_disorder_pt))

        # check if it is a better result than before
        if (len(tmp_key) > nb_keypoints):
            # save all the data if it is better
            nb_keypoints = len(tmp_key)
            key_img = tmp_key
            matching_template = template

    print("\nDetected template: " + matching_template.name + ' (' +
          matching_template.layout + ')')
    return matching_template, keyPointCenter(key_img), test_img
