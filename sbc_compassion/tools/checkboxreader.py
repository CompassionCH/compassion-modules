"""
"""
import cv2
import numpy as np
import copy
from math import copysign

class CheckboxReader:
    """
    """

    def __init__(self,img,ratiomin=0.01,ratiomax=0.9):
        """
        """
        self.min = ratiomin
        self.max = ratiomax
        # read the image in greyscale
        self.img = cv2.imread(img,0)
        self.h, self.w = self.img.shape[:2]
        self.state = None
        self._findCorner()
        self._checkConnectivity()
        if len(self.corners) == 4:
            i = self._findBorder()
            self._findState(i)

    def getState(self):
        """
        """
        return self.state


    def _findState(self,border):
        """
        """
        start = copy.deepcopy(self.corners[0])
        d = start[0]**2 + start[1]**2
        for i in self.corners:
            d_tmp = i[0]**2 + i[1]**2
            if d_tmp < d:
                start = i
                d = d_tmp
        end = copy.deepcopy(self.corners[0])
        d = (self.h-end[0])**2 + (self.w-end[1])**2
        for i in self.corners:
            d_tmp = (self.h-i[0])**2 + (self.w-i[1])**2
            if d_tmp < d:
                end = i
                d = d_tmp
        black = 0
        pixel = 0
        for i in range(start[0]+border,end[0]-border):
            for j in range(start[1]+border,end[1]-border):
                pixel += 1
                if isBlack(self.img[i,j]):
                    black += 1
        
        ratio = float(black)/float(pixel)

        self.state = False
        if ratio > self.min and ratio < self.max:
            self.state = True
        


    def _findCorner(self):
        """
        """
        self.corners = []
        for i in range(self.h):
            for j in range(self.w):
                self._checkPixel(i,j)

    def _checkPixel(self,i,j):
        """
        check if corner and add to self.corners
        """
        down = [False,False]
        up = [False,False]
        right = [False,False]
        left = [False,False]
        # discard case where i,j is not black and discard case
        # too close to the border
        if (isBlack(self.img[i,j]) and i>1 and i<self.h-2
            and j<self.w-2 and j>1):
            if isBlack(self.img[i+1,j]):
                down[0] = True
            if isBlack(self.img[i+2,j]):
                down[1] = True
            if isBlack(self.img[i-1,j]):
                up[0] = True
            if isBlack(self.img[i-2,j]):
                up[1] = True
            if isBlack(self.img[i,j+1]):
                right[0] = True
            if isBlack(self.img[i,j+2]):
                right[1] = True
            if isBlack(self.img[i,j-1]):
                left[0] = True        
            if isBlack(self.img[i,j-2]):
                left[1] = True        

        if isCorner(down,up,right,left):
            self.corners.append((i,j))

    def _checkConnectivity(self):
        """
        check connected corner
        """
        ret, sure_fg = cv2.threshold(self.img,128,255,0)
        marker = connectedComponents(sure_fg)
        cv2.imwrite('watershed.png',marker)
        cluster = []
        while len(self.corners)!=0:
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

        self.corners = []
        for i in cluster:
            if len(i) > len(self.corners):
                self.corners = i

        a = 0
        for i in cluster:
            if len(i) == len(self.corners):
                a += 1
                
        if a > 1:
            raise Exception('Two squares have been detected')
    
    def _findBorder(self):
        """
        """
        width = np.inf
        for i in self.corners:
            for j in self.corners:
                if i != j:
                    dist_max = np.abs(i[0]-j[0])
                    dist_max = np.maximum(dist_max,np.abs(i[1]-j[1]))
                    if dist_max < width:
                        width = dist_max
        i = 1
        border = True
        while i < width/2 and border:
            border = self._isStillBorder(i)
            i += 1
        i = i-1
        return i


    def _isStillBorder(self,distance):
        """
        """
        for i in self.corners:
            k = 0
            d = [-1, -1, -1]
            neigh = []
            for j in self.corners:
                if j!=i:
                    neigh.append(j)
                    d[k] = (j[0]-i[0])**2 + (j[1]-i[1])**2
                    k += 1
            d = d.index(max(d))
            k = 0
            # find direction other corners
            direct = [0,0]
            if abs(neigh[d][0]) > 1:
                direct[0] = copysign(1,neigh[d][0])*distance
            if abs(neigh[d][1]) > 1:
                direct[1] = copysign(1,neigh[d][1])*distance

            ind = [i[0]+direct[0],i[1]+direct[1]]
            if not isBlack(self.img[tuple(ind)]):
                return False
            # check pixel between corners
            for j in neigh:
                if d!=k:
                    # NEED ADD INDEX
                    ind = [(i[0]+j[0])/2,(i[0]+j[0])/2]
                    
                    mdir = [0,0]
                    if abs(j[0]) > 1:
                        mdir[1] = direct[1]
                    if abs(j[1]) > 1:
                        mdir[0] = direct[0]

                    ind = [ind[0]+mdir[0],ind[1]+mdir[1]]
                    if not isBlack(self.img[tuple(ind)]):
                        return False
                k += 1

def isBlack(pixel,threshold=90):
    """
    """
    if pixel > threshold:
        return False
    else:
        return True


def isCorner(down,up,right,left):
    """
    """

    if (isDirectionOK(right,left) and 
        isDirectionOK(down,up)):
        return True
    else:
        return False


def isDirectionOK(a,b):
    """
    """
    # case where a True is on each side
    if (a[0] or a[1]) and (b[0] or b[1]):
        return False
    # case where a False is on each side
    elif (not a[0] or not a[1]) and (not b[0] or not b[1]):
        return False
    else:
        return True
        


def connectedComponents(img,connectivity=8):
    """
    """
    con = np.zeros((3,3),bool)
    if connectivity==8:
        con[0,:] = 1
        con[1,:2] = 1
    elif connectivity==4:
        con[0,1] = 1
        con[1,:2] = 1
    else:
        raise Exception('{}-connectivity does not exist'.format(connectivity))

    h,w = img.shape[:2]
    # square mask
    mh = (con.shape[0]-1)/2
    mw = mh
    ret = np.zeros((h,w),np.int8)
    col = 1
    E = []
    for i in range(h):
        for j in range(w):
            if img[i,j] == 0:
                col_tmp = -1
                for x in range(con.shape[0]):
                    for y in range(con.shape[1]):
                        if (i+x-mh < h and i+x-mh >= 0 and
                            j-mw+y < w and j-mw+y >= 0):
                            if ret[i+x-mh,j-mw+y] != 0 and con[x,y]:
                                a = ret[i+x-mh,j-mw+y]
                                if col_tmp != -1:
                                    if a not in E[col_tmp-1]:
                                        E[col_tmp-1].append(a)
                                    if col_tmp not in E[a-1]:
                                        E[a-1].append(col_tmp)
                                    if a < col_tmp:
                                        col_tmp = a
                                else:
                                    col_tmp = a
                if col_tmp == -1:
                    ret[i,j] = col
                    E.append([col])
                    col += 1
                else:
                    ret[i,j] = col_tmp

    eq_table = col*np.ones(col-1,int)
    for i in range(col-1):
        eq_table[i] = min(E[i])

    for i in range(h):
        for j in range(w):
            if ret[i,j] != 0:
                ret[i,j] = eq_table[ret[i,j]-1]
    return ret

