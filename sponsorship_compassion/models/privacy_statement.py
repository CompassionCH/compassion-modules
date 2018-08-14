# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class PrivacyStatement(models.Model):
    _name = "compassion.privacy.statement"
    _order = 'version'
    _sql_constraints = [('unique_privacy_statement', 'unique(version)',
                         'This "Version" already exists')]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(compute='_compute_name')
    version = fields.Char()
    text = fields.Html(translate=True)
    date = fields.Date()

    @api.model
    def get_current(self):
        return self.env[
            'compassion.privacy.statement'].search([], order='date desc',
                                                   limit=1)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('version')
    def _compute_name(self):
        for rd in self:
            rd.name = rd.version


class PrivacyStatementAgreement(models.Model):
    _name = 'privacy.statement.agreement'
    _sql_constraints = [('unique_privacy_agreement',
                         'unique(partner_id,privacy_statement_id',
                         'This partner has already accepted this privacy '
                         'statement')]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    partner_id = fields.Many2one('res.partner', 'Partner')
    agreement_date = fields.Date()
    privacy_statement_id = fields.Many2one('compassion.privacy.statement',
                                           'Privacy statement')
    version = fields.Char(related='privacy_statement_id.version',
                          readonly=True)
    origin_signature = fields.Selection(
        [('new_letter', 'Website new letter'),
         ('new_sponsorship', 'Website new sponsorship'),
         ('first_payment', 'First payment')])

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def open_contract(self):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }
