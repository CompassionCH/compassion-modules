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
from openerp import netsvc
from openerp.osv import orm
from openerp.tools.translate import _


class compassion_child(orm.Model):

    """ Add allocation and deallocation methods on the children. """
    _inherit = 'compassion.child'

    def allocate(self, cr, uid, args, context=None):
        child_id = args.get('object_id')
        if child_id:
            # Child already exists, put it back to available state
            child = self.browse(cr, uid, child_id, context)
            if child.state == 'P':
                raise orm.except_orm(
                    _("Child allocation error"),
                    _("The child that will be allocated is sponsored. "
                      "Maybe someone forgot to terminate the sponsorship ? "
                      "Please verify information of child %s.") % child.code)
            if child.state in ('F', 'X'):
                # Start a new workflow making the child available again
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_create(uid, self._name, child_id, cr)
        else:
            # Allocate a new child
            child_id = self.create(cr, uid, {
                'code': args.get('code'),
                'date': args.get('date')
            }, context=context)
        # Update all information of child
        args['event'] = 'Allocate'
        return self.update(cr, uid, args, context=context)

    def deallocate(self, cr, uid, args, context=None):
        """Deallocate child.
        TODO:
            If child is sponsored, it means it will be transfered to another
            project. We should not mark end the sponsorship and should
            warn the sponsor of the change.
        """
        return self.write(cr, uid, args.get('object_id'), {
            'state': 'X', 'exit_date': args.get('date')}, context)

    def depart(self, cr, uid, args, context=None):
        """Not yet ready"""
        # TODO : possibly terminate the contract, mark the child as departed
        # and the user should do the right communication
        # to the sponsor from GP.
        child = self.browse(cr, uid, args.get('object_id'), context)
        if child.sponsor_id:
            contract_ids = self.pool.get('recurring.contract').search(
                cr, uid, [
                    ('child_id', '=', child.id),
                    ('partner_id', '=', child.sponsor_id.id),
                    ('state', 'in', ('waiting', 'active'))], context=context)
            if contract_ids:
                # TODO : Terminate contract with information retrieved by the
                #        GetExitDetails API (which is not yet ready)
                return True
        elif child.state != 'F':
            # TODO : Mark child as departed with information retrieved
            #        by GetExitDetails API.
            return True

        return True

    def update(self, cr, uid, args, context=None):
        """ When we receive a notification that child has been updated,
        we fetch the last case study. """
        # Write new code of child, if changed
        child = self.browse(cr, uid, args.get('object_id'), context)
        if child.code != args.get('code'):
            child.write({'code': args.get('code')})

        # Perform the required update given the event
        event = args.get('event')
        if event == 'Allocate':
            self.get_infos(cr, uid, args.get('object_id'), context=context)
        elif event == 'Transfer':
            # Nothing to do, only the child code has changed
            return True
        elif event == 'CaseStudy':
            self._get_case_study(cr, uid, child, context)
        elif event == 'NewImage':
            self._get_last_pictures(cr, uid, child.id, context)
        return True


class compassion_project(orm.Model):

    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, args, context=None):
        """ When we receive a notification that a project has been updated,
        we fetch the last informations. """
        self.update_informations(cr, uid, args.get('object_id'), context)
        return True
