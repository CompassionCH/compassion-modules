# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields, api
from openerp.addons.message_center_compassion.mappings import base_mapping as \
    mapping


class ChildNote(models.Model):
    """ A child Note """
    _name = 'compassion.child.note'
    _description = 'Child Note'
    # _order = 'date desc'

    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade'
    )
    body = fields.Char()
    record_type = fields.Char()
    type = fields.Char()
    visibility = fields.Char()
    source_code = fields.Char()

    @api.model
    def process_commkit(self, commkit_data):
        child_note_mapping = mapping.new_onramp_mapping(
                                                self._name,
                                                self.env,
                                                'beneficiary_note')
        vals = child_note_mapping.get_vals_from_connect(commkit_data)
        child_note = self.create(vals)
        return [child_note.id]
