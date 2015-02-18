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
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from datetime import datetime


class compassion_child(orm.Model):
    """ Add allocation and deallocation methods on the children. """
    _inherit = 'compassion.child'

    def _get_child_states(self, cr, uid, context=None):
        """ Add new error state used when an incoming message for a child
        could not be processed. """
        res = super(compassion_child, self)._get_child_states(cr, uid, context)
        res.append(('E', _('Error')))
        return res

    _columns = {
        # New field to save previous state if child goes
        # in error state
        'previous_state': fields.char('Previous state', size=1),
        'state': fields.selection(
            _get_child_states, _("Status"), select=True, readonly=True,
            track_visibility="onchange", required=True),
    }

    def allocate(self, cr, uid, args, context=None):
        child_id = args.get('object_id')
        if child_id:
            # Child already exists, put it back to available state
            # and erase exit details
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
                child.write({
                    'exit_date': False,
                    'exit_reason': False,
                    'gp_exit_reason': False})
        else:
            # Allocate new child
            child_vals = {
                'code': args.get('code'),
                'date': args.get('date')}
            args['object_id'] = self._insert_new_child(cr, uid, child_vals,
                                                       context)

        # Commit the allocation, in case update information triggers an
        # error, so that the child is still saved in database.
        cr.commit()

        # Update all information of child
        args['event'] = 'Allocate'
        return self.update(cr, uid, args, context=context)

    def deallocate(self, cr, uid, args, context=None):
        """Deallocate child.
        This happens only for unsponsored children that are no longer
        assigned to Switzerland.
        """
        return self.write(cr, uid, args.get('object_id'), {
            'state': 'X', 'exit_date': args.get('date')}, context)

    def depart(self, cr, uid, args, context=None):
        """When a depart is done automatically when processing a message:
        1. If the child is sponsored, the sponsorship is terminated with the
           'Child Departure' ending reason.
        2. The child is marked as departed (GetExitDetails API is called)
        3. GP_Exit_Reason is inferred if possible.
        """
        if context is None:
            context = dict()
        child = self.browse(cr, uid, args.get('object_id'), context)
        if child.sponsor_id:
            for contract in child.contract_ids:
                if contract.state in ('waiting', 'active', 'mandate'):
                    # Terminate contract and mark the departure
                    contract.write({
                        'end_reason': '1',  # Child departure
                        'end_date': datetime.today().strftime(DF),
                        'gmc_state': 'depart'})

                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(
                        uid, 'recurring.contract', contract.id,
                        'contract_terminated', cr)

        if child.state != 'F':
            child.write({'state': 'F'})
            # Reload child to get the ExitDetails information, and infer
            # GP Exit reason
            ctx = context.copy()
            ctx['lang'] = 'en_US'
            child = self.browse(cr, uid, child.id, ctx)
            if child.exit_reason:
                for gp_exit in self.get_gp_exit_reasons(cr, uid, ctx):
                    if child.exit_reason.startswith(gp_exit[1]):
                        child.write({'gp_exit_reason': gp_exit[0]})
                        break

        return True

    def update(self, cr, uid, args, context=None):
        """ When we receive a notification that child has been updated,
        we fetch the information of child given what was updated. """
        res = True
        if not args.get('object_id'):
            raise orm.except_orm(
                _("Child not found"),
                _("Child %s was not found. Please process the allocate "
                  "message.") % args.get('code'))
        # Write new code of child, if changed
        child = self.browse(cr, uid, args.get('object_id'), context)
        if child.code != args.get('code'):
            child.write({'code': args.get('code')})

        # Perform the required update given the event
        event = args.get('event')
        if event in ('Allocate', 'Transfer'):
            res = self.get_infos(cr, uid, args.get('object_id'), context)
        elif event == 'CaseStudy':
            res = self._get_case_study(cr, uid, child, context)
        elif event == 'NewImage':
            # Get the last case study for attaching it in GP
            self._get_case_study(cr, uid, child, context)
            res = self._get_last_pictures(cr, uid, child.id, context)

        if not res:
            raise orm.except_orm(_("Update Child Error"),
                                 _("The child %s could not be updated")
                                 % args.get('code'))

        # Notify the change if the child is sponsored
        if child.sponsor_id:
            # Maps the event to the gmc state value of contract
            gmc_states = {
                'Transfer': 'transfer',
                'CaseStudy': 'casestudy',
                'NewImage': 'picture',
            }
            for contract in child.contract_ids:
                if contract.state in ('waiting', 'active', 'mandate'):
                    contract.write({'gmc_state': gmc_states[event]})

        if child.state == 'E':
            # Put the child back to normal state
            child.write({'state': child.previous_state})

        return True

        ######################################################################
        #                          PRIVATE METHODS                           #
        ######################################################################

    def _insert_new_child(self, cr, uid, vals, context=None):
        """Creates a non-existing child and link messages
        referencing it."""
        child_id = self.create(cr, uid, vals, context)
        # Link existing messages to the child
        mess_obj = self.pool.get('gmc.message.pool')
        mess_ids = mess_obj.search(
            cr, uid, [('incoming_key', '=', vals.get('code')),
                      ('object_id', '=', 0)],
            context=context)
        if mess_ids:
            mess_obj.write(cr, uid, mess_ids, {
                'object_id': child_id,
                'child_id': child_id}, context)
        return child_id
