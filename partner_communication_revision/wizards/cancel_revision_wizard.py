# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class ValidateRevisionWizard(models.TransientModel):
    _name = 'partner.communication.cancel.proposition'
    _description = 'Cancel proposition wizard'

    revision_id = fields.Many2one(
        'partner.communication.revision',
        default=lambda s: s._default_revision(),
        required=True
    )
    revision_mode = fields.Selection(
        [('proposition', 'Reviser'),
         ('correction', 'Corrector')],
        'Assign revision to',
        required=True,
        default='correction'
    )
    user_id = fields.Many2one(
        'res.users', 'Set person in charge',
        domain=[('share', '=', False)],
        compute='_compute_user_id',
        inverse='_inverse_user_id'
    )
    comments = fields.Text()

    @api.model
    def _default_revision(self):
        return self.env['partner.communication.revision'].browse(
            self._context['active_id'])

    @api.multi
    def _compute_user_id(self):
        for wizard in self:
            if wizard.revision_mode == 'proposition':
                wizard.user_id = wizard.revision_id.user_id
            else:
                wizard.user_id = wizard.revision_id.correction_user_id

    @api.multi
    def _inverse_user_id(self):
        for wizard in self:
            if wizard.revision_mode == 'proposition':
                wizard.revision_id.user_id = wizard.user_id
            else:
                wizard.revision_id.correction_user_id = wizard.user_id

    @api.onchange('revision_id', 'revision_mode')
    def onchange_revision_id(self):
        self._compute_user_id()

    @api.multi
    def cancel_revision(self):
        self.ensure_one()
        revision_vals = {'state': 'pending', 'is_master_version': False}
        if self.revision_mode != 'proposition':
            revision_vals.update({
                'state': 'submit',
                'proposition_correction': self.revision_id.proposition_text,
                'subject_correction': self.revision_id.subject
            })
        self.revision_id.write(revision_vals)
        if self.user_id != self.env.user or self.comments:
            next_action_text = u'<b>Next action for {}: ' \
                u'Make corrections and resubmit.</b><br/><br/>'.format(
                    self.user_id.firstname)
            body = u"The text was set back in revision by {}{}{}".format(
                self.env.user.firstname,
                u" with following comments:<br/><br/>" if self.comments else
                u".",
                self.comments or u"").strip()
            subject = "[{}] Approval cancelled:  text needs corrections"\
                .format(self.revision_id.display_name)
            self.revision_id.notify_proposition(
                subject, next_action_text + body)

        return True
