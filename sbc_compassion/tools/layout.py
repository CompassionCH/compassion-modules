"""
Define a few position in a scan
This file is the 'user' part of the importation of mails.
When a layout is modified, only this one needs to be changed (it should at
least)
"""
import numpy as np

# position of the upper-right corner of the blue square
bluesquare = np.array([580, 8])
# relation between template and template image (index for Layout.name)
pattern = {'triforce': 0}


class Layout:
    """
    Abstract class in order to do inheritance
    """
    size_ref = []


class LayoutLetter(Layout):
    """
    Defines the different layouts (in order to add or remove one, needs
    to modify at least ../models/sponsorship_correspondence.py and
    ../models/import_mail_line.py)

    :param int|str value: Layout (can be the list index, the name of the \
    layout [e.g. 'L5'] or the name of the pattern)
    """
    name = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']
    # width, height of the referece template
    size_ref = [595, 842]
    # position of to cut for the qr code, pattern
    # [min x,max x, min y, max y]
    qrcode = [0, 150, 0, 100]
    pattern_pos = [240, 370, 730, 842]

    def __init__(self, value):
        if type(value) == int:
            self._setValue(value)
        elif type(str):
            if value in self.name:
                self._setValue(self.name.index(value))
            elif value in pattern.keys():
                self._setValue(pattern[value])
        else:
            raise Exception("Type not accepted ({})".format(type(value)))

        self._init_pos()

    def getLayout(self):
        """
        :returns: Name of the layout
        :rtype: str
        """
        if self.value is None:
            return None
        else:
            return self.name[self.value]

    def getValue(self):
        """
        :returns: Index in the list of layout
        :rtype: int
        """
        return self.value

    def _setValue(self, value):
        """
        Done in order to check if the value is right
        """
        if value < len(self.name) and value >= 0:
            self.value = value
        else:
            self.value = None

    def _init_pos(self):
        """
        Set the position that depends on the layout
        """
        # position given by patternrecognition.keyPointCenter
        # in the reference template.
        # the key needs to be the same name (without the extension) than in  
        # the directory ./pattern (except for bluesquare that does not depends
        # on a pattern)
        if self.value == 0:
            self.pattern = np.array([300, 784])
            # position to cut for the checkboxes in the reference templated
            # [min x,max x, min y, max y] // x = for width, y = for height
            self.checkboxes = {'fra': [263, 284, 12, 32],
                               'ita': [263, 284, 32, 52],
                               'deu': [263, 284, 52, 72],
                               'spa': [371, 390, 12, 32],
                               'eng': [371, 390, 32, 52],
                               'other': [368, 390, 52, 72]}
