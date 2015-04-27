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


def migrate(cr, version):
    reload(sys)
    sys.setdefaultencoding('UTF8')

    if not version:
        return

    # Set the contract type
    cr.execute(
        '''
        UPDATE recurring_contract
        SET type = 'S'
        WHERE child_id IS NOT NULL
        '''
    )
    cr.execute(
        '''
        UPDATE recurring_contract
        SET type = 'O'
        WHERE child_id IS NULL
        '''
    )
