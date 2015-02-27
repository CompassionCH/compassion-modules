# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import pdb

def migrate(cr, version):
    pdb.set_trace()
    if not version:
        return
    a = cr.execute(
    '''
    SELECT id FROM wkf WHERE osv = 'recurring.contract'
    ''')
   
    
