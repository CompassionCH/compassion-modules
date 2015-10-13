"""
Define a few position in a scan
This file is the 'user' part of the importation of mails.
When a layout is modified, only this one needs to be changed (it should at
least)
"""
import numpy as np
from enum import Enum

# position of the upper-right corner of the blue square
bluesquare = np.array([580,8])
# relation between template and template image (index for Layout.name)
pattern = {'triforce': 0,
       }


class Layout:
    """
    Defines the different layouts (in order to add or remove one, needs 
    to modify at least ../models/sponsorship_correspondence.py and
    ../models/import_mail_line.py)
    """
    name = ['L1','L2','L3','L4','L5','L6']
    # width, height of the referece template
    size_ref = [595,842]
    # position of to cut for the qr code, pattern
    # [min x,max x, min y, max y]
    qrcode = [0,150,0,100]
    pattern_pos = [240,370,730,842]
                

    def __init__(self,value):
        if type(value) == int:
            self.value = number
        elif type(str):
            self.value = name.index(value)
        else:
            raise Exception("Type not accepted ({})".format(type(value)))

        self._init_pos()

    def getLayout():
        return name[self.value]

    def getValue():
        return self.value

    def _init_pos():
        # position given by patternrecognition.keyPointCenter
        # in the reference template.
        # the key needs to be the same name (without the extension) than in  
        # the directory ./pattern (except for bluesquare that does not depends on
        # a pattern)
        if self.value == 0:
            self.pattern = np.array([300,784])
            # position to cut for the checkboxes in the reference templated
            # [min x,max x, min y, max y] // x = for width, y = for height
            self.checkboxes = { 'fr': [263,284,12,32],
                                'it': [263,284,32,52],
                                'de': [263,284,52,72],
                                'es': [371,390,12,32],
                                'en': [371,390,32,52],
                                'other': [368,390,52,72]
                            }
        
        
