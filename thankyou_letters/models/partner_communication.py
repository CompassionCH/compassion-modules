# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import threading
import locale
from contextlib import contextmanager
from datetime import datetime

from odoo import api, models, fields

LOCALE_LOCK = threading.Lock()


@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, (name, 'UTF-8'))
        finally:
            locale.setlocale(locale.LC_ALL, saved)


class PartnerCommunication(models.Model):
    _inherit = 'partner.communication.job'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    date_communication = fields.Char(compute='_compute_date_communication')
    signature = fields.Char(compute='_compute_signature')
    success_story_id = fields.Many2one(
        'success.story', 'Success Story', domain=[('type', '=', 'story')])
    success_sentence_id = fields.Many2one(
        'success.story', 'Success Sentence',
        domain=[('type', '=', 'sentence')])
    success_sentence = fields.Html(related='success_sentence_id.body')
    print_subject = fields.Boolean(default=True)
    print_header = fields.Boolean()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _compute_date_communication(self):
        lang_map = {
            'fr_CH': u'le %d %B %Y',
            'fr': u'le %d %B %Y',
            'de_DE': u'%d. %B %Y',
            'en_US': u'%d %B %Y',
            'it_IT': u'%d %B %Y',
        }
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for communication in self:
            lang = communication.partner_id.lang
            with setlocale(lang):
                date = today.strftime(lang_map.get(lang)).decode('utf-8')
                communication.date_communication = city + u", " + date

    @api.multi
    def _compute_signature(self):
        for communication in self:
            user = communication.user_id or self.env.user
            user = user.with_context(lang=communication.partner_id.lang)
            employee = user.employee_ids
            signature = ''
            if len(employee) == 1:
                signature = employee.name + '<br/>' + \
                    employee.department_id.name + '<br/>'
            signature += user.company_id.name
            communication.signature = signature

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """
        Fetch a success story at creation
        :param vals: values for record creation
        :return: partner.communication.job record
        """
        job = super(PartnerCommunication, self).create(vals)
        job.set_success_story()
        return job

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def set_success_story(self):
        """
        Takes the less used active success story and attach it
        to communications.
        :return: True
        """
        all_stories = self.env['success.story'].search([
            ('is_active', '=', True)])
        stories = all_stories.filtered(lambda s: s.type == 'story')
        sentences = all_stories.filtered(lambda s: s.type == 'sentence')
        for job in self:
            # Only set success story for donation letters
            if job.config_id.model == 'account.invoice.line' and stories:
                if len(stories) == 1:
                    job.success_story_id = stories
                else:
                    story, use_count = job._get_min_used_story(stories)
                    job.success_story_id = story

            if sentences and 'object.success_sentence' in \
                    job.with_context(
                        lang=job.partner_id.lang).email_template_id.body_html:
                if len(sentences) == 1:
                    job.success_sentence_id = sentences
                else:
                    sentence, use_count = job._get_min_used_story(sentences)
                    if use_count < 5:
                        job.success_sentence_id = sentence

        return True

    @api.multi
    def refresh_text(self, refresh_uid=False):
        """
        Refresh the success story as well
        :param refresh_uid: User that refresh
        :return: True
        """
        self.set_success_story()
        super(PartnerCommunication, self).refresh_text(refresh_uid)
        return True

    @api.multi
    def send(self):
        """
        Update the count of succes story prints when sending a receipt.
        :return: True
        """
        res = super(PartnerCommunication, self).send()
        for job in self.filtered('sent_date'):
            if job.success_story_id:
                job.success_story_id.print_count += 1
            if job.success_sentence and job.success_sentence in job.body_html:
                job.success_sentence_id.print_count += 1

        return res

    @api.multi
    def _get_min_used_story(self, stories):
        """
        Given success stories, returns the one that the partner has received
        the least.
        :param stories: <success.story> recordset
        :return: <success.story> single record, <int> usage count
        """
        self.ensure_one()
        usage_count = dict()
        type = stories.mapped('type')[0]
        field = 'success_story_id' if type == 'story' else \
            'success_sentence_id'
        # Put the least used stories at end of list to choose them in case
        # of equality use for a partner.
        stories = reversed(stories.sorted(lambda s: s.current_usage_count))
        for s in stories:
            usage = self.search_count([
                ('partner_id', '=', self.partner_id.id),
                (field, '=', s.id)
            ])
            usage_count[usage] = s
        min_used = min(usage_count.keys())
        return usage_count[min_used], min_used


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # Translate name of department for signatures
    name = fields.Char(translate=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Translate name of Company for signatures
    address_name = fields.Char(translate=True)
