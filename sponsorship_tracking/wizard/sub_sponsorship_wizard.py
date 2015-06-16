# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _


class sub_sponsorship_wizard(orm.TransientModel):
    _name = "sds.subsponsorship.wizard"

    def _get_no_sub_reasons(self, cr, uid, context=None):
        return [
            ('other_sponsorship', _('Sponsors other children')),
            ('financial', _('Financial reasons')),
            ('old', _('Is too old to sponsor another child')),
            ('other_support', _('Wants to support with fund donations')),
            ('other_organization', _('Supports another organization')),
            ('not_now', _("Doesn't want to take another child right now")),
            ('not_given', _('Not given')),
            ('other', _('Other...'))
        ]

    _columns = {
        'state': fields.selection([
            ('sub', 'sub'),
            ('no_sub', 'no_sub')]),
        'child_id': fields.many2one(
            'compassion.child', string=_("Child")),
        'no_sub_default_reasons': fields.selection(
            _get_no_sub_reasons, string=_("No sub reason")),
        'no_sub_reason': fields.char(_("No sub reason")),
    }

    def create_subsponsorship(self, cr, uid, ids, context=None):
        """ Creates a subsponsorship. """
        if not isinstance(ids, list):
            ids = [ids]
        child = self.browse(cr, uid, ids[0], context).child_id
        if not child:
            raise orm.except_orm("No child selected", "Please select a child")

        sponsorship_id = context.get('active_id')
        contract_obj = self.pool.get('recurring.contract')
        origin_obj = self.pool.get('recurring.contract.origin')
        sub_origin_ids = origin_obj.search(cr, uid, [
            ('type', '=', 'sub')], context=context)

        contract_obj.copy(cr, uid, sponsorship_id, {
            'parent_id': sponsorship_id,
            'origin_id': sub_origin_ids and sub_origin_ids[0],
        }, context)

        sub_id = contract_obj.search(cr, uid, [
            ('state', '=', 'draft'),
            ('origin_id', '=', sub_origin_ids and sub_origin_ids[0]),
            ('parent_id', '=', sponsorship_id)], context=context)
        if sub_id and len(sub_id) == 1:
            contract_obj.write(cr, uid, sub_id, {
                'child_id': child.id}, context)
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'recurring.contract', sub_id[0],
                                    'contract_validated', cr)

        return True

    def no_sub(self, cr, uid, ids, context=None):
        """ No SUB for the sponsorship. """
        if not isinstance(ids, list):
            ids = [ids]

        sponsorship_id = context.get('active_id')
        contract_obj = self.pool.get('recurring.contract')
        wizard = self.browse(cr, uid, ids[0], context)
        default_reason = wizard.no_sub_default_reasons
        reason = False
        if default_reason == 'other':
            reason = wizard.no_sub_reason
        else:
            reason = dict(self._get_no_sub_reasons(cr, uid, context)).get(
                default_reason)
        contract_obj.write(cr, uid, sponsorship_id, {
            'no_sub_reason': reason}, context)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'recurring.contract', sponsorship_id,
                                'no_sub', cr)
        return True
