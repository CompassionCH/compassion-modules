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
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
        ('soft bounced', 'Soft bounced'),
        ('not an email', 'Not an email')
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
                pcj.partner_id,
                pcj.subject,
                pcj.body_html AS body,
                'out' AS direction,
                0 as phone_id,
                0 as email_id,
                0 as message_id,
                pcj.id as paper_id,
                'not an email' as tracking_status
                FROM "partner_communication_job" as pcj
                WHERE pcj.state = 'done'
                AND pcj.send_mode = 'physical'
                AND pcj.partner_id = %s
    -- phonecalls
            UNION (
              SELECT
                'Phone' as communication_type,
                crmpc.date as communication_date,
                crmpc.partner_id as partner_id,
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
                'not an email' as tracking_status
                FROM "crm_phonecall" as crmpc
                WHERE crmpc.partner_id = %s
                )
    -- outgoing e-mails
            UNION (
              SELECT
                'Email' as communication_type,
                m.date as communication_date,
                rel.res_partner_id as partner_id,
                m.subject as subject,
                m.body,
                'out' AS direction,
                0 as phone_id,
                mail.id as email_id,
                0 as message_id,
                0 as paper_id,
                mt.state as tracking_status
                FROM "mail_mail" as mail
                JOIN mail_message m ON mail.mail_message_id = m.id
                JOIN mail_mail_res_partner_rel rel
                ON rel.mail_mail_id = mail.id
                JOIN mail_tracking_email mt ON mail.id = mt.mail_id 
                WHERE mail.state = ANY (ARRAY ['sent', 'received'])
                AND rel.res_partner_id = %s
                )
    -- incoming messages from partners
            UNION (
              SELECT
                'Email' as communication_type,
                m.date as communication_date,
                m.author_id as partner_id,
                m.subject as subject,
                m.body,
                'in' AS direction,
                0 as phone_id,
                0 as email_id,
                m.id as message_id,
                0 as paper_id,
                'not an email' as tracking_status
                FROM "mail_message" as m
                WHERE m.subject IS NOT NULL
                AND m.message_type = 'email'
                AND m.author_id = %s
                )
                """, [partner_id] * 4)
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
