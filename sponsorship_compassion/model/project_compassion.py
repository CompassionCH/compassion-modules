# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from datetime import datetime


class project_compassion(orm.Model):
    _inherit = 'compassion.project'

    def suspend_funds(self, cr, uid, project_id, context=None,
                      date_start=None, date_end=None):
        """ When a project is suspended, We update all contracts of
        sponsored children in the project, so that we don't create invoices
        during the period of suspension.
        We also remove the children on internet.
        """
        project = self.browse(cr, uid, project_id, context)
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(cr, uid, [
            ('child_code', 'like', project.code),
            ('state', 'in', ('active', 'waiting', 'mandate'))],
            context=context)
        contract_obj.suspend_contract(cr, uid, contract_ids, context,
                                      date_start, date_end)
        return True


class suspension_wizard(orm.TransientModel):
    """ Wizard to extend suspensions of projects. """
    _name = 'compassion.project.suspension.wizard'

    _columns = {
        'date_start': fields.date(_('Start of suspension')),
        'date_end': fields.date(_('End of suspension'),
                                help=_("will add 3 months if empty")),
    }

    _defaults = {
        'date_start': datetime.today().strftime(DF)
    }

    def perform_suspension(self, cr, uid, ids, context=None):
        project_id = context.get('active_id')
        if not project_id:
            raise orm.except_orm(
                _('No project selected'),
                _('Please select a project to suspend'))

        project_obj = self.pool.get('compassion.project')
        project = project_obj.browse(cr, uid, project_id, context)
        if project.suspension != 'fund-suspended':
            raise orm.except_orm(
                _('Suspension error'),
                _('The project is not fund-suspended. '
                  'You cannot extend the suspension.'))

        wizard = self.browse(cr, uid, ids[0], context)
        date_start = datetime.strptime(wizard.date_start, DF) if \
            wizard.date_start else None
        date_end = datetime.strptime(wizard.date_end, DF) if \
            wizard.date_end else None
        project_obj.suspend_funds(
            cr, uid, project_id, context=context,
            date_start=date_start,
            date_end=date_end)

        return True
