"""
Define a few function that are useful in order to detect a pattern using the sift implementation
in opencv.
A method (keyPointCenter) has been defined in order to find an approximation
of the center based on the keypoint detected.
"""
import cv2
import numpy as np


def patternRecognition(image,template,box=([0,1],[0,1]),threshold=2,save_res=False):
    """
    Try to find a pattern in the subset (given by box) of the image.
    
    :param str image: Name of the image
    :param str template: Name of the template
    :param tuple(list) box: Subset of the image to cut (relative position). \
    First index w/h, second min/max
    :param int threshold: Number of keypoints to find in order to define a match
    :param bool save_res: Save an image ('sift_result.jpg') showing the keypoints

    :returns: None if not enough keypoints found, position of the keypoints (first index image/template)
    :rtype: np.array(), np.array()
    """
    
    # read images
    img1 = cv2.imread(image)
    img2 = cv2.imread(template)

    # cut the part useful for the recognition
    (xmin,ymin),img1 = subsetImage(img1,box)
    
    # compute the keypoints
    sift = cv2.xfeatures2d.SIFT_create()
    kp1,des1 = sift.detectAndCompute(img1,None)
    kp2,des2 = sift.detectAndCompute(img2,None)
    
    # find matches between the two pictures
    good = findMatches(des1,des2)

    print len(good)
    if save_res:
        img3 = cv2.drawMatchesKnn(img2,kp2,img1,kp1,good,None,flags=2)
        cv2.imwrite('sift_result.png',img3)
    
    if len(good) >= threshold:
        # put in a np.array the position of the image's keypoints
        ret1 = np.array([kp1[i[0].trainIdx].pt for i in good])
        # compute the position in the original picture
        ret1 = ret1 + np.array((xmin,ymin))
        # put in a np.array the position of the template's keypoints
        ret2 = np.array([kp2[i[0].queryIdx].pt for i in good])
        return ret1,ret2
    else:
        return None

def subsetImage(img,box):
    """
    Cut a part of the image given by box.
    Box is a tuple (of 2) containg a list of two elements.
    The tuple gives the choice between the width and the height,
    the list between the min and the max
    :param array img: Image read by cv2.imread
    :param tuple(list[]) box: Relative coordinate to cut
    :returns: Minimum in X and Y and the subset of the image
    :rtype: tuple(),array
    """
    h,w = img.shape[:2]
    # compute absolute coordinates
    xmin = round(w*box[0][0])
    xmax = round(w*box[0][1])
    ymin = round(h*box[1][0])
    ymax = round(h*box[1][1])
    # in opencv first index->height
    return (xmin,ymin),img[ymin:ymax,xmin:xmax]
    

def findMatches(des1,des2,test=0.8):
    """
    Look through the descriptor in order to find some matches.
    :param list[] des1: Descriptor of the image
    :param list[] des2: Descriptor of the template
    :returns: Matches found in the descriptors
    :rtype: list[Keypoints] 
    """
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des2,des1,k=2)
    # Apply ratio test
    good = []
    for m,n in matches:
        if m.distance < test*n.distance:
            good.append([m])
    
    return good


def keyPointCenter(keypoint):
    """
    Compute the Center of the keypoints by using a weight computed with the distance
    (therefore a point far away from the main group [for example in case of error in
    the matching function] will have a small weight)
    :param np.array() keypoint: Keypoints computed by :func:`patternRecognition` \
    for either the image or the template
    :returns: Coordinates of the center
    :rtype: list[float]
    """
    if len(keypoint) <= 1:
        return keypoint
    else:
        # normalization of the weights
        N = 0
        # return value
        center = np.array([0.0,0.0])
        for i in keypoint:
            omega = 0
            for j in keypoint:
                # compute the distance
                omega += np.sum((np.array(i)-np.array(j))**2)
            # invert the weight in order to have a small one
            # for a keypoint far away
            if omega == 0:
                omega = 1e-8
            omega = 1.0/np.sqrt(omega)
            N += omega
            center += omega*np.array(i)
        return center/N

