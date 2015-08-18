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
from openerp import api, models, fields, exceptions, _


class sub_sponsorship_wizard(models.TransientModel):
    _name = "sds.subsponsorship.wizard"

    state = fields.Selection([
        ('sub', 'sub'),
        ('no_sub', 'no_sub')])
    child_id = fields.Many2one(
        'compassion.child', 'Child')
    no_sub_default_reasons = fields.Selection(
        '_get_no_sub_reasons', 'No sub reason')
    no_sub_reason = fields.Char('No sub reason')

    def _get_no_sub_reasons(self):
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

    @api.multi
    def create_subsponsorship(self):
        """ Creates a subsponsorship. """
        self.ensure_one()
        child = self.child_id
        if not child:
            raise exceptions.Warning(
                _("No child selected"),
                _("Please select a child"))

        sponsorship_id = self.env.context.get('active_id')
        contract_obj = self.env['recurring.contract']
        contract = contract_obj.browse(sponsorship_id)
        origin_obj = self.env['recurring.contract.origin']
        sub_origin_id = origin_obj.search([('type', '=', 'sub')], limit=1).id

        sub_contract = contract.copy({
            'parent_id': sponsorship_id,
            'origin_id': sub_origin_id,
        })
        sub_contract.write({'child_id': child.id})
        sub_contract.signal_workflow('contract_validated')

        return True

    @api.multi
    def no_sub(self):
        """ No SUB for the sponsorship. """
        self.ensure_one()
        sponsorship_id = self.env.context.get('active_id')
        contract = self.env['recurring.contract'].browse(sponsorship_id)
        default_reason = self.no_sub_default_reasons
        reason = False
        if default_reason == 'other':
            reason = self.no_sub_reason
        else:
            reason = dict(self._get_no_sub_reasons()).get(default_reason)
        contract.write({'no_sub_reason': reason})
        contract.signal_workflow('no_sub')
        return True
