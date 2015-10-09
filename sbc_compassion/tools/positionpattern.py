"""
Define a few position in a scan
"""
import numpy as np

# width, height of the referece template
size_ref = [595,842]

# position of to cut for the qr code, pattern
# [min x,max x, min y, max y]
qrcode = [0,150,0,100]
pattern_pos = [240,370,730,842]

# position to cut for the checkboxes in the reference templated
# [min x,max x, min y, max y] // x = for width, y = for height
checkboxes = { 'fr': [263,284,12,32],
               'it': [263,284,32,52],
               'de': [263,284,52,72],
               'es': [371,390,12,32],
               'en': [371,390,32,52],
               'other': [368,390,52,72]
}


# position given by patternrecognition.keyPointCenter
# in the reference template.
# the key needs to be the same name (without the extension) than in  
# the directory ./pattern (except for bluesquare that does not depends on
# a pattern)
pattern = { 'triforce': np.array([300,784]),
            'bluesquare': np.array([580,8])
}
