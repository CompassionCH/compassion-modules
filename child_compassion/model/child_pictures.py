# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config


class child_pictures(orm.Model):

    _name = 'compassion.child.pictures'
    
    _columns = {
        'child_id': fields.many2one('compassion.child', _('Child')),
        'fullshot': fields.char('Fullshot'),    # FIXME
        'headshot': fields.char('Fullshot'),    # FIXME
        'date': fields.date(_('Date of pictures')),
    }