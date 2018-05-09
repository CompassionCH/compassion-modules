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
    _name = 'partner.communication.submit.revision'
    _description = 'Submit revision text wizard'

    revision_id = fields.Many2one(
        'partner.communication.revision',
        default=lambda s: s._default_revision(),
    )
    state = fields.Selection(related='revision_id.state')
    reviser_name = fields.Char(related='revision_id.user_id.name')
    corrector_name = fields.Char(related='revision_id.correction_user_id.name')
    comments = fields.Text()

    @api.model
    def _default_revision(self):
        return self.env['partner.communication.revision'].browse(
            self._context['active_id'])

    @api.multi
    def submit(self):
        self.ensure_one()
        revision = self.revision_id
        if self.state == 'pending':
            subject_base = u'[{}] Revision text submitted'
            body_base = u'A new text for was submitted for approval. {}'
            revision.write({
                'proposition_correction':
                revision.proposition_correction or revision.proposition_text,
                'subject_correction':
                revision.subject_correction or revision.subject,
                'state': 'submit',
                'is_corrected': False
            })
        else:
            subject_base = u'[{}] Correction submitted'
            body_base = u'Corrections were proposed. {}'
            revision.write({'state': 'pending', 'is_corrected': True})

        body = body_base.format(self.comments or '').strip()
        subject = subject_base.format(revision.display_name)
        revision.notify_proposition(subject, body)
        return True
