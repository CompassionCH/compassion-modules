# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api, _
from psycopg2 import IntegrityError


class contract_origin(models.Model):
    """ Origin of a contract """
    _name = 'recurring.contract.origin'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(readonly=True)
    type = fields.Selection('_get_origin_types', help=_(
        "Origin of contract : "
        " * Contact with sponsor/ambassador : an other sponsor told the "
        "person about Compassion."
        " * Event : sponsorship was made during an event"
        " * Marketing campaign : sponsorship was made after specific "
        "campaign (magazine, ad, etc..)"
        " * Transfer : sponsorship transferred from another country."
        " * Other : select only if none other type matches."
    ), required=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account')
    contract_ids = fields.One2many(
        'recurring.contract', 'origin_id', 'Sponsorships originated',
        readonly=True)
    country_id = fields.Many2one('res.country', 'Country')
    other_name = fields.Char('Give details', size=128)
    won_sponsorships = fields.Integer(
        compute='_get_won_sponsorships', store=True)

    _sql_constraints = [(
        'name_uniq', 'UNIQUE(name)',
        _("You cannot have two origins with same name."
          "The origin does probably already exist.")
    )]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_origin_types(self):
        return [
            ('partner', _("Contact with sponsor/ambassador")),
            ('event', _("Event")),
            ('marketing', _("Marketing campaign")),
            ('sub', _("SUB Sponsorship")),
            ('transfer', _("Transfer")),
            ('other', _("Other")),
        ]

    @api.depends('contract_ids.origin_id', 'contract_ids.state')
    @api.one
    def _get_won_sponsorships(self):
        contract_ids = self.contract_ids.filtered(
            lambda c: c.state in ('active', 'terminated'))
        self.won_sponsorships = len(contract_ids)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    @api.depends('type')
    def name_get(self):
        res = list()
        for origin in self:
            res.append((origin.id, origin._name_get()))

        return res

    @api.model
    def create(self, vals):
        """Try to find existing origin instead of raising an error."""
        try:
            res = super(contract_origin, self).create(vals)
        except IntegrityError:
            # Find the origin
            self.env.cr.commit()     # Release the lock
            origins = self.search([
                ('type', '=', vals.get('type')),
                ('partner_id', '=', vals.get('partner_id')),
                ('analytic_id', '=', vals.get('analytic_id')),
                ('country_id', '=', vals.get('country_id')),
                ('other_name', '=', vals.get('other_name')),
            ])
            if origins:
                res = origins[0]
            else:
                raise
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _name_get(self):
        name = ""
        if self.type == 'partner':
            if self.partner_id.parent_id:
                name = self.partner_id.parent_id.name + ", "
            name += self.partner_id.name or self.name
        elif self.type in ('event', 'marketing'):
            name = self.analytic_id.name
        elif self.type == 'transfer':
            if self.country_id:
                name = 'Transfer from ' + self.country_id.name
            else:
                name = 'Transfer from partner country'
        elif self.type == 'other':
            name = self.other_name or 'Other'
        elif self.type == 'sub':
            name = 'SUB Sponsorship'

        return name
