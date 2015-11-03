"""
"""
import cv2
import numpy as np
import zxing
from os import remove


class StickerWriter:

    """
    """
    size = [2480, 3508]  # 300 dpi
    zx = zxing.BarCodeTool()

    def __init__(self, text):
        """
        dict
        """
        self.text = text
        self.img = 255 * np.ones(self.size, np.uint8)
        #
        # This code is not working with new template models
        #
        # self.lay = LayoutLetter()
        # lay = self.lay.getLayout()
        # key = self.text.keys()
        # n = len(key)
        # for i,sticker in enumerate(lay):
            # while i >= n:
                # i -= n
            # name = key[i]
            # code = self.text[key[i]]
            # self._draw(sticker,name,code)

    def getImage():
        """
        """

    def _draw(self, sticker, name, code):
        """
        """
        file_ = '/tmp/stickerwriter_qr_code.png'
        self.zx.encode(
            file_, code, width=self.lay.qr_code, height=self.lay.qr_code)
        qr = cv2.imread(file_)
        h, w = qr.shape[:2]
        for i in range(w):
            for j in range(h):
                indi = sticker[0] + self.margin + i
                indj = sticker[1] + self.margin + j
                self.img[indi, indj] = qr[i, j]
        pdb.set_trace()
        remove(file_)
