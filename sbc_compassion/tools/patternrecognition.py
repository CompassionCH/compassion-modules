##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammannn@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
Define a few function that are useful in order to detect a pattern using the
sift implementation in opencv.
A method (keyPointCenter) has been defined in order to find an approximation
of the center based on the keypoint detected.
"""
import base64
import logging
import math
import tempfile
from copy import deepcopy
from time import time

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
except ImportError:
    _logger.warning(
        "Please install cv2 and numpy on your system to use SBC module")


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################
def patternRecognition(
        image, pattern, crop_area=None, threshold=2, full_result=False, algo="ORB"
):
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
    :param string algo: Feature descriptor algorithm. Can be either 'SIFT'
    or 'ORB'. The advantage of ORB is that it is free and do not need the
    use of opencv-contrib

    :returns: None if not enough keypoints found, position of the keypoints \
    (first index image/pattern)
    :rtype: np.array(), np.array()
    """
    if crop_area is None:
        crop_area = [0, 1, 0, 1]
    # read images
    img1 = deepcopy(image)
    if img1 is None:
        raise UserError(_("Template image is broken"))
    if isinstance(pattern, bytes):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(base64.b64decode(pattern))
            temp.flush()
            img2 = cv2.imread(temp.name, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    else:
        # TODO this will make this line fail:
        # kp2, des2 = feature_descriptor.detectAndCompute(img2, None)
        img2 = pattern
    if img2 is None:
        raise UserError(_("The pattern image is broken"))

    # cut the part useful for the recognition
    (xmin, ymin), img1 = subsetImage(img1, crop_area)

    feature_descriptor = None
    if algo == "SIFT":
        # compute the keypoints and descriptors using SIFT
        feature_descriptor = cv2.xfeatures2d.SIFT_create()
    elif algo == "ORB":
        # compute keypoints with ORB (FAST detector and BRIEF descriptor)
        # The threshold has to lay between 1 and 15. The LOWER is the
        # threshold, the HIGHER is the number of detected feature. The
        # default threshold is 12. We choose 8 because 12 was to
        # restrictive for our small images
        feature_descriptor = cv2.ORB_create(edgeThreshold=8)

    kp1, des1 = feature_descriptor.detectAndCompute(img1, None)
    kp2, des2 = feature_descriptor.detectAndCompute(img2, None)

    if des1 is None or des2 is None or min(len(des1), len(des2)) < 2:
        return None

    # Find feature in img1 matching with features of img2
    matches12 = findMatches(des1, des2, algo)
    matches12 = removeBadMatches(matches12, kp1, kp2)

    # Find feature in img2 matching with features of img1
    matches21 = findMatches(des2, des1, algo)
    matches21 = removeBadMatches(matches21, kp2, kp1)

    # We keep only matches contained matches12 AND matches21
    good_matches = keepReciproqueMatches(matches12, matches21)

    if full_result:
        return kp1, kp2, good_matches
    if len(good_matches) >= threshold:
        # put in a np.array the position of the image's keypoints
        keypoints1 = np.array([kp1[i[0].queryIdx].pt for i in good_matches])
        keypoints2 = np.array([kp2[i[0].trainIdx].pt for i in good_matches])

        # measure if the two sets of point look similar or not (in terms of
        # location)
        disorder_pt = measure_disorder(keypoints1, keypoints2)

        # compute the position in the original picture
        keypoints1 = keypoints1 + np.array((xmin, ymin))
        return keypoints1, disorder_pt
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
    xmin = int(round(w * crop_area[0]))
    xmax = int(round(w * crop_area[1]))
    ymin = int(round(h * crop_area[2]))
    ymax = int(round(h * crop_area[3]))
    # in opencv first index->height
    return (xmin, ymin), img[ymin:ymax, xmin:xmax]


def findMatches(desA, desB, algo="SIFT", test=0.8):
    """
    Look through the descriptor in order to find some matches.

    :param list[] desA: Descriptor of the image
    :param list[] desB: Descriptor of the template
    :param string algo: must be 'SIFT' or 'ORB'. It will help to select the
    distance measurement to be used
    :returns: Matches found in the descriptors
    :rtype: list[Keypoints]
    """

    # Brute Force Matcher.
    norm = cv2.NORM_HAMMING if algo == "ORB" else cv2.NORM_L2
    bf = cv2.BFMatcher(normType=norm)

    matches = bf.knnMatch(desA, desB, k=2)
    # Apply ratio test
    good = []
    for m, n in matches:
        if m.distance < test * n.distance:
            good.append([m])

    return good


def removeBadMatches(matchesAB, kpA, kpB, max_angle=45):
    """
    SIFT and ORB are rotation invariant. which means that they detect
    matches regardless of the rotation. But in our case, we know that our
    images have roughly the same orientation. This function aim to remove
    matches where the difference of angle between kpA and kpB is
    bigger than max_angle.

    :param matchesAB: Contains the matching indices of kpA to kpB
    :param kpA: Keypoints of image A
    :param kpB: Keypoints of image B
    :param max_angle: Maximum angle difference allowed for a match
    :return: filtered_matchesAB: The new set of match which is not rotation
    invariant anymore
    """

    filtered_matchesAB = []
    for match in matchesAB:
        angleA = kpA[match[0].queryIdx].angle
        angleB = kpB[match[0].trainIdx].angle
        dAngle = math.fabs(angleA - angleB)
        dAngle = dAngle if dAngle < 180 else 360 - dAngle
        if dAngle < max_angle:
            filtered_matchesAB.append(match)
    return filtered_matchesAB


def keepReciproqueMatches(betterAB, betterBA):
    bestAB = []
    for matchAB in betterAB:
        idA = matchAB[0].queryIdx
        idB = matchAB[0].trainIdx
        for matchBA in betterBA:
            if idA == matchBA[0].trainIdx and idB == matchBA[0].queryIdx:
                bestAB.append(matchAB)
    return bestAB


def measure_disorder(posA, posB):
    """
    Naive function to check if the matching point clouds looks the same

    :param posA:
    :param posB:
    :return:
    """

    # centering positions around their mean
    posA = posA - posA.mean(axis=0)
    posB = posB - posB.mean(axis=0)

    # if the the two patterns are similar, with no deformation and with same
    # scale and orientations, then the sum of absolute differences should
    # be close to zero
    SAD = (np.absolute(posA - posB)).sum()
    # we return the mean of the Sum of Absolute Difference
    disorder_pt = SAD // len(posA)
    return disorder_pt


def scaled_rigid_transform(A, B):
    """
    NOTICE: This function could be used within a RANSAC algorithm to
    detect outliers in the matching. However, the RANSAC part haven't been
    coded yet because I finally found an other way to detect outliers which is
    simpler and which is efficient enough.

    That function gives the transformation between the
    set of point A and B minimizing the square distance.
    The rigid transform is made of translation and rotations.
        (see http://nghiaho.com/?page_id=671)
    Here we've modified the rigid transform by adding the scaling term. It is
    not a rigid transform anymore, but it still should find a nearly optimal
    transformation made of scaling, rotation and translation.

    :param np.array A: List of position (x,y) of the keypoints A
    :param np.array B: List of position (x,y) of the keypoints B matching
    with keypoints B
    :return: tuple (scaleAB, R, t):
        scaleAB: scale factor of A to B. If A and B are similar, it should
        be close to 1.0
        R: Rotation matrix. should be close to [[1, 0], [0, 1]]
        t: translation vector, can be anything
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

    scaleAB = magnitude_B / magnitude_A
    AA *= scaleAB

    # dot is matrix multiplication for array
    H = np.transpose(AA) * BB

    # compute the singular value decomposition transformation.
    U, S, Vt = np.linalg.svd(H)

    R = Vt.T * U.T

    # special reflection case
    if np.linalg.det(R) < 0:
        Vt[1, :] *= -1
        R = Vt.T * U.T

    t = -scaleAB * R * centroid_A.T + centroid_B.T

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


def find_template(img, templates, resize_ratio=1.0):
    """
    Use pattern recognition to detect which template correponds to img.

    :param img: Opencv Image to analyze
    :param templates: Collection of all templates
    :returns: Detected template, center position of detected pattern,\
        image showing the detected keypoints for all the template
    :rtype: template, layout, None or np.array
    """
    tic = time()
    # number of keypoint related between the picture and the pattern
    nb_keypoints = 0.0
    # we will store the nb of matched keypoints for each pattern (only used
    #  by _logger.debug)
    score = ["0" for k in templates]
    _logger.debug(
        "\t\t\tTemplates ids:\t\t" + "\t".join([str(t.id) for t in templates])
    )

    key_img = False
    matching_template = None

    i = -1
    for template in templates:
        i = i + 1
        # Crop the image to speedup detection and avoid false positives
        crop_area = template.get_pattern_area()
        (xmin, ymin), img1 = subsetImage(img, crop_area)

        # resizing the pattern, assuming it had been saved at 300dpi
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(base64.b64decode(template.pattern_image))
            temp.flush()
            temp_image = cv2.imread(
                temp.name, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
            )
        # temp_image = cv2.resize(
        #     temp_image,
        #     None,
        #     fx=resize_ratio,
        #     fy=resize_ratio,
        #     interpolation=cv2.INTER_CUBIC,
        # )

        # plt.imshow(img1)
        # plt.show()
        #
        # plt.imshow(temp_image)
        # plt.show()

        # try to recognize the pattern
        res = patternRecognition(img1, temp_image)
        del temp_image
        if res is None:
            continue

        tmp_key, tmp_disorder_pt = res
        if tmp_key is None:
            continue

        # check if it is a better result than before
        if len(tmp_key) > nb_keypoints and len(tmp_key) > 5:
            # save all the data if it is better
            nb_keypoints = len(tmp_key)
            key_img = tmp_key
            matching_template = template

        score[i] = str(len(tmp_key))

    tic = time() - tic
    _logger.debug("\t\t\tTemplates scores:\t" + "\t".join(score))
    if matching_template:
        _logger.debug(
            "\t\t\tTemplate '"
            + matching_template.name
            + f"' matched with {nb_keypoints} keypoints in {tic:.3} seconds"
        )
    else:
        _logger.warning("\t\t\tNo template found.")
    return matching_template, keyPointCenter(key_img)
