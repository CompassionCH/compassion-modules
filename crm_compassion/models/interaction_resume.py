# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class InteractionResume(models.TransientModel):

    _name = "interaction.resume"
    _order = "communication_date desc"

    partner_id = fields.Many2one("res.partner", "Partner")
    email = fields.Char()
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
    communication_date = fields.Datetime()
    subject = fields.Text()
    body = fields.Html()
    phone_id = fields.Many2one("crm.phonecall", "Phonecall")
    paper_id = fields.Many2one("partner.communication.job", "Communication")
    email_id = fields.Many2one("mail.mail", "Email")
    message_id = fields.Many2one("mail.message", "Email")
    tracking_status = fields.Selection([
        ('error', 'Error'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('rejected', 'Rejected'),
        ('spam', 'Spam'),
        ('unsub', 'Unsubscribed'),
        ('bounced', 'Bounced'),
        ('soft bounced', 'Soft bounced'),
    ])

    @api.model
    def populate_resume(self, partner_id):
        """
        Creates the rows for the resume of given partner
        :param partner_id: the partner
        :return: True
        """
        self.search([('partner_id', '=', partner_id)]).unlink()
        self.env.cr.execute("""
            SELECT
                'Paper' as communication_type,
                pcj.sent_date as communication_date,
                COALESCE(p.contact_id, pcj.partner_id) AS partner_id,
                NULL AS email,
                COALESCE(c.name, pcj.subject) AS subject,
                pcj.body_html AS body,
                'out' AS direction,
                0 as phone_id,
                0 as email_id,
                0 as message_id,
                pcj.id as paper_id,
                NULL as tracking_status
                FROM "partner_communication_job" as pcj
                JOIN res_partner p ON pcj.partner_id = p.id
                FULL OUTER JOIN partner_communication_config c
                    ON pcj.config_id = c.id
                    AND c.name != 'Default communication'
                WHERE pcj.state = 'done'
                AND pcj.send_mode = 'physical'
                AND (p.contact_id = %s OR p.id = %s)
    -- phonecalls
            UNION (
              SELECT
                'Phone' as communication_type,
                crmpc.date as communication_date,
                COALESCE(p.contact_id, p.id) AS partner_id,
                NULL AS email,
                crmpc.name as subject,
                crmpc.name as body,
                CASE crmpc.direction
                    WHEN 'inbound' THEN 'in' ELSE 'out'
                    END
                AS direction,
                crmpc.id as phone_id,
                0 as email_id,
                0 as message_id,
                0 as paper_id,
                NULL as tracking_status
                FROM "crm_phonecall" as crmpc
                JOIN res_partner p ON crmpc.partner_id = p.id
                WHERE (p.contact_id = %s OR p.id = %s)
                )
    -- outgoing e-mails
            UNION (
              SELECT
                'Email' as communication_type,
                m.date as communication_date,
                COALESCE(p.contact_id, p.id) AS partner_id,
                p.email,
                COALESCE(config.name, m.subject) as subject,
                m.body,
                'out' AS direction,
                0 as phone_id,
                mail.id as email_id,
                0 as message_id,
                job.id as paper_id,
                COALESCE(mt.state, 'error') as tracking_status
                FROM "mail_mail" as mail
                JOIN mail_message m ON mail.mail_message_id = m.id
                JOIN mail_mail_res_partner_rel rel
                ON rel.mail_mail_id = mail.id
                JOIN mail_tracking_email mt ON mail.id = mt.mail_id
                JOIN res_partner p ON rel.res_partner_id = p.id
                FULL OUTER JOIN partner_communication_job job
                    ON job.email_id = mail.id
                FULL OUTER JOIN partner_communication_config config
                    ON job.config_id = config.id
                    AND config.name != 'Default communication'
                WHERE mail.state = ANY (ARRAY ['sent', 'received'])
                AND (p.contact_id = %s OR p.id = %s)
                )
    -- incoming messages from partners
            UNION (
              SELECT
                'Email' as communication_type,
                m.date as communication_date,
                COALESCE(p.contact_id, p.id) AS partner_id,
                p.email,
                m.subject as subject,
                m.body,
                'in' AS direction,
                0 as phone_id,
                0 as email_id,
                m.id as message_id,
                0 as paper_id,
                NULL as tracking_status
                FROM "mail_message" as m
                JOIN res_partner p ON m.author_id = p.id
                WHERE m.subject IS NOT NULL
                AND m.message_type = 'email'
                AND (p.contact_id = %s OR p.id = %s)
                )
                """, [partner_id] * 8)
        for row in self.env.cr.dictfetchall():
            self.create(row)
        return True

    def open_object(self):
        """
        TODO Implement and add icon in tree view
        Used for opening the related object directly from tree view.
        :return: action for opening the related object
        """
        self.ensure_one()
        return True
