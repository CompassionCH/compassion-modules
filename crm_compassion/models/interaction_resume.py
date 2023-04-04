##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InteractionResume(models.TransientModel):
    _name = "interaction.resume"
    _description = "Resume of a given partner"
    _order = "communication_date desc"

    partner_id = fields.Many2one("res.partner", "Partner")
    email = fields.Char()
    communication_type = fields.Selection(
        [
            ("Paper", "Paper"),
            ("Phone", "Phone"),
            ("SMS", "SMS"),
            ("Email", "Email"),
            ("Other", "Other"),
        ]
    )
    direction = fields.Selection(
        [
            ("in", "Incoming"),
            ("out", "Outgoing"),
        ]
    )
    # Used to display icons in tree view
    state = fields.Selection(related="direction")
    communication_date = fields.Datetime()
    subject = fields.Text()
    other_type = fields.Char()
    has_attachment = fields.Boolean()
    body = fields.Html()
    phone_id = fields.Many2one("crm.phonecall", "Phonecall")
    paper_id = fields.Many2one("partner.communication.job", "Communication")
    rule_id = fields.Many2one(
        "partner.communication.config",
        "Communication rule",
        related="paper_id.config_id",
    )
    email_id = fields.Many2one("mail.mail", "Email")
    mass_mailing_id = fields.Many2one("mail.mass_mailing", "Mass mailing")
    other_interaction_id = fields.Many2one(
        "partner.log.other.interaction", "Logged interaction"
    )
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
        partner_email = original_partner.email
        partner_ids = [partner_id]
        partner_ids += original_partner.mapped("other_contact_ids").ids
        partner_ids += (
            self.env["res.partner"]
            .search([("email", "!=", False), ("email", "=", partner_email)])
            .ids
        )
        self.search(
            [("partner_id", "in", partner_ids), ("communication_type", "=", "Email")]
        ).unlink()
        self.env.cr.execute(
            """
                    -- Partner Communications (both e-mail and physical)
                    SELECT DISTINCT ON(email_id, subject)
                        CASE pcj.send_mode
                            WHEN 'physical' THEN 'Paper' ELSE 'Email'
                            END
                        as communication_type,
                        pcj.sent_date as communication_date,
                        pcj.partner_id AS partner_id,
                        COALESCE(pcj.email_to, mt.recipient_address) AS email,
                        pcj.subject AS subject,
                        '' as other_type,
                        REGEXP_REPLACE(pcj.body_html, '<img[^>]*>', '') AS body,
                        'out' AS direction,
                        0 as phone_id,
                        pcj.email_id as email_id,
                        0 as message_id,
                        false as is_from_employee,
                        pcj.id as paper_id,
                        CASE pcj.send_mode
                            WHEN 'digital' THEN COALESCE(mt.state, 'error')
                            ELSE NULL
                            END
                        AS tracking_status,
                        0 as mass_mailing_id,
                        0 as other_interaction_id,
                        EXISTS(
                            SELECT id FROM partner_communication_attachment a WHERE a.communication_id = pcj.id
                        ) AS has_attachment
                        FROM "partner_communication_job" as pcj
                        FULL OUTER JOIN mail_tracking_email mt ON pcj.email_id = mt.mail_id
                        WHERE pcj.state = 'done'
                        AND pcj.partner_id = ANY(%s)
                        AND pcj.date BETWEEN (NOW() - interval '3 year') AND NOW()
            -- phonecalls
                    UNION (
                      SELECT
                        'Phone' as communication_type,
                        crmpc.date as communication_date,
                        crmpc.partner_id AS partner_id,
                        NULL AS email,
                        crmpc.name as subject,
                        '' as other_type,
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
                        0 as mass_mailing_id,
                        0 as other_interaction_id,
                        false as has_attachment
                        FROM "crm_phonecall" as crmpc
                        WHERE crmpc.partner_id = ANY(%s) AND crmpc.state = 'done'
                        )
            -- outgoing e-mails
                    UNION (
                      SELECT DISTINCT ON (email_id)
                        'Email' as communication_type,
                        m.date as communication_date,
                        mt.partner_id AS partner_id,
                        mt.recipient_address as email,
                        m.subject as subject,
                        '' as other_type,
                        REGEXP_REPLACE(m.body, '<img[^>]*>', '') AS body,
                        'out' AS direction,
                        0 as phone_id,
                        mail.id as email_id,
                        0 as message_id,
                        mail.is_from_employee as is_from_employee,
                        0 as paper_id,
                        COALESCE(mt.state, 'error') as tracking_status,
                        mt.mass_mailing_id as mass_mailing_id,
                        0 as other_interaction_id,
                        EXISTS(
                            SELECT a.message_id
                            FROM message_attachment_rel a WHERE message_id = m.id
                        ) as has_attachment
                        FROM "mail_mail" as mail
                        JOIN mail_message m ON mail.mail_message_id = m.id
                        JOIN mail_tracking_email mt ON mail.id = mt.mail_id
                        WHERE mail.state = ANY (ARRAY ['sent', 'received', 'exception'])
                        AND mt.partner_id = ANY(%s)
                        AND (mail.direction = 'out' OR mail.direction IS NULL)
                        AND m.model != 'partner.communication.job'
                        AND m.date BETWEEN (NOW() - interval '1 year') AND NOW()
                        )

            -- mass mailings sent from mailchimp (no associated email)
                    UNION (
                      SELECT DISTINCT ON (email, mass_mailing_id)
                        'Email' as communication_type,
                        mail.sent as communication_date,
                        tracking.partner_id AS partner_id,
                        mail.email as email,
                        source.name as subject,
                        '' as other_type,
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
                        mm.id as mass_mailing_id,
                        0 as other_interaction_id,
                        EXISTS(
                            SELECT a.message_id
                            FROM message_attachment_rel a WHERE a.message_id = tracking.mail_message_id
                        ) as has_attachment
                        FROM "mail_mail_statistics" as mail
                        JOIN mail_tracking_email tracking ON mail.mail_tracking_id = tracking.id
                        JOIN mail_mass_mailing mm ON mail.mass_mailing_id = mm.id
                        JOIN utm_source source ON mm.source_id = source.id
                        WHERE mail.sent IS NOT NULL
                        AND tracking.mail_id IS NULL  -- skip if it's already in mail
                        AND mail.email = %s
                        AND mail.create_date BETWEEN (NOW() - interval '1 year') AND NOW()
                        )
            -- incoming messages from partners
                    UNION (
                      SELECT
                        'Email' as communication_type,
                        m.date as communication_date,
                        m.author_id AS partner_id,
                        m.email_from as email,
                        m.subject as subject,
                        '' as other_type,
                        REGEXP_REPLACE(m.body, '<img[^>]*>', '') AS body,
                        'in' AS direction,
                        0 as phone_id,
                        0 as email_id,
                        m.id as message_id,
                        false as is_from_employee,
                        0 as paper_id,
                        NULL as tracking_status,
                        0 as mass_mailing_id,
                        0 as other_interaction_id,
                        EXISTS(
                            SELECT a.message_id
                            FROM message_attachment_rel a WHERE message_id = m.id
                        ) as has_attachment
                        FROM "mail_message" as m
                        WHERE m.subject IS NOT NULL
                        AND m.message_type = 'email'
                        AND m.author_id = ANY(%s)
                        AND m.date BETWEEN (NOW() - interval '1 year') AND NOW()
                        )
            -- other interactions
                    UNION (
                      SELECT
                        'Other' as communication_type,
                        o.date as communication_date,
                        o.partner_id AS partner_id,
                        '' as email,
                        o.subject as subject,
                        o.other_type as other_type,
                        REGEXP_REPLACE(o.body, '<img[^>]*>', '') AS body,
                        o.direction AS direction,
                        0 as phone_id,
                        0 as email_id,
                        0 as message_id,
                        false as is_from_employee,
                        0 as paper_id,
                        NULL as tracking_status,
                        0 as mass_mailing_id,
                        o.id as other_interaction_id,
                        false as has_attachment
                        FROM "partner_log_other_interaction" as o
                        WHERE o.partner_id = ANY(%s)
                        )
            ORDER BY communication_date desc
                            """,
            (
                partner_ids,
                partner_ids,
                partner_ids,
                partner_email or "",
                partner_ids,
                partner_ids,
            ),
        )

        return self.create(self.env.cr.dictfetchall())

    def create(self, vals):
        res = super().create(vals)
        filter_res = self
        emails = self.env["mail.mail"]
        for record in res:
            email = record.email_id
            if not email or email not in emails:
                emails += email
                filter_res += record
        (res - filter_res).unlink()
        return filter_res

    def write(self, vals):
        log_date = vals.get("communication_date")
        if log_date:
            for record in self:
                for _field in [
                    "email_id",
                    "message_id",
                    "paper_id",
                    "other_interaction_id",
                    "phone_id",
                ]:
                    getattr(record, _field).write({"date": log_date})
        direction = vals.get("direction")
        if direction:
            for record in self.filtered(lambda r: r.direction != direction):
                email = record.email_id
                message = record.message_id
                if not email:
                    email = self.env["mail.mail"].search(
                        [("mail_message_id", "=", message.id)]
                    )
                if email:
                    author = email.author_id
                    dest = email.recipient_ids
                    # Solves the previous bug on logged emails where author is same as dest
                    if author == dest:
                        dest = self.env.user.partner_id
                    email.write(
                        {
                            "author_id": dest[:1].id,
                            "recipient_ids": [(6, 0, author.ids)],
                            "partner_ids": [(6, 0, author.ids)],
                            "email_from": dest[:1].email,
                            "direction": direction,
                        }
                    )
                    email.mail_message_id.write(
                        {
                            "author_id": dest[:1].id,
                            "email_from": dest[:1].email,
                            "partner_ids": [(6, 0, author.ids)],
                            "email_to": author.email,
                        }
                    )
                elif record.other_interaction_id:
                    record.other_interaction_id.direction = direction
                else:
                    raise UserError(_("Cannot change direction of this interaction"))
        return super().write(vals)
