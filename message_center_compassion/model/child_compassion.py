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
from openerp import api, models, fields, netsvc, _
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime


class compassion_project(models.Model):
    """ Add update method. """
    _inherit = 'compassion.project'

    @api.model
    def update(self, args):
        """ When we receive a notification that a project has been updated,
        we fetch the last informations. """
        project = self.browse(args.get('object_id'))
        return project.update_informations()


class compassion_child(models.Model):
    """ Add allocation and deallocation methods on the children. """
    _inherit = 'compassion.child'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # New field to save previous state if child goes
    # in error state
    previous_state = fields.Char('Previous state', size=1)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_child_states(self):
        """ Add new error state used when an incoming message for a child
        could not be processed. """
        res = super(compassion_child, self)._get_child_states()
        res.append(('E', _('Error')))
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def allocate(self, args):
        child_id = args.get('object_id')
        if child_id:
            # Child already exists, put it back to available state
            # and erase exit details
            child = self.browse(child_id)
            if child.state == 'P':
                raise Warning(
                    _("Child allocation error"),
                    _("The child that will be allocated is sponsored. "
                      "Maybe someone forgot to terminate the sponsorship ? "
                      "Please verify information of child %s.") % child.code)
            if child.state in ('F', 'X'):
                # Start a new workflow making the child available again
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_create(self.env.user.id, self._name, child_id,
                                      self.env.cr)
                child.write({
                    'exit_date': False,
                    'exit_reason': False,
                    'gp_exit_reason': False})
        else:
            # Allocate new child
            child_vals = {
                'code': args.get('code'),
                'date': args.get('date')}
            args['object_id'] = self._insert_new_child(child_vals)

        # Commit the allocation, in case update information triggers an
        # error, so that the child is still saved in database.
        self.env.cr.commit()

        # Update all information of child
        args['event'] = 'Allocate'
        return self.update(args)

    def deallocate(self, args):
        """Deallocate child.
        This happens only for unsponsored children that are no longer
        assigned to Switzerland.
        """
        return self.write(args.get('object_id'), {
            'state': 'X', 'exit_date': args.get('date')})

    def depart(self, args):
        """When a depart is done automatically when processing a message:
        1. If the child is sponsored, the sponsorship is terminated with the
           'Child Departure' ending reason.
        2. The child is marked as departed (GetExitDetails API is called)
        3. GP_Exit_Reason is inferred if possible.
        """
        lang = self.env.context.get('lang')
        self.env.context = self.env.with_context(lang='en_US').context
        child = self.browse(args.get('object_id'))
        if child.sponsor_id:
            for contract in child.sponsorship_ids:
                if contract.state in ('waiting', 'active', 'mandate'):
                    # Terminate contract and mark the departure
                    contract.write({
                        'end_reason': '1',  # Child departure
                        'end_date': datetime.today().strftime(DF),
                        'gmc_state': 'depart'})

                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(
                        self.env.user.id, 'recurring.contract', contract.id,
                        'contract_terminated', self.env.cr)

        if child.state != 'F':
            child.write({'state': 'F'})
            if child.exit_reason:
                for gp_exit in self.get_gp_exit_reasons():
                    if child.exit_reason.startswith(gp_exit[1]):
                        child.write({'gp_exit_reason': gp_exit[0]})
                        break

        self.env.context = self.env.with_context(lang=lang).context
        return True

    def update(self, args):
        """ When we receive a notification that child has been updated,
        we fetch the information of child given what was updated. """
        res = True
        if not args.get('object_id'):
            raise Warning(
                _("Child not found"),
                _("Child %s was not found. Please process the allocate "
                  "message.") % args.get('code'))
        # Write new code of child, if changed
        child = self.browse(args.get('object_id'))
        if child.code != args.get('code'):
            child.write({'code': args.get('code')})

        # Perform the required update given the event
        event = args.get('event')
        if event in ('Allocate', 'Transfer'):
            res = child.get_infos()
        elif event == 'CaseStudy':
            res = child._get_case_study()
        elif event == 'NewImage':
            res = child._get_last_pictures()

        if not res:
            raise Warning(
                _("Update Child Error"),
                _("The child %s could not be updated") % args.get('code'))

        # Notify the change if the child is sponsored
        if child.sponsor_id:
            sponsor_id = child.sponsor_id.id
            contracts = self.env['recurring.contract'].search([
                ('state', 'not in', ('terminated', 'cancelled')),
                '|', ('partner_id', '=', sponsor_id),
                ('correspondant_id', '=', sponsor_id)])
            contracts.set_gmc_event(event)

        if child.state == 'E':
            # Put the child back to normal state
            child.reset_child_state()

        return True

    def reset_child_state(self):
        for child in self:
            child.write({'state': child.previous_state,
                         'previous_state': False})
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def view_error_messages(self):
        return {
            'type': 'ir.actions.act_window',
            'id': 'action_gmc_message_incoming_form',
            'view_mode': 'tree,form',
            'res_model': 'gmc.message.pool',
            'domain': [('child_id', 'in', self.ids),
                       ('state', '=', 'failure')]
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _insert_new_child(self, vals):
        """Creates a non-existing child and link messages
        referencing it."""
        child_id = self.create(vals).id
        # Link existing messages to the child
        messages = self.env['gmc.message.pool'].search([
            ('incoming_key', '=', vals.get('code')),
            ('object_id', '=', 0)])
        messages.write({
            'object_id': child_id,
            'child_id': child_id})
        return child_id
