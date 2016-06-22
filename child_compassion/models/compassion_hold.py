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


class CompassionHold(models.Model):
    _name = 'compassion.hold'

    name = fields.Char('Name')
    hold_id = fields.Char()
    child_id = fields.Many2one('compassion.child', 'Child on hold')
    type = fields.Selection([
        ('Available', 'Available'),
        ('Change Commitment Hold', 'Change Commitment Hold'),
        ('Consignment Hold', 'Consignment Hold'),
        ('Delinquent Mass Cancel Hold', 'Delinquent Mass Cancel Hold'),
        ('E-Commerce Hold', 'E-Commerce Hold'),
        ('Inactive', 'Inactive'),
        ('Ineligible', 'Ineligible'),
        ('No Money Hold', 'No Money Hold'),
        ('Reinstatement Hold', 'Reinstatement Hold'),
        ('Reservation Hold', 'Reservation Hold'),
        ('Sponsor Cancel Hold', 'Sponsor Cancel Hold'),
        ('Sponsored', 'Sponsored'),
        ('Sub Child Hold', 'Sub Child Hold')
    ])
    expiration_date = fields.Datetime()
    primary_owner = fields.Char()
    secondary_owner = fields.Char()
    no_money_yield_rate = fields.Float()
    yield_rate = fields.Float()
    channel = fields.Char()
    source_code = fields.Char()
