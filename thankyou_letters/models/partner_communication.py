##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class CommunicationDefaults(models.AbstractModel):
    _inherit = "partner.communication.defaults"

    print_subject = fields.Boolean(default=True)
    print_header = fields.Boolean()
    show_signature = fields.Boolean()
    add_success_story = fields.Boolean()


class PartnerCommunication(models.Model):
    _inherit = "partner.communication.job"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    success_story_id = fields.Many2one(
        "success.story",
        "Success Story",
        domain=[("type", "=", "story")],
        readonly=False,
    )
    success_sentence_id = fields.Many2one(
        "success.story",
        "Success Sentence",
        domain=[("type", "=", "sentence")],
        readonly=False,
    )
    success_sentence = fields.Text(related="success_sentence_id.body_text")
    add_success_story = fields.Boolean(related="config_id.add_success_story")
    amount = fields.Float(compute="_compute_donation_amount", store=True)

    @api.depends("object_ids")
    def _compute_donation_amount(self):
        for communication in self:
            if communication.model == "account.move.line":
                try:
                    invoice_lines = communication.get_objects().exists()
                    if not invoice_lines:
                        continue
                except ValueError:
                    continue
                communication.amount = sum(invoice_lines.mapped("price_subtotal"))

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []
        default_vals.extend(["print_subject", "print_header", "show_signature"])
        return super()._get_default_vals(vals, default_vals)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def set_success_story(self):
        """
        Takes the less used active success story and attach it
        to communications.
        :return: True
        """
        all_stories = self.env["success.story"].search(
            [("is_active", "=", True), ("only_when_chosen", "=", False)]
        )
        stories = all_stories.filtered(lambda s: s.type == "story")
        sentences = all_stories.filtered(lambda s: s.type == "sentence")
        default_story = self.env.context.get("default_success_story_id")
        for job in self:
            # Only set success story if config is set.
            if job.add_success_story and stories and not default_story:
                if len(stories) == 1:
                    job.success_story_id = stories
                else:
                    story, use_count = job._get_min_used_story(stories)
                    job.success_story_id = story

            body = job.with_context(
                lang=job.partner_id.lang
            ).email_template_id.body_html
            if sentences and body and "object.success_sentence" in body:
                if len(sentences) == 1:
                    job.success_sentence_id = sentences
                else:
                    sentence, use_count = job._get_min_used_story(sentences)
                    if use_count < 5:
                        job.success_sentence_id = sentence

        return True

    def refresh_text(self, refresh_uid=False):
        """
        Refresh the success story as well
        :param refresh_uid: User that refresh
        :return: True
        """
        for job in self:
            if not job.success_story_id.only_when_chosen:
                job.set_success_story()
        super().refresh_text(refresh_uid)
        return True

    def send(self):
        """
        Update the count of succes story prints when sending a receipt.
        :return: True
        """
        res = super().send()
        for job in self.filtered("sent_date"):
            if job.success_story_id:
                job.success_story_id.print_count += 1
            if job.success_sentence and job.success_sentence in job.body_html:
                job.success_sentence_id.print_count += 1

        return res

    def _get_min_used_story(self, stories):
        """
        Given success stories, returns the one that the partner has received
        the least.
        :param stories: <success.story> recordset
        :return: <success.story> single record, <int> usage count
        """
        self.ensure_one()
        usage_count = dict()
        type = stories.mapped("type")[0]
        field = "success_story_id" if type == "story" else "success_sentence_id"
        # Put the least used stories at end of list to choose them in case
        # of equality use for a partner.
        stories = reversed(stories.sorted(lambda s: s.current_usage_count))
        for s in stories:
            usage = self.search_count(
                [("partner_id", "=", self.partner_id.id), (field, "=", s.id)]
            )
            usage_count[usage] = s
        min_used = min(usage_count.keys())
        return usage_count[min_used], min_used
