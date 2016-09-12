# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging

from openerp import models, fields, api

logger = logging.getLogger(__name__)


class GenericChild(models.AbstractModel):
    """ Generic information of children shared by subclasses:
        - compassion.child : sponsored children
        - compassion.global.child : available children in global pool
    """
    _name = 'compassion.generic.child'

    # General Information
    #####################
    global_id = fields.Char('Global ID', required=True, readonly=True)
    correspondence_language_id = fields.Many2one(
        'res.lang.compassion', 'Correspondence language')
    local_id = fields.Char(
        'Local ID', size=11, help='Child reference', readonly=True)
    project_id = fields.Many2one('compassion.project', 'Project')
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field office',
        related='project_id.field_office_id')
    name = fields.Char()
    firstname = fields.Char()
    lastname = fields.Char()
    preferred_name = fields.Char()
    gender = fields.Selection([('F', 'Female'), ('M', 'Male')], readonly=True)
    birthdate = fields.Date(readonly=True)
    age = fields.Integer(readonly=True)
    is_orphan = fields.Boolean(readonly=True)
    beneficiary_state = fields.Selection([
        ("Available", "Available"),
        ("Active", "Active"),
        ("Change Commitment Hold", "Change Commitment Hold"),
        ("Consignment Hold", "Consignment Hold"),
        ("Delinquent Mass Cancel Hold", "Delinquent Mass Cancel Hold"),
        ("E-Commerce Hold", "E-Commerce Hold"),
        ("Inactive", "Inactive"),
        ("Ineligible", "Ineligible"),
        ("No Money Hold", "No Money Hold"),
        ("Reinstatement Hold", "Reinstatement Hold"),
        ("Reservation Hold", "Reservation Hold"),
        ("Sponsor Cancel Hold", "Sponsor Cancel Hold"),
        ("Sponsored", "Sponsored"),
        ("Sub Child Hold", "Sub Child Hold"),
    ], readonly=True)
    sponsorship_status = fields.Selection([
        ('Sponsored', 'Sponsored'),
        ('Unsponsored', 'Unsponsored'),
    ], readonly=True)
    unsponsored_since = fields.Date(readonly=True)

    @api.model
    def get_fields(self):
        return ['global_id', 'local_id', 'project_id', 'name', 'firstname',
                'lastname', 'preferred_name', 'gender', 'birthdate', 'age',
                'is_orphan', 'beneficiary_state', 'sponsorship_status',
                'unsponsored_since', 'correspondence_language_id']

    def get_child_vals(self):
        """ Get the required field values of one record for other record
            creation.
            :return: Dictionary of values for the fields
        """
        self.ensure_one()
        vals = self.read(self.get_fields())[0]
        if vals.get('correspondence_language_id'):
            vals['correspondence_language_id'] = vals[
                'correspondence_language_id'][0]
        if vals.get('project_id'):
            vals['project_id'] = vals['project_id'][0]

        del vals['id']
        return vals


class GlobalChild(models.TransientModel):
    """ Available child in the global childpool
    """
    _name = 'compassion.global.child'
    _inherit = 'compassion.generic.child'
    _description = 'Global Child'

    portrait = fields.Binary()
    fullshot = fields.Binary()
    image_url = fields.Char()
    color = fields.Integer(compute='_compute_color')
    is_area_hiv_affected = fields.Boolean()
    is_special_needs = fields.Boolean()
    field_office_id = fields.Many2one(store=True)
    search_view_id = fields.Many2one(
        'compassion.childpool.search'
    )
    priority_score = fields.Float(help='How fast the child should be '
                                       'sponsored')
    correspondent_score = fields.Float(help='Score based on how long the '
                                            'child is waiting')
    holding_global_partner_id = fields.Many2one(
        'compassion.global.partner', 'Holding global partner'
    )
    waiting_days = fields.Integer()
    hold_expiration_date = fields.Datetime()
    source_code = fields.Char(
        'origin of the hold'
    )

    @api.multi
    def _compute_color(self):
        for child in self:
            child.color = 6 if child.gender == 'M' else 9
