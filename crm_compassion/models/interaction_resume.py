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
    _description = "Resume of a given partner"
    _order = "communication_date desc"

    partner_id = fields.Many2one("res.partner", "Partner")
    email = fields.Char()
    communication_type = fields.Selection(
        [("Paper", "Paper"), ("Phone", "Phone"), ("SMS", "SMS"), ("Email", "Email")]
    )
    direction = fields.Selection([("in", "Incoming"), ("out", "Outgoing"), ])
    # Used to display icons in tree view
    state = fields.Selection(related="direction")
    communication_date = fields.Datetime()
    subject = fields.Text()
    has_attachment = fields.Boolean(compute="_compute_has_attachment")
    body = fields.Html()
    phone_id = fields.Many2one("crm.phonecall", "Phonecall")
    paper_id = fields.Many2one(
        "partner.communication.job", "Communication"
    )
    email_id = fields.Many2one("mail.mail", "Email")
    mass_mailing_id = fields.Many2one("mail.mass_mailing", "Mass mailing")
    logged_mail_direction = fields.Selection(related="email_id.direction")
    message_id = fields.Many2one("mail.message", "Email")
    is_from_employee = fields.Boolean(default=False)
    tracking_status = fields.Selection(
        [
            ("error", "Error"),
            ("deferred", "Deferred"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("opened", "Opened"),
            ("rejected", "Rejected"),
            ("spam", "Spam"),
            ("unsub", "Unsubscribed"),
            ("bounced", "Bounced"),
            ("soft-bounced", "Soft bounced"),
        ]
    )

    @api.model
    def populate_resume(self, partner_id):
        """
        Creates the rows for the resume of given partner
        :param partner_id: the partner
        :return: True
        """
        original_partner = self.env["res.partner"].browse(partner_id)
        email_address = original_partner.email
        partners_with_same_email_ids = (
            self.env["res.partner"]
                .search([("email", "!=", False), ("email", "=", email_address)])
                .ids
        )

        self.search([("partner_id", "in", partners_with_same_email_ids)]).unlink()
        self.env.cr.execute(
            """
                    SELECT
                        'Paper' as communication_type,
                        pcj.sent_date as communication_date,
                        COALESCE(p.contact_id, pcj.partner_id) AS partner_id,
                        NULL AS email,
                        COALESCE(source.name, pcj.subject) AS subject,
                        REGEXP_REPLACE(pcj.body_html, '<img[^>]*>', '') AS body,
                        'out' AS direction,
                        0 as phone_id,
                        0 as email_id,
                        0 as message_id,
                        false as is_from_employee,
                        pcj.id as paper_id,
                        NULL as tracking_status,
                        0 as mass_mailing_id
                        FROM "partner_communication_job" as pcj
                        JOIN res_partner p ON pcj.partner_id = p.id
                        FULL OUTER JOIN partner_communication_config c
                            ON pcj.config_id = c.id
                        FULL OUTER JOIN utm_source source
                            ON c.source_id = source.id
                            AND source.name not in ('Default communication','Donation - Thank You')
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
                        crmpc.is_from_employee as is_from_employee,
                        0 as paper_id,
                        NULL as tracking_status,
                        0 as mass_mailing_id
                        FROM "crm_phonecall" as crmpc
                        JOIN res_partner p ON crmpc.partner_id = p.id
                        WHERE (p.contact_id = %s OR p.id = %s) AND crmpc.state = 'done'
                        )
            -- outgoing e-mails
                    UNION (
                      SELECT
                        'Email' as communication_type,
                        m.date as communication_date,
                        COALESCE(p.contact_id, p.id) AS partner_id,
                        mt.recipient_address as email,
                        COALESCE(source.name, m.subject) as subject,
                        REGEXP_REPLACE(m.body, '<img[^>]*>', '') AS body,
                        'out' AS direction,
                        0 as phone_id,
                        mail.id as email_id,
                        0 as message_id,
                        mail.is_from_employee as is_from_employee,
                        job.id as paper_id,
                        COALESCE(mt.state, 'error') as tracking_status,
                        mt.mass_mailing_id as mass_mailing_id
                        FROM "mail_mail" as mail
                        JOIN mail_message m ON mail.mail_message_id = m.id
                        JOIN mail_mail_res_partner_rel rel
                        ON rel.mail_mail_id = mail.id
                        FULL OUTER JOIN mail_tracking_email mt ON mail.id = mt.mail_id
                        JOIN res_partner p ON rel.res_partner_id = p.id
                        FULL OUTER JOIN partner_communication_job job
                            ON job.email_id = mail.id
                        FULL OUTER JOIN partner_communication_config config
                            ON job.config_id = config.id
                        FULL OUTER JOIN utm_source source
                            ON config.source_id = source.id
                            AND source.name != 'Default communication'
                        WHERE mail.state = ANY (ARRAY ['sent', 'received'])
                        AND (p.contact_id = ANY(%s) OR p.id = ANY(%s))
                        AND (mail.direction = 'out' OR mail.direction IS NULL)
                        )

            -- mass mailings sent from mailchimp (no associated email)
                    UNION (
                      SELECT DISTINCT
                        'Email' as communication_type,
                        mail.sent as communication_date,
                        COALESCE(tracking.partner_id, p.contact_id, p.id) AS partner_id,
                        mail.email as email,
                        source.name as subject,
                        NULL AS body,
                        'out' AS direction,
                        0 as phone_id,
                        0 as email_id,
                        0 as message_id,
                        true as is_from_employee,
                        0 as paper_id,
                        CASE
                            WHEN mail.opened IS NOT NULL THEN 'opened'
                            WHEN mail.exception IS NOT NULL THEN 'error'
                            WHEN mail.bounced IS NOT NULL THEN 'bounced'
                        ELSE 'sent'
                        END tracking_status,
                        mm.id as mass_mailing_id
                        FROM "mail_mail_statistics" as mail
                        FULL OUTER JOIN mail_tracking_email tracking
                            ON mail.mail_tracking_id = tracking.id
                        JOIN res_partner p ON p.email = mail.email
                        JOIN mail_mass_mailing mm ON mail.mass_mailing_id = mm.id
                        JOIN utm_source source ON mm.source_id = source.id
                        WHERE mail.sent IS NOT NULL
                        AND tracking.mail_id IS NULL  -- skip if it's already in mail
                        AND mail.email = %s
                        )
            -- incoming messages from partners
                    UNION (
                      SELECT
                        'Email' as communication_type,
                        m.date as communication_date,
                        COALESCE(p.contact_id, p.id) AS partner_id,
                        m.email_from as email,
                        m.subject as subject,
                        REGEXP_REPLACE(m.body, '<img[^>]*>', '') AS body,
                        'in' AS direction,
                        0 as phone_id,
                        0 as email_id,
                        m.id as message_id,
                        false as is_from_employee,
                        0 as paper_id,
                        NULL as tracking_status,
                        0 as mass_mailing_id
                        FROM "mail_message" as m
                        JOIN res_partner p ON m.author_id = p.id
                        WHERE m.subject IS NOT NULL
                        AND m.message_type = 'email'
                        AND (p.contact_id = ANY(%s) OR p.id = ANY(%s))
                        )
            ORDER BY communication_date desc
            LIMIT 240
                            """,
            (
                partner_id,
                partner_id,
                partner_id,
                partner_id,
                partners_with_same_email_ids,
                partners_with_same_email_ids,
                email_address or "",
                partners_with_same_email_ids,
                partners_with_same_email_ids,
            ),
        )

        return self.create(self.env.cr.dictfetchall())

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
            row.has_attachment = (
                row.email_id.attachment_ids or row.message_id.attachment_ids
            )
