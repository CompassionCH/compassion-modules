# -*- encoding: utf-8 -*-
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

from openerp import api, models, fields

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
    print_header = fields.Boolean()
    date_communication = fields.Char(compute='_compute_date_communication')
    success_story_id = fields.Many2one('success.story', 'Success Story')
    print_subject = fields.Boolean(default=True)
    signature = fields.Char(compute='_compute_signature')

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
        Fetch a success story for donation communications
        :param vals: values for record creation
        :return: partner.communication.job record
        """
        job = super(PartnerCommunication, self).create(vals)
        if job.config_id.model == 'account.invoice.line':
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
        for job in self:
            story = self.env['success.story'].search([
                ('is_active', '=', True)]).sorted(
                lambda s: s.current_usage_count)
            if story:
                if len(story) == 1:
                    job.success_story_id = story
                else:
                    usage_count = dict()
                    for s in reversed(story):
                        usage = self.search_count([
                            ('partner_id', '=', job.partner_id.id),
                            ('success_story_id', '=', s.id)
                        ])
                        usage_count[usage] = s
                    min_used = min(usage_count.keys())
                    job.success_story_id = usage_count[min_used]

        return True

    @api.multi
    def refresh_text(self, refresh_uid=False):
        """
        Refresh the success story as well
        :param refresh_uid: User that refresh
        :return: True
        """
        super(PartnerCommunication, self).refresh_text(refresh_uid)
        self.filtered('success_story_id').set_success_story()
        return True

    @api.multi
    def send(self):
        """
        Update the count of succes story prints when sending a receipt.
        :return: True
        """
        res = super(PartnerCommunication, self).send()
        for job in self.filtered('success_story_id').filtered('sent_date'):
            job.success_story_id.print_count += 1

        return res


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # Translate name of department for signatures
    name = fields.Char(translate=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Translate name of Company for signatures
    address_name = fields.Char(translate=True)
