##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Girardin <emmanuel.girardin@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
Run this script if you want to compute the best decision threshold for the
class CheckBoxReader. The main is at the end of the file and contains a few
more explanations
"""

import os
import logging
from . import checkboxreader as cbr

_logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError:
    _logger.warning('Please install cv2, numpy and matplotlib to use SBC '
                    'module')


def findmax(x):
    m = max(x)
    ind = [i for i, val in enumerate(x) if val == m]
    return m, ind


def findmin(x):
    m = min(x)
    ind = [i for i, val in enumerate(x) if val == m]
    return m, ind


def plot(img):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.imshow(img, cmap='gray', interpolation='nearest')
    plt.pause(1)


def compute_threshold(D1, D2, display=False):
    D12 = np.concatenate((D1, D2))

    N1 = len(D1)
    N2 = len(D2)

    bins = list(range(0, int(max(D12)), int(max(D12)/50.0)))

    # We define P1 to be the probability of the box to be checked, and P2 the
    # probability of being empty with P1 + P2 = 1
    P1 = 1.0/6.0
    P2 = 5.0/6.0

    # The probability distribution function can be computed as an histogram
    pdf1, bins1 = np.histogram(D1, bins)
    pdf2, bins2 = np.histogram(D2, bins)

    # We normalized them in order that their integral is equal to 1
    pdf1 = pdf1 / (1.0*N1)
    pdf2 = pdf2 / (1.0*N2)

    # Know we want to find the threshold 't' minimizing the following error
    # probability:   PErr(t) = P(D1<t) + P(D2>=t)
    # To do so, we will use the cummulative distribution function
    cdf1 = np.cumsum(pdf1)
    cdf2 = np.cumsum(pdf2)

    # cdf1[-1] and cdf2[-1] are supposed to be equal to 1 and
    # P(Error) can be computed like this
    PErr = P1*cdf1 + P2*(1-cdf2)

    # We finally find the minimum Error:
    mini, index = findmin(PErr)
    threshold = (bins[index[0]]+bins[index[-1]])/2.0

    if display:
        # Let's plot a few results
        fig = plt.figure()

        # plot pdfs
        hist = fig.add_subplot(121)
        hist.plot(bins1[1:], P1*pdf1, 'r-', linewidth=2)
        hist.plot(bins2[1:], P2*pdf2, 'b-', linewidth=2)
        hist.set_xlabel('Score distribution')
        hist.set_ylabel('Probability')
        hist.grid(True)

        # ROC Curve
        roc = fig.add_subplot(122)
        roc.plot(1-cdf2, 1-cdf1, linewidth=5)
        roc.set_xlabel('False Negative Rate')
        roc.set_ylabel('True Positive Rate')
        roc.grid(True)

        plt.show()
        plt.pause(1)
    return threshold


def train(folder, indices=None):
    D = []
    files = os.listdir(folder)
    files.sort()
    if not indices:
        indices = list(range(len(files)))
    for index in indices:
        img_name = files[index]
        img = cv2.imread(folder + '/' + img_name)
        cbr_img = cbr.CheckboxReader(img)
        score = cbr_img.compute_boxscore(boxsize=17)
        D.append(score)
    D = np.array(D)
    return D


def test(thresh, folder, indices=None):
    PR = 0
    files = os.listdir(folder)
    files.sort()
    if not indices:
        indices = list(range(len(files)))
    for index in indices:
        img_name = files[index]
        img = cv2.imread(folder + '/' + img_name)
        cbr_img = cbr.CheckboxReader(img)
        score = cbr_img.compute_boxscore(boxsize=17)
        if thresh < score:
            PR += 1.0
    PR //= (len(indices)*1.0)
    return PR

# ----------------------------------------------------------------------------
# ------------------------------- MAIN ---------------------------------------
# ----------------------------------------------------------------------------

# This script read a set of images in a folder. You can find a set of
# checkbox images at on the nas at /it/devel/Scan Lettres S2B/checkboxes
# folder0 contain two sub folder "True" and "False"
# True contains 100 small images of positive checkboxes, and "False"
# contains 100 of negative checkboxes


# Train
folder0 = '/home/openerp/dev/addons/compassion-modules/sbc_compassion/tests' \
          '/testdata/checkboxes'

DTrue = train(folder0 + '/True')
DFalse = train(folder0 + '/False')
# we compute the threshold which minimize the probability error. Set
# display to False if you haven't matplotlib installed
thresh = compute_threshold(DTrue, DFalse, display=True)
# pylint: disable=print-used
print(('A nice decision threshold would be ' + str(thresh)))

# Test:
# We finally test the threshold. It is better to test it on images that you
#  didn't used for the training.

# True and False Positive Rates
TruePR = test(thresh, folder0 + '/True')
FalsePR = test(thresh, folder0 + '/False')

# pylint: disable=print-used
print(('True Rositive Rate: ' + str(TruePR)))
# pylint: disable=print-used
print(('False Positive Rate: ' + str(FalsePR)))
