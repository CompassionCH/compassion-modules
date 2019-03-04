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
    _order = "communication_date desc"

    partner_id = fields.Many2one("res.partner", "Partner")
    communication_type = fields.Selection([('Paper', "Paper"),
                                           ("Phone", "Phone"),
                                           ("SMS", "SMS"),
                                           ('Email', "Email")])
    direction = fields.Selection([
        ('in', 'Incoming'),
        ('out', 'Outgoing'),
    ])
    # Used to display icons in tree view
    state = fields.Selection(related='direction')
    communication_date = fields.Date()
    subject = fields.Text()
    body = fields.Html(compute='_compute_body')
    phone_id = fields.Many2one("crm.phonecall", "Phonecall")
    paper_id = fields.Many2one("partner.communication.job", "Communication")
    email_id = fields.Many2one("mail.mail", "Email")
    message_id = fields.Many2one("mail.message", "Email")

    def _compute_body(self):
        for resume in self:
            resume.body = resume.paper_id.body_html or resume.phone_id.name or\
                resume.email_id.body_html or resume.message_id.body

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
              SELECT ROW_NUMBER()
                OVER (ORDER BY sub.communication_type, sub.res_id) as id,
              sub.*
    -- paper communications
              FROM (( SELECT
                pcj.id AS res_id,
                'Paper' as communication_type,
                pcj.sent_date as communication_date,
                pcj.partner_id,
                pcj.subject,
                'out' AS direction,
                NULL::Integer as phone_id,
                NULL::Integer as email_id,
                NULL::Integer as message_id,
                pcj.id as paper_id
                FROM "partner_communication_job" as pcj
                WHERE pcj.state = 'done'
                AND pcj.send_mode = 'physical'
                )
    -- phonecalls
            UNION ALL (
              SELECT
                crmpc.id AS res_id,
                'Phone' as communication_type,
                crmpc.date as communication_date,
                crmpc.partner_id as partner_id,
                crmpc.name as subject,
                CASE crmpc.direction
                    WHEN 'inbound' THEN 'in' ELSE 'out'
                    END
                AS direction,
                crmpc.id as phone_id,
                NULL::Integer as email_id,
                NULL::Integer as message_id,
                NULL::Integer as paper_id
                FROM "crm_phonecall" as crmpc
                )
    -- outgoing e-mails
            UNION ALL (
              SELECT
                mail.id AS res_id,
                'Email' as communication_type,
                m.date as communication_date,
                rel.res_partner_id as partner_id,
                m.subject as subject,
                'out' AS direction,
                NULL::Integer as phone_id,
                mail.id as email_id,
                NULL::Integer as message_id,
                NULL::Integer as paper_id
                FROM "mail_mail" as mail
                JOIN mail_message m ON mail.mail_message_id = m.id
                JOIN mail_mail_res_partner_rel rel
                ON rel.mail_mail_id = mail.id
                WHERE mail.state IN ('sent', 'received')
                )
    -- incoming messages from partners
            UNION ALL (
              SELECT
                m.id AS res_id,
                'Email' as communication_type,
                m.date as communication_date,
                m.author_id as partner_id,
                m.subject as subject,
                'in' AS direction,
                NULL::Integer as phone_id,
                NULL::Integer as email_id,
                m.id as message_id,
                NULL::Integer as paper_id
                FROM "mail_message" as m
                )) sub )
        ORDER BY communication_date desc
                """ % self._table)
