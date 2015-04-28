# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import sys
from operator import itemgetter
import pdb



def migrate(cr, version):
    reload(sys)
    sys.setdefaultencoding('UTF8')
    
    