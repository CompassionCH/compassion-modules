# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields


class FieldOffice(models.Model):
    _name = 'compassion.field.office'

    name = fields.Char('Name')
    project_ids = fields.One2many(
        'compassion.project', 'field_office_id', 'Compassion projects')

