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
from odoo import tools
from odoo import models, fields, api


class InteractionResume(models.Model):

    _name = "interaction.resume"
    _auto = False
    _table = "interaction_resume"

    partner_id = fields.Many2one("res.partner")
    communication_type = fields.Selection([('Paper', "Paper"),
                                           ("Phone", "Phone"),
                                           ("SMS", "SMS"),
                                           ('Email', "Email")])
    communication_date = fields.Date()
    communication = fields.Many2one("ir.model", string='Model')
    communication_phone = fields.Many2one("crm.phonecall")
    communication_paper = fields.Many2one("partner.communication.job")
    communication_email = fields.Many2one("mail.tracking.email")
    communication_shown = fields.Char("Communication")

    @api.model_cr
    def init(self):
        # to prevent IDs duplication with UNION, recurring contracts IDs are
        # pair and account invoice IDs are impair.
        # many fields are hardcoded due to csv exportation needs
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
              SELECT
                (2 * ROW_NUMBER() OVER (ORDER BY (SELECT pcj.id))) AS id,
                'Paper' as communication_type,
                pcj.date as communication_date,
                pcj.partner_id as partner_id,
                pcj.id as communication,
                pcj.subject as communication_shown,
                NULL::Integer as communication_phone,
                NULL::Integer as communication_email,
                pcj.id as communication_paper
                FROM "partner_communication_job" as pcj
                )
            UNION ALL (
              SELECT
                (2 * ROW_NUMBER() OVER (ORDER BY (SELECT crmpc.id)) - 1) AS id,
                'Phone' as communication_type,
                crmpc.date as communication_date,
                crmpc.partner_id as partner_id,
                crmpc.id as communication,
                crmpc.name as communication_shown,
                crmpc.id as communication_phone,
                NULL::Integer as communication_email,
                NULL::Integer as communication_paper
                FROM "crm_phonecall" as crmpc
                )
            UNION ALL (
              SELECT
                (2 * ROW_NUMBER() OVER (ORDER BY (SELECT mte.id)) - 1) AS id,
                'Email' as communication_type,
                mte.date as communication_date,
                mte.partner_id as partner_id,
                mte.id as communication,
                mte.name as communication_shown,
                NULL::Integer as communication_phone,
                mte.id as communication_email,
                NULL::Integer as communication_paper
                FROM "mail_tracking_email" as mte
                )
                """ % self._table)
