# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, fields, api
from ..mappings.child_note_mapping import ChildNoteMapping


class ChildNote(models.Model):
    """ A child Note """
    _name = 'compassion.child.note'
    _description = 'Child Note'
    _order = 'id desc'

    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade'
    )
    body = fields.Char()
    record_type = fields.Char()
    type = fields.Char()
    visibility = fields.Char()
    source_code = fields.Char()

    @api.model
    def create(self, vals):
        note = super(ChildNote, self).create(vals)
        note.child_id.message_post(
            note.body, "New beneficiary notes"
        )
        return note

    @api.model
    def process_commkit(self, commkit_data):
        child_note_mapping = ChildNoteMapping(self.env)
        note_ids = list()
        for notes_data in commkit_data.get('GPPublicNotesKit', [commkit_data]):
            vals = child_note_mapping.get_vals_from_connect(notes_data)
            child_note = self.create(vals)
            note_ids.append(child_note.id)
        return note_ids
