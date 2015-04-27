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


def migrate(cr, version):
    reload(sys)
    sys.setdefaultencoding('UTF8')

    if not version:
        return

    activities_to_migrate = ['banking_validation', 'validation', 'mandate', 'cancelled', 'waiting']
    
    for activity in activities_to_migrate:
        cr.execute(
        '''
        SELECT id,create_date FROM wkf_activity
        WHERE name = '{}'
        '''.format(activity))
        
        activity_ids = cr.fetchall()

        new_activity_id = max(activity_ids,key=itemgetter(1))[0]
        old_activity_id = min(activity_ids,key=itemgetter(1))[0]
        
        # Update workitems
        cr.execute(
        '''
        UPDATE wkf_workitem 
        SET act_id = {0}
        WHERE act_id = {1}
        '''.format(new_activity_id, old_activity_id)
        )
        
        # Update transitions
        cr.execute(
        '''
        UPDATE wkf_transition 
        SET act_to = {0}
        WHERE act_to = {1}
        '''.format(new_activity_id, old_activity_id)
        )

        cr.execute(
        '''
        UPDATE wkf_transition 
        SET act_from = {0}
        WHERE act_from = {1}
        '''.format(new_activity_id, old_activity_id)
        )
    
