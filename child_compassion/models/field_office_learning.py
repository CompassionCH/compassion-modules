##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class LearningInfo(models.Model):
    _name = 'field.office.learning'
    _description = 'Field Office Learning information'
    _rec_name = 'title'
    _order = 'field_office_id asc, sequence asc'

    sequence = fields.Integer()
    time = fields.Float()
    title = fields.Text(
        translate=True,
        help="Contains the title of the learning information.",
    )
    description = fields.Text(
        translate=True,
        help="Contains the description of the learning information.",
    )
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field office', required=True
    )

    def get_learning_json(self):
        return {
            'TIME': '{0:02.0f}:{1:02.0f}'.format(*divmod(self.time * 60, 60))
            if self.time else '',
            'DESCRIPTION': self.description or '',
            'TITLE': self.title or ''
        }
