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
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime


class child_property(orm.Model):
    _inherit = 'compassion.child.property'

    def attach_pictures(self, cr, uid, ids, pictures_id, context=None):
        res = super(child_property, self).attach_pictures(
            cr, uid, ids, pictures_id, context)
        if res:
            six_months = 180
            case_study_date = self.browse(cr, uid, ids[0], context).info_date
            case_study_date = datetime.strptime(case_study_date, DF)

            picture_obj = self.pool.get('compassion.child.pictures')
            picture_date = picture_obj.browse(
                cr, uid, pictures_id, context).date
            picture_date = datetime.strptime(picture_date, DF)

            date_diff = abs((case_study_date - picture_date).days)

            if (date_diff > six_months):
                picture_obj.write(
                    cr, uid, pictures_id, {'case_study_id': False}, context)
                self.unattach_pictures(cr, uid, ids, pictures_id, context)

        return res

    def unattach_pictures(self, cr, uid, ids, pictures_id, context=None):
        self.write(cr, uid, ids, {'pictures_id': False}, context)
        
