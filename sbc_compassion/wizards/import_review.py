# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import Warning


class ImportReview(models.TransientModel):
    """
    Browse through the import lines and allow the user to review and correct
    the results easily.
    """

    _name = 'import.letters.review'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    progress = fields.Float(default=0.0, compute='_compute_progress')
    import_line_ids = fields.Many2many(
        'import.letter.line', readonly=True,
        default=lambda self: self._get_default_lines())
    current_line_index = fields.Integer(default=0)
    count = fields.Integer(compute='_compute_count')
    nb_lines = fields.Integer(compute='_compute_count')
    current_line_id = fields.Many2one(
        'import.letter.line', compute='_get_current_line', store=True,
        readonly=True)
    postpone_import_id = fields.Many2one(
        'import.letters.history')

    # Import line related fields
    state = fields.Selection(related='current_line_id.status', readonly=True)
    letter_image = fields.Binary(
        related='current_line_id.letter_image_preview', readonly=True)
    partner_id = fields.Many2one(related='current_line_id.partner_id')
    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship')
    child_id = fields.Many2one(related='current_line_id.child_id')
    template_id = fields.Many2one(related='current_line_id.template_id')
    language_id = fields.Many2one(
        related='current_line_id.letter_language_id')
    is_encourager = fields.Boolean(related='current_line_id.is_encourager')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_default_lines(self):
        return self.env.context['line_ids']

    @api.depends('import_line_ids', 'current_line_index')
    def _get_current_line(self):
        for wizard in self:
            if wizard.import_line_ids:
                wizard.current_line_id = wizard.import_line_ids[
                    wizard.current_line_index]

    @api.depends('import_line_ids')
    def _compute_count(self):
        for wizard in self:
            wizard.nb_lines = len(wizard.import_line_ids)
            wizard.count = wizard.current_line_index + 1

    @api.depends('current_line_index')
    def _compute_progress(self):
        for wizard in self:
            wizard.progress = (float(wizard.count) / wizard.nb_lines) * 100

    @api.onchange('sponsorship_id')
    def _get_partner_child(self):
        for wizard in self:
            child = wizard.sponsorship_id.child_id
            if child:
                wizard.child_id = child

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def next(self):
        """ Load the next import line in the view. """
        self.ensure_one()
        if self.current_line_id.status != 'ok':
            raise Warning(
                _("Import is not valid"),
                _("Please review this import before going to the next."))
        self.current_line_id.reviewed = True
        self.current_line_index = self.current_line_index + 1

    @api.multi
    def finish(self):
        """ Return to import view. """
        self.ensure_one()
        import_history = self.current_line_id.import_id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': import_history._name,
            'res_id': import_history.id,
            'context': self.env.context,
            'target': 'current',
        }

    @api.multi
    def postpone(self):
        """ Move the line in another import. """
        self.ensure_one()
        postpone_import = self.postpone_import_id
        if not postpone_import:
            postpone_import = self.env['import.letters.history'].create({
                'import_completed': True})
            self.postpone_import_id = postpone_import
        self.current_line_id.import_id = postpone_import
        self.current_line_index = self.current_line_index + 1
