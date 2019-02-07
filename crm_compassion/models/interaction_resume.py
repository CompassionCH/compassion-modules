# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _


class InteractionResume(models.Model):

    _name = "interaction.resume"

    partner_id = fields.Many2one("res.partner")
    communication_type = fields.Selection([('Paper', "Paper"), ("Phone", "Phone"), ("SMS", "SMS"), ('Email', "Email")])
    communication_date = fields.Date()
    communication = fields.Many2one("ir.model", string='Model')
    communication_shown = fields.Integer("Communication")

