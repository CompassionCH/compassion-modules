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
from odoo.tools.mail import html2plaintext, html_sanitize


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
    has_attachment = fields.Boolean(compute='_compute_has_attachment')
    body = fields.Html()
    phone_id = fields.Many2one("crm.phonecall", "Phonecall")
    paper_id = fields.Many2one("partner.communication.job", "Communication")
    email_id = fields.Many2one("mail.mail", "Email")
    color = fields.Char(compute='_compute_color')
    message_id = fields.Many2one("mail.message", "Email")
    tracking_status = fields.Selection([
        ('error', 'Error'),
        ('deferred', 'Deferred'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('rejected', 'Rejected'),
        ('spam', 'Spam'),
        ('unsub', 'Unsubscribed'),
        ('bounced', 'Bounced'),
        ('soft-bounced', 'Soft bounced'),
    ])

    @api.model
    def populate_resume(self, partner_id):
        """
        Creates the rows for the resume of given partner
        :param partner_id: the partner
        :return: True
        """
        original_partner = self.env['res.partner'].search([
            ('id', '=', partner_id)
        ])
        email_address = original_partner.email
        partners_with_same_email = self.env['res.partner'].search([
            ('email', '=', email_address)
        ])
        self.search([('partner_id', '=', partner_id)]).unlink()

        default_communication_config = self.env['partner.communication.config'].search([
            ('name', '=', "Default communication")
        ])

        # Paper communications
        paper_communications = self.env['partner.communication.job'].search([
            ('state', '=', 'done'),
            ('send_mode', '=', 'physical'),
            ('config_id', '=', default_communication_config.id),
            ('partner_id', 'in', partners_with_same_email.ids)
        ])
        for paper_communication in paper_communications:
            self.create_interaction_resume(
                "Phone",
                paper_communication.sent_date,
                paper_communication.partner_id.id,
                None,
                paper_communication.subject,
                paper_communication.body_html,
                "out",
                0,
                0,
                0,
                paper_communication.id,
                None)

        # Phone communications
        phone_communications = self.env['crm.phonecall'].search([
            ('partner_id', 'in', partners_with_same_email.ids)
        ])
        for phone_communication in phone_communications:
            direction = 'out'
            if phone_communication.direction == "inbound":
                direction = 'in'
            self.create_interaction_resume(
                "Phone",
                phone_communication.date,
                phone_communication.partner_id.id,
                None,
                phone_communication.name,
                phone_communication.name,
                direction,
                phone_communication.id,
                0,
                0,
                0,
                None)

        # Outgoing email communications
        outgoing_messages = self.env['mail.message'].search([
            ('author_id', 'in', partners_with_same_email.ids),
            ('message_type', '=', 'email')
        ])
        outgoing_emails = self.env['mail.mail'].search([
            ('mail_message_id', 'in', outgoing_messages.ids)
        ])
        for email in outgoing_emails:
            mt = self.env['mail.tracking.email'].search([
                ('mail_id', '=', email.id)
            ])
            job = self.env['partner.communication.job'].search([
                ('email_id', '=', email.id)
            ])
            self.create_interaction_resume(
                "Email",
                email.date,
                email.mail_message_id.author_id.id,
                mt.recipient_address,
                email.subject,
                email.body,
                "out",
                0,
                email.id,
                0,
                job.id,
                mt.state or "error")

        # Incoming email communications
        incoming_messages = self.env['mail.message'].search([
            ('author_id', 'in', partners_with_same_email.ids),
            ('subject', '!=', None),
            ('message_type', '=', 'email')
        ])
        for message in incoming_messages:
            self.create_interaction_resume(
                "Email",
                message.date,
                message.author_id.id,
                message.author_id.email,
                message.subject,
                message.body,
                "in",
                0,
                0,
                message.id,
                0,
                None)

        return True

    def create_interaction_resume(self, comm_type, date, partner_id, email,
                                  subject, body, direction, phone_id,
                                  email_id, message_id, paper_id,
                                  tracking_status):
        self.env['interaction.resume'].create({
            'communication_type': comm_type,
            'communication_date': date,
            'partner_id': partner_id,
            'email': html_sanitize(email),
            'subject': subject,
            'body': body.replace('<img[^>]*>', ''),
            'direction': direction,
            'phone_id': phone_id,
            'email_id': email_id,
            'message_id': message_id,
            'paper_id': paper_id,
            'tracking_status': tracking_status
        })

    def open_object(self):
        """
        TODO Implement and add icon in tree view
        Used for opening the related object directly from tree view.
        :return: action for opening the related object
        """
        self.ensure_one()
        return True

    def _compute_has_attachment(self):
        """
        Check in each row if e-mail (outgoing) or message (incoming) contains
        at least 1 attachment.
        """
        for row in self:
            row.has_attachment = row.email_id.attachment_ids or \
                row.message_id.attachment_ids

    def _compute_color(self):
        for row in self:
            if len(html2plaintext(row.body).strip()) < 15 \
                    and row.direction == 'out':
                # mass mailing
                row.color = 'gray'
            elif row.direction == 'in':
                row.color = 'red'
            else:
                # outgoing
                row.color = 'green'




# self.env.cr.execute("""
#         SELECT
#                 'Paper' as communication_type,
#                 pcj.sent_date as communication_date,
#                 COALESCE(p.contact_id, pcj.partner_id) AS partner_id,
#                 NULL AS email,
#                 COALESCE(c.name, pcj.subject) AS subject,
#                 REGEXP_REPLACE(pcj.body_html, '<img[^>]*>', '') AS body,
#                 'out' AS direction,
#                 0 as phone_id,
#                 0 as email_id,
#                 0 as message_id,
#                 pcj.id as paper_id,
#                 NULL as tracking_status
#                 FROM "partner_communication_job" as pcj
#                 JOIN res_partner p ON pcj.partner_id = p.id
#                 FULL OUTER JOIN partner_communication_config c
#                     ON pcj.config_id = c.id
#                     AND c.name != 'Default communication'
#                 WHERE pcj.state = 'done'
#                 AND pcj.send_mode = 'physical'
#                 AND (p.contact_id = %s OR p.id = %s)
#     -- phonecalls
#             UNION (
#               SELECT
#                 'Phone' as communication_type,
#                 crmpc.date as communication_date,
#                 COALESCE(p.contact_id, p.id) AS partner_id,
#                 NULL AS email,
#                 crmpc.name as subject,
#                 crmpc.name as body,
#                 CASE crmpc.direction
#                     WHEN 'inbound' THEN 'in' ELSE 'out'
#                     END
#                 AS direction,
#                 crmpc.id as phone_id,
#                 0 as email_id,
#                 0 as message_id,
#                 0 as paper_id,
#                 NULL as tracking_status
#                 FROM "crm_phonecall" as crmpc
#                 JOIN res_partner p ON crmpc.partner_id = p.id
#                 WHERE (p.contact_id = %s OR p.id = %s)
#                 )
#     -- outgoing e-mails
#             UNION (
#               SELECT
#                 'Email' as communication_type,
#                 m.date as communication_date,
#                 COALESCE(p.contact_id, p.id) AS partner_id,
#                 mt.recipient_address as email,
#                 COALESCE(config.name, m.subject) as subject,
#                 REGEXP_REPLACE(m.body, '<img[^>]*>', '') AS body,
#                 'out' AS direction,
#                 0 as phone_id,
#                 mail.id as email_id,
#                 0 as message_id,
#                 job.id as paper_id,
#                 COALESCE(mt.state, 'error') as tracking_status
#                 FROM "mail_mail" as mail
#                 JOIN mail_message m ON mail.mail_message_id = m.id
#                 JOIN mail_mail_res_partner_rel rel
#                 ON rel.mail_mail_id = mail.id
#                 FULL OUTER JOIN mail_tracking_email mt ON mail.id = mt.mail_id
#                 JOIN res_partner p ON rel.res_partner_id = p.id
#                 FULL OUTER JOIN partner_communication_job job
#                     ON job.email_id = mail.id
#                 FULL OUTER JOIN partner_communication_config config
#                     ON job.config_id = config.id
#                     AND config.name != 'Default communication'
#                 WHERE mail.state = ANY (ARRAY ['sent', 'received'])
#                 AND (p.contact_id = %s OR p.id = %s)
#                 )
#     -- incoming messages from partners
#             UNION (
#               SELECT
#                 'Email' as communication_type,
#                 m.date as communication_date,
#                 COALESCE(p.contact_id, p.id) AS partner_id,
#                 m.email_from as email,
#                 m.subject as subject,
#                 REGEXP_REPLACE(m.body, '<img[^>]*>', '') AS body,
#                 'in' AS direction,
#                 0 as phone_id,
#                 0 as email_id,
#                 m.id as message_id,
#                 0 as paper_id,
#                 NULL as tracking_status
#                 FROM "mail_message" as m
#                 JOIN res_partner p ON m.author_id = p.id
#                 WHERE m.subject IS NOT NULL
#                 AND m.message_type = 'email'
#                 AND (p.contact_id = %s OR p.id = %s)
#                 )
#                 """, [partner_id] * 8)